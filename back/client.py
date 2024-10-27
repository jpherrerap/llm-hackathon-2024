import os
from typing import Dict, List, Any
from dotenv import load_dotenv
from back.agents import AgentManager
from back.database_manager import TicketDatabase

load_dotenv()

class BackClient:
    """
    BackClient manages the interaction between the user, the agent system, and the ticket database.

    This class handles user data, conversation flow, and ticket management. It provides methods
    to start conversations, process user queries, and retrieve conversation history and tickets.

    Attributes:
        ticket_db (TicketDatabase): An instance of TicketDatabase for managing tickets.
        agent_manager (AgentManager): An instance of AgentManager for handling agent interactions.
        user_data (Dict[str, str]): Stores current user information.

    Args:
        knowledge_db_file (str): Path to the knowledge database file.
        ticket_db_file (str): Path to the ticket database file.
    """

    def __init__(self, knowledge_db_file: str, ticket_db_file: str):
        self.ticket_db = TicketDatabase(ticket_db_file)
        self.agent_manager = AgentManager(global_context={"knowledge_db_file": knowledge_db_file})
        self.user_data = None

    def set_user_data(self, name: str, email: str, phone: str) -> Dict[str, str]:
        user_data = {"name": name, "email": email, "phone": phone}
        user_data["ticket_id"] = self.ticket_db.save_ticket(user_data, "Inicio de conversación", "Bienvenido al sistema de atención al cliente.")
        self.user_data = user_data
        return user_data

    def start_conversation(self):
        content = "¡Hola! Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?"
        self.agent_manager.messages.append({"role": "assistant", "content": content, "sender": "WelcomeAgent"})
        self.ticket_db.update_ticket(self.user_data["ticket_id"], "Sistema", content)
        return self.agent_manager

    def process_user_query(self, user_query: str):
        self.ticket_db.update_ticket(self.user_data["ticket_id"], "Usuario", user_query)
        response = self.agent_manager.run(user_query=user_query, context=self.user_data)
        assistant_response = response.messages[-1]["content"]
        self.ticket_db.update_ticket(self.user_data["ticket_id"], "Asistente", assistant_response)
        return response

    def get_conversation_history(self):
        return self.agent_manager.messages

    def get_all_tickets(self) -> List[Dict[str, Any]]:
        return self.ticket_db.get_all_tickets()

    def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        return self.ticket_db.get_ticket(ticket_id)

# Ejemplo de uso
if __name__ == "__main__":
    back_client = BackClient("db_knowledge.json", "db_tickets.json")
    
    back_client.set_user_data(name="Sebastian", email="sebag@gmail.com", phone="1234567890")

    welcome_message = back_client.start_conversation()
    print("Asistente:", welcome_message.messages[-1]["content"])

    while True:
        user_input = input("Usuario: ")
        if user_input.lower() == 'salir':
            break
        response = back_client.process_user_query(user_input)
        message = response.messages[-1]
        print(f"{message['role']}({response.agent.name}): {message['content']}")

    print("\nHistorial de la conversación:")
    for message in back_client.get_conversation_history():
        print(f"{message['role'].capitalize()}: {message['content']}")
