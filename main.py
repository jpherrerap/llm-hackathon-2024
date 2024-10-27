from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List, Dict, Any
from back.client import BackClient

# read local .env file
_ = load_dotenv(find_dotenv())
chat_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# Connect to MongoDB
uri = os.environ["MONGO_URI"]
client = MongoClient(uri)
db = client['vue-chatbot']
messages_collection = db['messages']
messages_collection.delete_many({}) # Clear the messages collection
messages_collection.insert_one({'role': 'system', 'content': 'You are a helpful assistant'}) # Add a system message

# Get the API key from environment variables

# Create a OpenAI ChatGPT completion function
def get_chat_response():
    messages = get_messages()
    response = chat_client.chat.completions.create(model="gpt-3.5-turbo",
    messages=messages,
    temperature=0.7)
    messages_collection.insert_one({'role': 'assistant', 'content': response.choices[0].message.content})

def get_messages():
    messages = list(messages_collection.find({}))
    for message in messages:
        message.pop('_id')
    return messages

app = FastAPI(debug=True)

# Set static file location
# app.mount("/assets", StaticFiles(directory="dist/assets", ht), name="static")

# # Setup Jinja2 templates to serve index.html
# templates = Jinja2Templates(directory="app/src")

# Serve index.html template from the root path
@app.get("/")
async def root(request: Request):
    return "hola"

# Create a websocket connection
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            if message_data['type'] == 'get_messages':
                messages = get_messages()
                await websocket.send_text(json.dumps({'type': 'message_update', 'content': messages[1:]}))

            if message_data['type'] == 'new_message':
                new_message = message_data['content']
                messages_collection.insert_one({'role': 'user', 'content': new_message})
                messages = get_messages()
                await websocket.send_text(json.dumps({'type': 'message_update', 'content': messages[1:]}))
                get_chat_response()
                messages = get_messages()
                await websocket.send_text(json.dumps({'type': 'message_update', 'content': messages[1:]}))

            if message_data['type'] == 'clear_messages':
                messages_collection.delete_many({})
                messages_collection.insert_one({'role': 'system', 'content': 'You are a helpful assistant'})
                messages = get_messages()
                await websocket.send_text(json.dumps({'type': 'message_update', 'content': messages[1:]}))

            if message_data['type'] == 'ping':
                await websocket.send_text(json.dumps({'type': 'pong'}))

    except WebSocketDisconnect:
        print("Client disconnected")
        print(get_messages())

@app.get("/api/tickets")
async def get_tickets():
    # This is where you'd fetch tickets from your database
    # For now, we'll return some dummy data
    return [
        {"id": 1, "title": "Cannot login", "description": "User is unable to login to their account", "createdAt": "2024-03-15T10:30:00Z", "resolved": False},
        {"id": 2, "title": "Payment failed", "description": "Customer's payment was declined", "createdAt": "2024-03-14T15:45:00Z", "resolved": True},
        {"id": 3, "title": "Product missing", "description": "Order arrived but one item is missing", "createdAt": "2024-03-13T09:00:00Z", "resolved": False},
    ]

# Inicializar el BackClient
back_client = BackClient("db_knowledge.json", "db_tickets.json")

class UserData(BaseModel):
    name: str
    email: str
    phone: str

class UserQuery(BaseModel):
    query: str

@app.post("/start_conversation")
async def start_conversation(user_data: UserData):
    back_client.set_user_data(user_data.name, user_data.email, user_data.phone)
    response = back_client.start_conversation()
    return {"message": response.messages[-1]["content"]}

@app.post("/process_query")
async def process_query(user_query: UserQuery):
    if not back_client.user_data:
        raise HTTPException(status_code=400, detail="Conversation not started. Please start a conversation first.")
    response = back_client.process_user_query(user_query.query)
    return {"message": response.messages[-1]["content"]}

@app.get("/tickets")
async def get_tickets():
    tickets = back_client.get_all_tickets()
    return tickets

@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    ticket = back_client.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
