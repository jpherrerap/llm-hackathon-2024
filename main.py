from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
