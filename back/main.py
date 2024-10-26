from back.back_client import BackClient

def main():
    back_client = BackClient("knowledge_db.json", "tickets_db.json")
    
    while True:
        user_data = back_client.get_user_data()
        user_input = input("Usuario: ")
        if user_input.lower() == 'salir':
            break
        response = back_client.process_user_query(user_input, user_data)
        print("Asistente:", response)

if __name__ == "__main__":
    main()
