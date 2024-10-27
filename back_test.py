import os
import sys
import json
from dotenv import load_dotenv
from back.client import BackClient
import shutil

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def create_test_databases():
    """
    Creates test databases for knowledge and tickets.
    
    This function generates sample data for FAQs and an empty ticket database,
    saving them as JSON files for testing purposes.
    """
    # Create test knowledge database
    knowledge_db = {
        "faq": [
            {
                "question": "¿Cuál es la política de devoluciones?",
                "answer": "Los clientes tienen 30 días para devolver productos no utilizados."
            },
            {
                "question": "¿Cuáles son los métodos de pago aceptados?",
                "answer": "Aceptamos tarjetas de crédito, débito, PayPal y transferencia bancaria."
            },
            {
                "question": "¿Cuánto tiempo tarda la entrega?",
                "answer": "El tiempo de entrega estándar es de 3 a 5 días hábiles."
            }
        ]
    }
    with open("test_db_knowledge.json", "w", encoding="utf-8") as f:
        json.dump(knowledge_db, f, indent=2, ensure_ascii=False)

    # Create test ticket database
    ticket_db = {"tickets": []}
    with open("test_db_tickets.json", "w", encoding="utf-8") as f:
        json.dump(ticket_db, f, indent=2, ensure_ascii=False)

def remove_test_databases():
    """
    Removes test databases and ChromaDB files.
    
    This function cleans up the test environment by deleting temporary database files
    and the ChromaDB directory.
    """
    if os.path.exists("test_db_knowledge.json"):
        os.remove("test_db_knowledge.json")
    if os.path.exists("test_db_tickets.json"):
        os.remove("test_db_tickets.json")
    # Remove ChromaDB database
    if os.path.exists("./chroma_db"):
        shutil.rmtree("./chroma_db", ignore_errors=True)

def test_backend():
    """
    Runs a series of tests on the backend system.
    
    This function creates test databases, initializes a BackClient, and processes
    a series of user queries to test various aspects of the system, including
    FAQ responses and customer service agent transfer.
    """
    # Create test databases
    create_test_databases()

    # Initialize BackClient
    back_client = BackClient("test_db_knowledge.json", "test_db_tickets.json")

    # Set user data
    back_client.set_user_data(name="Juan Pérez", email="juan@example.com", phone="123456789")

    # Start conversation
    print("Starting conversation:")
    welcome_message = back_client.start_conversation()
    print(f"Assistant: {welcome_message.messages[-1]['content']}")

    # Use questions from the FAQ database
    with open("test_db_knowledge.json", "r", encoding="utf-8") as f:
        knowledge_db = json.load(f)
    
    queries = [faq["question"] for faq in knowledge_db["faq"]]
    queries.append("¿Tienen alguna promoción actual?")  # Question not in database
    queries.append("¿Podrías explicarme más sobre los métodos de pago?")  # Ask for clarification
    queries.append("No entendí bien lo de la política de devoluciones, ¿puedes repetirlo?")  # Ask for re-explanation
    queries.append("Tengo un problema con mi pedido, necesito hablar con un agente")  # Should activate customer service
    queries.append("Gracias por tu ayuda")

    for query in queries:
        print(f"\n\033[90mUsuario\033[0m: {query}")
        response = back_client.process_user_query(query)
        # Check if transferred to customer service agent
        if response.agent.name == "CustomerServiceAgent":
            print("The conversation has been transferred to the customer service agent.")
            break

    # Check saved tickets
    print("\nSaved tickets:")
    for ticket in back_client.ticket_db.get_all_tickets():
        print(f"ID: {ticket['id']}")
        print(f"User Data: {ticket['user_data']}")
        print("---")

    # Remove test databases
    remove_test_databases() 

if __name__ == "__main__":
    test_backend()
