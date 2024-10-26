import os
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from swarm import Swarm
from back.agents import (
    create_welcome_agent, 
    create_triage_agent, 
    create_database_agent, 
    create_customer_service_agent
)
from back.database_manager import KnowledgeDatabase, TicketDatabase

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
        self.knowledge_db = KnowledgeDatabase(knowledge_db_file)
        self.ticket_db = TicketDatabase(ticket_db_file)

        # Inicializar agentes
        self.welcome_agent = create_welcome_agent()
        self.triage_agent = create_triage_agent()
        self.database_agent = create_database_agent(self.knowledge_db)
        self.customer_service_agent = create_customer_service_agent()

    def start_conversation(self) -> str:
        welcome_response = self.swarm.run(
            agent=self.welcome_agent,
            messages=[{"role": "system", "content": "Inicia la conversación con el usuario."}]
        )
        return welcome_response.messages[-1]["content"]

    def process_user_query(self, user_query: str, user_data: Dict[str, str], conversation_history: List[Dict[str, str]], ticket_id: str = None) -> Tuple[str, str]:
        # Si no hay ticket_id, crear uno nuevo
        if not ticket_id:
            ticket_id = self.ticket_db.save_ticket(user_data, user_query)
        else:
            # Actualizar el ticket existente con la nueva query
            self.ticket_db.update_ticket(ticket_id, user_query)

        # Agregar la consulta del usuario al historial de la conversación
        conversation_history.append({"role": "user", "content": user_query})

        # Iniciar con el agente de triage
        triage_response = self.swarm.run(
            agent=self.triage_agent,
            messages=conversation_history
        )

        if "DatabaseAgent" in triage_response.messages[-1]["content"]:
            # Consultar la base de datos
            db_response = self.swarm.run(
                agent=self.database_agent,
                messages=[{"role": "user", "content": user_query}]
            )
            
            response = db_response.messages[-1]["content"]
            if "No se encontró información" in response:
                # Si no se encuentra información, derivar al agente de servicio al cliente
                cs_response = self.swarm.run(
                    agent=self.customer_service_agent,
                    messages=[{"role": "user", "content": user_query}]
                )
                response = cs_response.messages[-1]["content"]
        else:
            # Continuar la conversación con el agente de bienvenida
            welcome_response = self.swarm.run(
                agent=self.welcome_agent,
                messages=conversation_history + [{"role": "system", "content": "Continúa la conversación con el usuario."}]
            )
            response = welcome_response.messages[-1]["content"]

        # Agregar la respuesta al historial de la conversación
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
    
    while True:
        user_input = input("Usuario: ")
        if user_input.lower() == 'salir':
            break
        user_data = back_client.get_user_data()
        response = back_client.process_user_query(user_input, user_data, [])
        print("Asistente:", response)
