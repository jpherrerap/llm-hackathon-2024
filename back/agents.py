from swarm import Agent
from back.database_manager import KnowledgeDatabase

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

def create_database_agent(knowledge_db: KnowledgeDatabase):
    def search_database(query: str) -> str:
        return knowledge_db.search_faq(query)

    return Agent(
        name="DatabaseAgent",
        instructions="Busca información en la base de datos de conocimientos.",
        functions=[search_database],
        model="llama3-groq-70b-8192-tool-use-preview",
        tool_choice="auto"
    )

def create_customer_service_agent():
    return Agent(
        name="CustomerServiceAgent",
        instructions="Maneja consultas de servicio al cliente que no se pueden responder con la información de la base de datos.",
        model="llama3-groq-70b-8192-tool-use-preview",
        tool_choice="auto"
    )

