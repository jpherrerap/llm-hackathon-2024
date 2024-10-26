import os
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from swarm import Swarm
from back.agents import create_triage_agent
from back.database_manager import FAQManager, TicketDatabase
import json

load_dotenv()

class BackClient:
    def __init__(self, knowledge_db_file: str, ticket_db_file: str):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is not set in the environment variables.")
        
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=self.groq_api_key,
        )
        self.swarm = Swarm(client=self.client)
        self.faq_manager = FAQManager(knowledge_db_file)
        self.ticket_db = TicketDatabase(ticket_db_file)

        # Inicializar agente de triage
        self.triage_agent = create_triage_agent(self.faq_manager)

    def start_conversation(self) -> str:
        welcome_response = self.swarm.run(
            agent=self.triage_agent,
            messages=[{"role": "system", "content": "Inicia la conversación con un saludo de bienvenida."}]
        )
        try:
            result = json.loads(welcome_response.messages[-1]["content"])
            return result["response"]
        except json.JSONDecodeError:
            return welcome_response.messages[-1]["content"]

    def process_user_query(self, user_query: str, user_data: Dict[str, str], conversation_history: List[Dict[str, str]], ticket_id: str = None) -> Tuple[str, str]:
        if not ticket_id:
            ticket_id = self.ticket_db.save_ticket(user_data, user_query)
        else:
            self.ticket_db.update_ticket(ticket_id, user_query)

        conversation_history.append({"role": "user", "content": user_query})

        triage_response = self.swarm.run(
            agent=self.triage_agent,
            messages=[
                {"role": "system", "content": "Procesa la consulta del usuario y proporciona una respuesta adecuada."},
                *conversation_history
            ]
        )

        try:
            result = json.loads(triage_response.messages[-1]["content"])
            response = result["response"]
        except json.JSONDecodeError:
            response = triage_response.messages[-1]["content"]

        conversation_history.append({"role": "assistant", "content": response})
        return response, ticket_id

    def get_user_data(self) -> Dict[str, str]:
        print("Por favor, proporcione sus datos:")
        name = input("Nombre: ")
        email = input("Email: ")
        phone = input("Teléfono: ")
        return {"name": name, "email": email, "phone": phone}

# Ejemplo de uso
if __name__ == "__main__":
    back_client = BackClient("knowledge_db.json", "ticket_db.json")
    
    conversation_history = []
    user_data = back_client.get_user_data()
    ticket_id = None

    welcome_message = back_client.start_conversation()
    print("Asistente:", welcome_message)
    conversation_history.append({"role": "assistant", "content": welcome_message})

    while True:
        user_input = input("Usuario: ")
        if user_input.lower() == 'salir':
            break
        response, ticket_id = back_client.process_user_query(user_input, user_data, conversation_history, ticket_id)
        print("Asistente:", response)
