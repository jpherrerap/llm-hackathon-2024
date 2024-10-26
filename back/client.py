import os
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from swarm import Swarm
from back.agents import (
    create_welcome_agent, 
    create_triage_agent, 
    create_database_search_agent,
    create_answer_selection_agent, 
    create_customer_service_agent
)
from back.database_manager import FAQManager, TicketDatabase

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

        # Inicializar agentes
        self.welcome_agent = create_welcome_agent()
        self.triage_agent = create_triage_agent()
        self.database_search_agent = create_database_search_agent(self.faq_manager)
        self.answer_selection_agent = create_answer_selection_agent()
        self.customer_service_agent = create_customer_service_agent()

    def start_conversation(self) -> str:
        welcome_response = self.swarm.run(
            agent=self.welcome_agent,
            messages=[{"role": "system", "content": "Inicia la conversación con el usuario."}]
        )
        return welcome_response.messages[-1]["content"]

    def process_user_query(self, user_query: str, user_data: Dict[str, str], conversation_history: List[Dict[str, str]], ticket_id: str = None) -> Tuple[str, str]:
        if not ticket_id:
            ticket_id = self.ticket_db.save_ticket(user_data, user_query)
        else:
            self.ticket_db.update_ticket(ticket_id, user_query)

        conversation_history.append({"role": "user", "content": user_query})

        triage_response = self.swarm.run(
            agent=self.triage_agent,
            messages=conversation_history
        )

        if "DatabaseAgent" in triage_response.messages[-1]["content"]:
            db_search_response = self.swarm.run(
                agent=self.database_search_agent,
                messages=[{"role": "user", "content": user_query}]
            )
            
            search_result = eval(db_search_response.messages[-1]["content"])
            
            if search_result["answer"] and search_result["confidence"] > 0.7:  # Umbral de confianza
                response = f"Basado en la pregunta '{search_result['question']}', la respuesta es: {search_result['answer']}"
            else:
                cs_response = self.swarm.run(
                    agent=self.customer_service_agent,
                    messages=[{"role": "user", "content": user_query}]
                )
                response = cs_response.messages[-1]["content"]
        else:
            welcome_response = self.swarm.run(
                agent=self.welcome_agent,
                messages=conversation_history + [{"role": "system", "content": "Continúa la conversación con el usuario."}]
            )
            response = welcome_response.messages[-1]["content"]

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
