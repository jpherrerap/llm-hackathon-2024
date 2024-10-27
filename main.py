from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from datetime import datetime
import socket
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List, Dict, Any
from back.client import BackClient
import asyncio
from fastapi.responses import JSONResponse
import argparse
from bson import json_util


def parse_arguments():
    parser = argparse.ArgumentParser(description='FastAPI Server Configuration')
    parser.add_argument(
        '--port', 
        type=int, 
        default=8000, 
        help='Port to run the server on (default: 8000)'
    )
    parser.add_argument(
        '--url', 
        type=str, 
        default=None, 
        help='URL to scrape'
    )
    return parser.parse_args()



# read local .env file
_ = load_dotenv(find_dotenv())
# chat_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# Connect to MongoDB


uri = os.environ.get("MONGO_URI", "mongodb://mongodb:27017")
PORT = 8000


client = MongoClient(uri)
db = client['vue-chatbot']
messages_collection = db['messages']
messages_collection.delete_many({}) # Clear the messages collection
messages_collection.insert_one({'role': 'system', 'content': 'You are a helpful assistant'}) # Add a system message

tickets_collection = db['tickets']

# Get the API key from environment variables

def get_messages():
    messages = list(messages_collection.find({}))
    for message in messages:
        message.pop('_id')
    return messages

app = FastAPI(debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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
        chat_client = BackClient("db_knowledge.json", "db_tickets.json")
        chat_client.set_user_data(name="Sebastian", email="sebag@gmail.com", phone="1234567890")
        message = chat_client.start_conversation().messages[-1]

        ticket_id = f"TICKET-{len(list(tickets_collection.find())) + 1:04d}"
        tickets_collection.insert_one({
                "id": ticket_id,
                "user_data": chat_client.user_data,
                "createdAt": datetime.now().isoformat(),
                "conversation": [],
                "resolved": False
            })
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            if message_data['type'] == 'get_messages':
                messages = get_messages()
                await websocket.send_text(json.dumps({'type': 'message_update', 'content': messages[1:]}))

            if message_data['type'] == 'new_message':
                new_message = message_data['content']
                user_message = {'role': 'user', 'content': new_message}
                if new_message.lower() == 'cerrar':
                    tickets_collection.update_one(
                    {"id": ticket_id},
                        {"$set": {"resolved": True}}
                    )

                messages_collection.insert_one(user_message)
                messages = get_messages()
                await websocket.send_text(json.dumps({'type': 'message_update', 'content': messages[1:]}))

                tickets_collection.update_one(
                    {"id": ticket_id},
                    {"$push": {"conversation": user_message}}
                )
                
                response = chat_client.process_user_query(new_message)
                message = response.messages[-1]
                ai_message = {'role': 'assistant', 'content': message['content']}
                messages_collection.insert_one(ai_message)
                messages = get_messages()
                
                tickets_collection.update_one(
                    {"id": ticket_id},
                    {"$push": {"conversation": ai_message}}
                )
                
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

    try:
        tickets_bson = tickets_collection.find()
        tickets = json.loads(json_util.dumps(tickets_bson))
        formatted_tickets = [
            {
                "id": str(ticket["id"]),  # Ensure id is a string
                "title": f"Consulta de {ticket['user_data']['name']}",
                "description": ticket['conversation'][0]['content'] if ticket['conversation'] else "Sin descripción",
                "createdAt": str(ticket.get('createdAt', "Fecha no disponible")),  # Ensure date is a string
                "resolved": bool(ticket.get('resolved', False)),  # Ensure resolved is a boolean
                # "user_data": ticket['user_data'],
                "conversation": ticket['conversation']
            }
            for ticket in tickets
        ]
        return JSONResponse(content=formatted_tickets)
    except Exception as e:
        print(f"Error in get_tickets: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

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

# Modify your main block at the bottom:
if __name__ == "__main__":
    import uvicorn
    args = parse_arguments()
    
    # Update the PORT variable with the CLI argument
    PORT = args.port
    
    # Store the URL if you need to use it later
    SCRAPE_URL = args.url
    if SCRAPE_URL:
        print(f"URL to scrape: {SCRAPE_URL}")
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)
