import os
import sys
import json
from dotenv import load_dotenv
from back.client import BackClient
import shutil
from back.database_manager import FAQManager
from langchain.schema import Document
import tempfile

# Añadir el directorio actual al sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()


# def test_chroma_db():
#     # Crear un directorio temporal para la base de datos
#     temp_dir = tempfile.mkdtemp()
    
#     # Crear una instancia temporal de FAQManager
#     temp_json_file = os.path.join(temp_dir, "temp_test_db.json")
#     with open(temp_json_file, "w") as f:
#         json.dump({"faqs": []}, f)
    
#     faq_manager = FAQManager(temp_json_file)
    
#     # Crear dos documentos de ejemplo
#     doc1 = Document(
#         page_content="Los clientes tienen 30 días para devolver productos no utilizados.",
#         metadata={
#             "question": "¿Cuál es la política de devoluciones?",
#             "answer": "Los clientes tienen 30 días para devolver productos no utilizados."
#         }
#     )
#     doc2 = Document(
#         page_content="Aceptamos tarjetas de cr��dito, débito, PayPal y transferencia bancaria.",
#         metadata={
#             "question": "¿Qué métodos de pago aceptan?",
#             "answer": "Aceptamos tarjetas de crédito, débito, PayPal y transferencia bancaria."
#         }
#     )
    
#     # Añadir documentos a la base de datos vectorial
#     faq_manager.knowledge_db.add_documents([doc1, doc2])
    
#     # Realizar una búsqueda de prueba
#     query = "política de devoluciones"
#     results = faq_manager.search_faq(query, k=1)
    
#     # Verificar los resultados
#     assert len(results) == 1, "Se esperaba 1 resultado"
#     assert "política de devoluciones" in results[0]["question"].lower(), "La pregunta no coincide con la consulta"
    
#     print("Test de Chroma DB completado con éxito.")
    
#     # Limpiar
#     shutil.rmtree(temp_dir, ignore_errors=True)

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
    if os.path.exists("test_db_knowledge.json"):
        os.remove("test_db_knowledge.json")
    if os.path.exists("test_db_tickets.json"):
        os.remove("test_db_tickets.json")
    # Eliminar la base de datos de ChromaDB
    if os.path.exists("./chroma_db"):
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
    with open("test_db_knowledge.json", "r", encoding="utf-8") as f:
        knowledge_db = json.load(f)
    
    queries = [faq["question"] for faq in knowledge_db["faqs"]]
    queries.append("¿Tienen alguna promoción actual?")  # Pregunta no en la base de datos
    queries.append("¿Podrías explicarme más sobre los métodos de pago?")  # Pide aclaración
    queries.append("No entendí bien lo de la política de devoluciones, ¿puedes repetirlo?")  # Pide reexplicación
    queries.append("Gracias por tu ayuda")

    ticket_id = None
    for query in queries:
        print(f"\nUsuario: {query}")
        response, ticket_id = back_client.process_user_query(query, user_data, conversation_history, ticket_id)
        print(f"Asistente: {response}")
        conversation_history.append({"role": "user", "content": query})
        conversation_history.append({"role": "assistant", "content": response})

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
