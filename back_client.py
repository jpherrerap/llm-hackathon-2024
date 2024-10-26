from back.client import BackClient

def main():
    back_client = BackClient("db_knowledge.json", "db_tickets.json")
    
    user_data = back_client.get_user_data()
    conversation_history = []
    ticket_id = None

    while True:
        user_input = input("Usuario: ")
        if user_input.lower() == 'salir':
            break
        response, ticket_id = back_client.process_user_query(user_input, user_data, conversation_history, ticket_id)
        print("Asistente:", response)
        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
