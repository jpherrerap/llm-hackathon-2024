import json
import os
from typing import Dict, List, Any
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter

class KnowledgeDatabase:
    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.vectorstore = None

    def initialize_from_documents(self, documents: List[Document]):
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        # Debug: Print the texts and metadatas
        print("Texts:", texts)
        print("Metadatas:", metadatas)
        
        # Ensure all texts are strings
        assert all(isinstance(text, str) for text in texts), "All texts must be strings"
        
        self.vectorstore = Chroma.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas,
            persist_directory="./chroma_db"
        )

    def search_faq(self, query: str) -> List[Dict[str, Any]]:
        if not self.vectorstore:
            raise ValueError("Vector store not initialized. Call initialize_from_documents first.")
        results = self.vectorstore.similarity_search_with_score(query, k=3)
        return [
            {
                "question": doc.metadata['question'],
                "answer": doc.page_content,
                "score": score
            } for doc, score in results
        ]

    def add_document(self, document: Document):
        if not self.vectorstore:
            raise ValueError("Vector store not initialized. Call initialize_from_documents first.")
        self.vectorstore.add_texts([document.page_content], [document.metadata])

class JSONAdapter:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load_faqs(self) -> List[Dict[str, str]]:
        with open(self.file_path, 'r') as f:
            database = json.load(f)
        return database['faqs']

    def save_faq(self, question: str, answer: str):
        with open(self.file_path, 'r+') as f:
            database = json.load(f)
            database['faqs'].append({"question": question, "answer": answer})
            f.seek(0)
            f.truncate()
            json.dump(database, f, indent=2)

    def get_all_faqs(self) -> List[Dict[str, str]]:
        return self.load_faqs()

class FAQManager:
    def __init__(self, json_file: str):
        self.client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
        )
        self.embeddings = OpenAIEmbeddings(client=self.client)
        self.json_adapter = JSONAdapter(json_file)
        self.knowledge_db = None
        self._initialize_knowledge_db()

    def _initialize_knowledge_db(self):
        faqs = self.json_adapter.load_faqs()
        for faq in faqs:
            print(faq)
        # Create a list of Document objects
        documents = [
            Document(
                page_content=f"{faq['question']} {faq['answer']}",
                metadata={"question": faq["question"], "answer": faq["answer"]}
            ) for faq in faqs
        ]
        
        for doc in documents:
            print(doc)

        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1800, chunk_overlap=100)
        all_splits = text_splitter.split_documents(documents)

        # Create and store the vector database
        self.knowledge_db = Chroma.from_documents(
            documents=all_splits,
            embedding=self.embeddings,
            collection_name="faq-collection",
            persist_directory="./chroma_db"
        )

        print(f"Vector database initialized with {len(all_splits)} documents.")

    def search_faq(self, query: str) -> List[Dict[str, Any]]:
        if not self.knowledge_db:
            raise ValueError("Vector store not initialized.")
        results = self.knowledge_db.similarity_search_with_score(query, k=3)
        return [
            {
                "question": doc.metadata['question'],
                "answer": doc.metadata['answer'],
                "score": score
            } for doc, score in results
        ]

    def add_faq(self, question: str, answer: str):
        self.json_adapter.save_faq(question, answer)
        new_doc = Document(page_content=question, metadata={"answer": answer})
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1800, chunk_overlap=100)
        splits = text_splitter.split_documents([new_doc])
        self.knowledge_db.add_documents(splits)

    def get_all_faqs(self) -> List[Dict[str, str]]:
        return self.json_adapter.get_all_faqs()

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
                "queries": [query]
            })
            f.seek(0)
            f.truncate()
            json.dump(database, f, indent=2)
        return ticket_id

    def update_ticket(self, ticket_id: str, query: str):
        with open(self.database_file, 'r+') as f:
            database = json.load(f)
            for ticket in database['tickets']:
                if ticket['id'] == ticket_id:
                    ticket['queries'].append(query)
                    break
            f.seek(0)
            f.truncate()
            json.dump(database, f, indent=2)

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
