import json
from typing import Dict, List, Any

class KnowledgeDatabase:
    def __init__(self, database_file: str):
        self.database_file = database_file

    def search_faq(self, query: str) -> str:
        with open(self.database_file, 'r') as f:
            database = json.load(f)
        for item in database['faqs']:
            if query.lower() in item['question'].lower():
                return item['answer']
        return "No se encontró información en la base de datos."

    def add_faq(self, question: str, answer: str):
        with open(self.database_file, 'r+') as f:
            database = json.load(f)
            database['faqs'].append({"question": question, "answer": answer})
            f.seek(0)
            f.truncate()
            json.dump(database, f, indent=2)

    def get_all_faqs(self) -> List[Dict[str, str]]:
        with open(self.database_file, 'r') as f:
            database = json.load(f)
        return database['faqs']

class TicketDatabase:
    def __init__(self, database_file: str):
        self.database_file = database_file

    def save_ticket(self, user_data: Dict[str, str], query: str) -> str:
        with open(self.database_file, 'r+') as f:
            database = json.load(f)
            ticket_id = f"TICKET-{len(database['tickets']) + 1:04d}"
            database['tickets'].append({
                "id": ticket_id,
                "user_data": user_data,
                "query": query
            })
            f.seek(0)
            f.truncate()
            json.dump(database, f, indent=2)
        return ticket_id

    def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        with open(self.database_file, 'r') as f:
            database = json.load(f)
        for ticket in database['tickets']:
            if ticket['id'] == ticket_id:
                return ticket
        return None

    def get_all_tickets(self) -> List[Dict[str, Any]]:
        with open(self.database_file, 'r') as f:
            database = json.load(f)
        return database['tickets']
