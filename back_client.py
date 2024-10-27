from back.client import BackClient

def main():
    client = BackClient("db_knowledge.json", "db_tickets.json")
    print("Starting Swarm CLI 🐝")
    client.set_user_data(name="Sebastian", email="sebag@gmail.com", phone="1234567890")
    message = client.start_conversation().messages[-1]
    print(f"{message['role']}: {message['content']}")

    while True:
        user_input = input("\033[90mUsuario\033[0m: ")
        if user_input.lower() == 'salir':
            break
        response = client.process_user_query(user_input)
        message = response.messages[-1]
        print(f"{message['role']}({response.agent.name}): {message['content']}")

    print("\nHistorial de la conversación:")
    for message in client.get_conversation_history():
        print(f"{message['role'].capitalize()}: {message['content']}")

if __name__ == "__main__":
    main()
