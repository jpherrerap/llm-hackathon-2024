import os
from typing import Dict
from dotenv import load_dotenv
from openai import OpenAI
from swarm import Swarm
from back.agents import create_triage_agent, create_database_agent, create_customer_service_agent
from back.database_manager import DatabaseManager

load_dotenv()

class BackClient:
    def __init__(self, database_file: str):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=self.groq_api_key,
        )
        self.swarm = Swarm(client=self.client)
        self.db_manager = DatabaseManager(database_file)

        # Inicializar agentes
        self.triage_agent = create_triage_agent()
        self.database_agent = create_database_agent(self.db_manager)
        self.customer_service_agent = create_customer_service_agent()

    def process_user_query(self, user_query: str, user_data: Dict[str, str]) -> str:
        # Guardar el ticket de consulta
        ticket_id = self.db_manager.save_ticket(user_data, user_query)

        # Iniciar con el agente de triage
        triage_response = self.swarm.run(
            agent=self.triage_agent,
            messages=[{"role": "user", "content": user_query}]
        )

        if triage_response.agent.name == "DatabaseAgent":
            # Consultar la base de datos
            db_response = self.swarm.run(
                agent=self.database_agent,
                messages=[{"role": "user", "content": user_query}]
            )
            
            if "No se encontró información" in db_response.messages[-1]["content"]:
                # Si no se encuentra información, derivar al agente de servicio al cliente
                cs_response = self.swarm.run(
                    agent=self.customer_service_agent,
                    messages=[{"role": "user", "content": user_query}]
                )
                return cs_response.messages[-1]["content"]
            else:
                return db_response.messages[-1]["content"]
        else:
            return "Lo siento, no puedo procesar esta consulta en este momento."

    def get_user_data(self) -> Dict[str, str]:
        print("Por favor, proporcione sus datos:")
        name = input("Nombre: ")
        email = input("Email: ")
        phone = input("Teléfono: ")
        return {"name": name, "email": email, "phone": phone}

# Ejemplo de uso
if __name__ == "__main__":
    back_client = BackClient("database.json")
    
    while True:
        user_input = input("Usuario: ")
        if user_input.lower() == 'salir':
            break
        user_data = back_client.get_user_data()
        response = back_client.process_user_query(user_input, user_data)
        print("Asistente:", response)