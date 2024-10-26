from swarm import Agent
from back.database_manager import FAQManager
from typing import List, Dict, Any

def create_welcome_agent():
    return Agent(
        name="WelcomeAgent",
        instructions="Da la bienvenida al usuario y pregunta sobre su necesidad. Luego, transfiere al agente de triage para cada respuesta del usuario.",
        model="llama3-groq-70b-8192-tool-use-preview",
        tool_choice="auto"
    )

def create_triage_agent():
    def transfer_to_database_agent():
        return "DatabaseAgent"

    return Agent(
        name="TriageAgent",
        instructions="Determina si la consulta del usuario es una pregunta que se puede responder con la base de datos.",
        functions=[transfer_to_database_agent],
        model="llama3-groq-70b-8192-tool-use-preview",
        tool_choice="auto"
    )

def create_database_agent(faq_manager: FAQManager):
    def search_database(query: str) -> List[Dict[str, Any]]:
        return faq_manager.search_faq(query)

    return Agent(
        name="DatabaseAgent",
        instructions="Busca información en la base de datos de conocimientos y devuelve las 3 mejores coincidencias.",
        functions=[search_database],
        model="llama3-groq-70b-8192-tool-use-preview",
        tool_choice="auto"
    )

def create_answer_selection_agent():
    return Agent(
        name="AnswerSelectionAgent",
        instructions="Analiza las 3 mejores coincidencias y selecciona la respuesta más apropiada para la consulta del usuario. Considera los puntajes de similitud. Si ninguna es apropiada, indica que se debe derivar al servicio al cliente.",
        model="llama3-groq-70b-8192-tool-use-preview",
        tool_choice="auto",
    )

def create_customer_service_agent():
    return Agent(
        name="CustomerServiceAgent",
        instructions="Maneja consultas de servicio al cliente que no se pueden responder con la información de la base de datos.",
        model="llama3-groq-70b-8192-tool-use-preview",
        tool_choice="auto"
    )

def create_database_search_agent(faq_manager: FAQManager):
    def search_and_select_answer(query: str) -> Dict[str, Any]:
        results = faq_manager.search_faq(query)
        if not results:
            return {"answer": None, "confidence": 0}
        
        # Analizar los resultados y seleccionar la mejor respuesta
        best_result = max(results, key=lambda x: x['score'])
        confidence = 1 - best_result['score']  # Convertir la distancia en confianza
        
        return {
            "answer": best_result['answer'],
            "question": best_result['question'],
            "confidence": confidence
        }

    return Agent(
        name="DatabaseSearchAgent",
        instructions="Busca en la base de datos de conocimientos y selecciona la mejor respuesta para la consulta del usuario.",
        functions=[search_and_select_answer],
        model="llama3-groq-70b-8192-tool-use-preview",
        tool_choice="auto"
    )
