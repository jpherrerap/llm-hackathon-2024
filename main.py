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
import asyncio
import socket

# read local .env file
_ = load_dotenv(find_dotenv())
chat_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# Connect to MongoDB
def is_running_in_docker():
    try:
        with open('/proc/1/cgroup', 'rt') as ifh:
            return 'docker' in ifh.read()
    except FileNotFoundError:
        return False

if is_running_in_docker():
    uri = os.environ.get("MONGO_URI", "mongodb://mongodb:27017")
    PORT = 8001
else:
    uri = os.environ.get("EXTERNAL_MONGO_URI", "mongodb://localhost:27017")
    PORT = 8000
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
    client = await client_pool.get_client()
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data['type'] == 'start_conversation':
                user_data = message_data['content']
                client.set_user_data(user_data['name'], user_data['email'], user_data['phone'])
                response = client.start_conversation()
                await websocket.send_text(json.dumps({
                    'type': 'conversation_started',
                    'content': response.messages[-1]["content"]
                }))
            
            elif message_data['type'] == 'user_query':
                response = client.process_user_query(message_data['content'])
                await websocket.send_text(json.dumps({
                    'type': 'assistant_response',
                    'content': response.messages[-1]["content"]
                }))
            
            elif message_data['type'] == 'get_conversation_history':
                history = client.get_conversation_history()
                await websocket.send_text(json.dumps({
                    'type': 'conversation_history',
                    'content': history
                }))
    
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    finally:
        await client_pool.release_client(client)

@app.get("/api/tickets")
async def get_tickets():
    client = await client_pool.get_client()
    try:
        tickets = client.get_all_tickets()
        # Transformar los tickets al formato esperado por el frontend
        formatted_tickets = [
            {
                "id": ticket["id"],
                "title": f"Consulta de {ticket['user_data']['name']}",
                "description": ticket['conversation'][0]['content'] if ticket['conversation'] else "Sin descripción",
                "createdAt": ticket.get('createdAt', "Fecha no disponible"),
                "resolved": ticket.get('resolved', False)
            }
            for ticket in tickets
        ]
        return formatted_tickets
    finally:
        await client_pool.release_client(client)

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
    client = await client_pool.get_client()
    try:
        client.set_user_data(user_data.name, user_data.email, user_data.phone)
        response = client.start_conversation()
        return {"message": response.messages[-1]["content"]}
    finally:
        await client_pool.release_client(client)

@app.post("/process_query")
async def process_query(user_query: UserQuery):
    client = await client_pool.get_client()
    try:
        if not client.user_data:
            raise HTTPException(status_code=400, detail="Conversation not started. Please start a conversation first.")
        response = client.process_user_query(user_query.query)
        return {"message": response.messages[-1]["content"]}
    finally:
        await client_pool.release_client(client)

@app.get("/tickets")
async def get_tickets():
    client = await client_pool.get_client()
    try:
        tickets = client.get_all_tickets()
        return tickets
    finally:
        await client_pool.release_client(client)

@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    client = await client_pool.get_client()
    try:
        ticket = client.get_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return ticket
    finally:
        await client_pool.release_client(client)

# Pool de conexiones para BackClient
class BackClientPool:
    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self.clients = asyncio.Queue(maxsize=max_connections)
        self.semaphore = asyncio.Semaphore(max_connections)

    async def get_client(self):
        async with self.semaphore:
            if self.clients.empty():
                return BackClient("db_knowledge.json", "db_tickets.json")
            return await self.clients.get()

    async def release_client(self, client):
        await self.clients.put(client)

client_pool = BackClientPool()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
