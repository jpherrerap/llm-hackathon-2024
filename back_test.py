import os
import sys
import json
from dotenv import load_dotenv
from back.client import BackClient

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
            }
        ]
    }
    with open("test_db_knowledge.json", "w") as f:
        json.dump(knowledge_db, f, indent=2)

    # Crear base de datos de tickets de prueba
    ticket_db = {"tickets": []}
    with open("test_db_tickets.json", "w") as f:
        json.dump(ticket_db, f, indent=2)

def remove_test_databases():
    os.remove("test_db_knowledge.json")
    os.remove("test_db_tickets.json")

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

    queries = [
        "Hola, necesito ayuda con una devolución",
        "¿Cuál es la política de devoluciones?",
        "¿Cuándo llegará mi pedido?",
        "¿Cuál es el significado de la vida?",
        "Gracias por tu ayuda"
    ]

    for query in queries:
        print(f"\nUsuario: {query}")
        response = back_client.process_user_query(query, user_data, conversation_history)
        print(f"Asistente: {response}")

    # Verificar tickets guardados
    print("\nTickets guardados:")
    for ticket in back_client.ticket_db.get_all_tickets():
        print(f"ID: {ticket['id']}, Query: {ticket['query']}")

    # Eliminar bases de datos de prueba
    remove_test_databases()

if __name__ == "__main__":
    test_backend()
