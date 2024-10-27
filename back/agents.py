import os
from openai import OpenAI
from swarm import Agent, Swarm
from typing import List, Dict, Any
from back.database_manager import FAQManager
import json

def search_database(messages: List[Dict[str, str]], context_variables: Dict[str, Any]) -> str:
    faq_manager = FAQManager(context_variables["knowledge_db_file"])
    
    if isinstance(messages, str):
        enriched_query = [messages]
    else:
        enriched_query = messages[-5:]

    enriched_query = " ".join(enriched_query)
    results = faq_manager.search_faq(enriched_query)
    print(f"\033[92mBest database result:\033[0m {results}")
    if not results:
        return json.dumps({"answer": None, "confidence": 0})
    best_result = max(results, key=lambda x: x['score'])
    db_response = f"Respuesta de la base de datos: {best_result['answer']}"
    return db_response

def handle_customer_service(messages: List[Dict[str, str]], context_variables: Dict[str, Any]) -> str:
    response = "Entiendo tu consulta. Un agente de servicio al cliente se pondrá en contacto contigo pronto para ayudarte mejor."
    return response

# def transfer_to_database_agent(messages: List[Dict[str, str]], context_variables: Dict[str, Any]) -> str:
#     return database_agent

def transfer_to_customer_service_agent(messages: List[Dict[str, str]], context_variables: Dict[str, Any]) -> str:
    return customer_service_agent

def transfer_back_to_triage_agent(messages: List[Dict[str, str]], context_variables: Dict[str, Any]) -> str:
    return triage_agent

triage_agent = Agent(
    name="TriageAgent",
    instructions="Trasfiere al usuario a un agente de base de datos para responder la consulta. Solo si el usuario no esta conforme, transfiere a un agente de servicio al cliente.",
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
    instructions="Maneja consultas de servicio al cliente que no se pueden responder con la información de la base de datos. En caso de terminar la solicitud, transfiere la consulta de nuevo al agente de triaje.",
    tool_choice="auto",
    parallel_tool_calls=False,
    functions=[handle_customer_service, transfer_back_to_triage_agent],
)

def pretty_print_messages(messages) -> None:
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
    def __init__(self, global_context: Dict[str, Any] = {}):
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