import json
from typing import Dict

class DatabaseManager:
    def __init__(self, database_file: str):
        self.database_file = database_file

    def search_faq(self, query: str) -> str:
        with open(self.database_file, 'r') as f:
            database = json.load(f)
        for item in database['faqs']:
            if query.lower() in item['question'].lower():
                return item['answer']
        return "No se encontró información en la base de datos."

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
            json.dump(database, f, indent=2)
        return ticket_id
