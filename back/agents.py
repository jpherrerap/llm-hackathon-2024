from swarm import Agent
from back.database_manager import FAQManager
from typing import List, Dict, Any
import json

def create_welcome_agent():
    def welcome_user() -> str:
        return json.dumps({
            "agent": "WelcomeAgent",
            "response": "Bienvenido a nuestro servicio de atención al cliente. ¿En qué puedo ayudarte hoy?"
        })

    return Agent(
        name="WelcomeAgent",
        instructions="Da la bienvenida al usuario y pregunta sobre su necesidad. Responde siempre en formato JSON con las claves 'agent' y 'response'.",
        functions=[welcome_user],
        model="llama3-groq-70b-8192-tool-use-preview",
        tool_choice="auto"
    )

def create_database_search_agent(faq_manager: FAQManager):
    def search_and_select_answer(query: str, conversation_history: List[Dict[str, str]]) -> str:
        context = " ".join([msg["content"] for msg in conversation_history[-5:]])
        enriched_query = f"{context} {query}".strip()

        results = faq_manager.search_faq(enriched_query)
        if not results:
            return json.dumps({"answer": None, "confidence": 0})
        
        best_result = max(results, key=lambda x: x['score'])
        confidence = 1 - best_result['score']
        
        return json.dumps({
            "agent": "DatabaseSearchAgent",
            "answer": best_result['answer'],
            "question": best_result['question'],
            "confidence": confidence
        })

    return Agent(
        name="DatabaseSearchAgent",
        instructions="Busca en la base de datos de conocimientos y selecciona la mejor respuesta para la consulta del usuario.",
        functions=[search_and_select_answer],
        model="llama3-groq-70b-8192-tool-use-preview",
        tool_choice="auto"
    )

def create_customer_service_agent():
    def handle_customer_service(query: str, conversation_history: List[Dict[str, str]]) -> str:
        return json.dumps({
            "agent": "CustomerServiceAgent",
            "response": "Entiendo tu consulta. Permíteme buscar más información para ayudarte mejor."
        })

    return Agent(
        name="CustomerServiceAgent",
        instructions="Maneja consultas de servicio al cliente que no se pueden responder con la información de la base de datos.",
        functions=[handle_customer_service],
        model="llama3-groq-70b-8192-tool-use-preview",
        tool_choice="auto"
    )

def create_triage_agent(faq_manager: FAQManager):
    welcome_agent = create_welcome_agent()
    database_search_agent = create_database_search_agent(faq_manager)
    customer_service_agent = create_customer_service_agent()

    def welcome() -> str:
        response = welcome_agent.run(messages=[{"role": "system", "content": "Da la bienvenida al usuario."}])
        try:
            return json.loads(response.messages[-1]["content"])
        except json.JSONDecodeError:
            return json.dumps({
                "agent": "WelcomeAgent",
                "response": response.messages[-1]["content"]
            })

    def search_database(query: str, conversation_history: List[Dict[str, str]]) -> str:
        response = database_search_agent.run(messages=[
            {"role": "system", "content": "Busca en la base de datos considerando todo el contexto de la conversación."},
            *conversation_history,
            {"role": "user", "content": query}
        ])
        try:
            return json.loads(response.messages[-1]["content"])
        except json.JSONDecodeError:
            return json.dumps({
                "agent": "DatabaseSearchAgent",
                "answer": response.messages[-1]["content"],
                "confidence": 0.5
            })

    def customer_service(query: str, conversation_history: List[Dict[str, str]]) -> str:
        response = customer_service_agent.run(messages=[
            *conversation_history,
            {"role": "user", "content": query}
        ])
        try:
            return json.loads(response.messages[-1]["content"])
        except json.JSONDecodeError:
            return json.dumps({
                "agent": "CustomerServiceAgent",
                "response": response.messages[-1]["content"]
            })

    def triage_and_respond(query: str, conversation_history: List[Dict[str, str]]) -> str:
        if len(conversation_history) == 0:
            return welcome()
        
        db_result = search_database(query, conversation_history)
        
        if db_result.get("answer") and db_result.get("confidence", 0) > 0.7:
            response = f"Basado en la pregunta '{db_result.get('question', '')}', la respuesta es: {db_result['answer']}"
        else:
            cs_result = customer_service(query, conversation_history)
            response = cs_result.get("response", "Lo siento, no pude procesar tu solicitud.")
        
        return json.dumps({
            "agent": "TriageAgent",
            "response": response,
            "next_action": "continue" if "¿Puedo ayudarte con algo más?" not in response else "end"
        })

    return Agent(
        name="TriageAgent",
        instructions="Determina qué agente debe manejar la consulta del usuario y proporciona la respuesta adecuada. Responde siempre en formato JSON con las claves 'agent', 'response', y 'next_action'.",
        functions=[triage_and_respond],
        model="llama3-groq-70b-8192-tool-use-preview",
        tool_choice="auto"
    )
