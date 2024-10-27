import os
from openai import OpenAI
from swarm import Agent, Swarm
from typing import List, Dict, Any
from back.database_manager import FAQManager
import json

def search_database(messages: List[Dict[str, str]], context_variables: Dict[str, Any]) -> str:
    """
    Searches the FAQ database for the most relevant answers.

    Args:
        messages (List[Dict[str, str]]): List of messages from the conversation history.
        context_variables (Dict[str, Any]): Context variables, including the path to the knowledge database file.

    Returns:
        str: Formatted response with the best matches from the database.
    """
    faq_manager = FAQManager(context_variables["knowledge_db_file"])
    
    if isinstance(messages, str): # 5 ultimas consultas
        enriched_query = [messages]
    else:
        enriched_query = messages[-5:]

    enriched_query = " ".join(enriched_query)
    results = faq_manager.search_faq(enriched_query, k=3)
    print(f"\033[92mDatabase top-3 results:\033[0m")
    if not results:
        return json.dumps({"answer": None, "confidence": 0})
    
    for result in results:
        print(f"Question: {result['question']}")
        print(f"Answer: {result['answer']}")
        print(f"Confidence: {result['score']}")
        print("---")
    
    best_result = max(results, key=lambda x: x['score'])
    db_response = f"Respuestas de la base de datos:\n"
    for result in results:
        db_response += f"Pregunta: {result['question']}\n"
        db_response += f"Respuesta: {result['answer']}\n"
        db_response += f"Confianza: {result['score']}\n"
        db_response += "---\n"
    return db_response

def handle_customer_service(messages: List[Dict[str, str]], context_variables: Dict[str, Any]) -> str:
    """
    Handles customer service queries that cannot be answered by the database.

    Args:
        messages (List[Dict[str, str]]): List of messages from the conversation history.
        context_variables (Dict[str, Any]): Context variables.

    Returns:
        str: Generic customer service response.
    """
    response = "Entiendo tu consulta. Un agente de servicio al cliente se pondrá en contacto contigo pronto para ayudarte mejor."
    return response

# def transfer_to_database_agent(messages: List[Dict[str, str]], context_variables: Dict[str, Any]) -> str:
#     return database_agent

def transfer_to_customer_service_agent(messages: List[Dict[str, str]], context_variables: Dict[str, Any]) -> str:
    """
    Transfers the conversation to the customer service agent.

    Args:
        messages (List[Dict[str, str]]): List of messages from the conversation history.
        context_variables (Dict[str, Any]): Context variables.

    Returns:
        Agent: Instance of the customer service agent.
    """
    return customer_service_agent

def transfer_back_to_triage_agent(messages: List[Dict[str, str]], context_variables: Dict[str, Any]) -> str:
    """
    Transfers the conversation back to the triage agent.

    Args:
        messages (List[Dict[str, str]]): List of messages from the conversation history.
        context_variables (Dict[str, Any]): Context variables.

    Returns:
        Agent: Instance of the triage agent.
    """
    return triage_agent

triage_agent = Agent(
    name="TriageAgent",
    instructions="Trasfiere al usuario a un agente de base de datos para responder la consulta.\
        Solo si el usuario no esta conforme, transfiere a un agente de servicio al cliente.",
    tool_choice="auto",
    parallel_tool_calls=False,
    functions=[search_database, transfer_to_customer_service_agent],
)

# database_agent = Agent(
#     name="DatabaseAgent",
#     instructions="Selecciona la mejor respuesta para la consulta del usuario. Vuelve al agente de triaje para saber si hay mas dudas.",
#     tool_choice="auto",
#     parallel_tool_calls=False,
#     functions=[search_database, transfer_back_to_triage_agent, transfer_to_customer_service_agent],
# )

customer_service_agent = Agent(
    name="CustomerServiceAgent",
    instructions="Maneja consultas de servicio al cliente que no se pueden responder con la\
        información de la base de datos. En caso de terminar la solicitud, transfiere la consulta de nuevo al agente de triaje.",
    tool_choice="auto",
    parallel_tool_calls=False,
    functions=[handle_customer_service, transfer_back_to_triage_agent],
)

def pretty_print_messages(messages) -> None:
    """
    Prints the messages and tool calls from agents in a formatted manner.

    Args:
        messages (List[Dict]): List of messages and tool calls from agents.
    """
    for message in messages:
        if message["role"] != "assistant":
            continue

        # print agent name in blue
        print(f"\033[94m{message['sender']}\033[0m:", end=" ")

        # print response, if any
        if message["content"]:
            print(message["content"])

        # print tool calls in purple, if any
        tool_calls = message.get("tool_calls") or []
        if len(tool_calls) > 1:
            print()
        for tool_call in tool_calls:
            f = tool_call["function"]
            name, args = f["name"], f["arguments"]
            arg_str = json.dumps(json.loads(args)).replace(":", "=")
            print(f"\033[95m{name}\033[0m({arg_str[1:-1]})")

class AgentManager:
    """
    Manages the interaction between different agents and maintains the conversation context.
    """

    def __init__(self, global_context: Dict[str, Any] = {}):
        """
        Initializes the AgentManager.

        Args:
            global_context (Dict[str, Any], optional): Global context for all agents. Defaults to {}.
        """
        self.swarm = Swarm(
            client = OpenAI(
                # base_url="https://api.groq.com/openai/v1",
                api_key=os.getenv("OPENAI_API_KEY"),
            ),
            
        )
        self.messages = []
        self.agent = triage_agent
        self.global_context = global_context
        
    def run(self, user_query: str, context: Dict[str, Any] = {}):
        """
        Runs a user query through the agent system.

        Args:
            user_query (str): User's query.
            context (Dict[str, Any], optional): Specific context for this query. Defaults to {}.

        Returns:
            Response: Response from the current agent.
        """
        self.messages.append({"role": "user", "content": user_query})

        response = self.swarm.run(
            agent=self.agent,
            messages=self.messages,
            context_variables=self.global_context or context,
            stream=False,
            debug=False,
        )

        pretty_print_messages(response.messages)
        self.messages.extend([{"role": "assistant", "content": response.messages[-1]["content"]}])
        self.agent = response.agent
        return response
    
def run_demo_loop(
    starting_agent = triage_agent, context_variables=None, stream=False, debug=False
) -> None:
    """
    Runs an interactive demo loop for the agent system.

    Args:
        starting_agent (Agent, optional): Initial agent. Defaults to triage_agent.
        context_variables (Dict, optional): Context variables. Defaults to None.
        stream (bool, optional): Whether to use streaming. Defaults to False.
        debug (bool, optional): Whether to activate debug mode. Defaults to False.
    """
    client = Swarm(
        client = OpenAI(
            # base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("OPENAI_API_KEY"),
        ),
        
    )
    print("Starting Swarm CLI 🐝")

    messages = []
    agent = starting_agent

    while True:
        user_input = input("\033[90mUser\033[0m: ")
        messages.append({"role": "user", "content": user_input})

        response = client.run(
            agent=agent,
            messages=messages,
            context_variables=context_variables or {},
            stream=stream,
            debug=debug,
        )

        pretty_print_messages(response.messages)
        messages.extend([{"role": "assistant", "content": response.messages[-1]["content"]}])
        agent = response.agent
    
if __name__ == "__main__":
    run_demo_loop(starting_agent=triage_agent)
