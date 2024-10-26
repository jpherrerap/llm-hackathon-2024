import os
import sys
import json
from dotenv import load_dotenv
from back.client import BackClient
import shutil

# Añadir el directorio actual al sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def create_test_databases():
    # Crear base de datos de conocimientos de prueba
    knowledge_db = {
        "faqs": [
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

    # Crear base de datos de tickets de prueba
    ticket_db = {"tickets": []}
    with open("test_db_tickets.json", "w", encoding="utf-8") as f:
        json.dump(ticket_db, f, indent=2, ensure_ascii=False)

def remove_test_databases():
    os.remove("test_db_knowledge.json")
    os.remove("test_db_tickets.json")
    # Eliminar la base de datos de ChromaDB
    shutil.rmtree("./chroma_db", ignore_errors=True)

def test_backend():
    # Crear bases de datos de prueba
    create_test_databases()

    # Inicializar el BackClient
    back_client = BackClient("test_db_knowledge.json", "test_db_tickets.json")

    # Iniciar la conversación
    print("Iniciando conversación:")
    welcome_message = back_client.start_conversation()
    print(f"Asistente: {welcome_message}")

    # Simular una conversación
    user_data = {"name": "Juan Pérez", "email": "juan@example.com", "phone": "123456789"}
    conversation_history = [{"role": "assistant", "content": welcome_message}]

    # Usar las preguntas de la base de FAQs
    with open("test_db_knowledge.json", "r") as f:
        knowledge_db = json.load(f)
    
    queries = [faq["question"] for faq in knowledge_db["faqs"]]
    queries.append("¿Tienen alguna promoción actual?")  # Pregunta no en la base de datos
    queries.append("Gracias por tu ayuda")

    ticket_id = None
    for query in queries:
        print(f"\nUsuario: {query}")
        response, ticket_id = back_client.process_user_query(query, user_data, conversation_history, ticket_id)
        print(f"Asistente: {response}")

    # Verificar tickets guardados
    print("\nTickets guardados:")
    for ticket in back_client.ticket_db.get_all_tickets():
        print(f"ID: {ticket['id']}")
        print(f"Queries: {ticket['queries']}")
        print(f"User Data: {ticket['user_data']}")
        print("---")

    # Eliminar bases de datos de prueba
    remove_test_databases()

if __name__ == "__main__":
    test_backend()
