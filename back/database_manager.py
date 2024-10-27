import json
import os
import tempfile
import shutil
from typing import Dict, List, Any
from uuid import uuid4
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter

class FAQManager:
    def __init__(self, json_file: str):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"), # TODO: Cambiar por GROQ_API_KEY
            # base_url="https://api.groq.com/openai/v1",
        )
        self.embeddings = OpenAIEmbeddings(
            # client=self.client,
            model="text-embedding-3-small",
            embedding_ctx_length=8191,  # Longitud máxima del contexto
            chunk_size=1000,  # Tamaño del chunk para procesamiento por lotes
        )
        self.json_adapter = JSONAdapter(json_file)
        self.knowledge_db = None
        self.persist_directory = tempfile.mkdtemp()  # Crear un directorio temporal
        self._initialize_knowledge_db()

    def _initialize_knowledge_db(self):
        faqs = self.json_adapter.load_faqs()
        
        if not faqs:
            print("No hay FAQs disponibles para inicializar la base de datos vectorial.")
            self.knowledge_db = Chroma(
                embedding_function=self.embeddings,
                collection_name="faq-collection",
                persist_directory=self.persist_directory
            )
            return

        # Crear documentos manteniendo tanto la pregunta como la respuesta en los metadatos
        documents = []
        for faq in faqs:
            # Usamos la respuesta como contenido principal y guardamos ambos en metadata
            doc = Document(
                page_content=faq["answer"],
                metadata={
                    "question": faq["question"],
                    "answer": faq["answer"]  # Guardamos la respuesta completa en metadata
                },
                id=str(uuid4())  # Agregar un ID único
            )
            documents.append(doc)

        # Configurar el text splitter con parámetros más apropiados para FAQ
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Reducido para mejor manejo de FAQs
            chunk_overlap=200,  # Aumentado para mejor contexto
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Dividir los documentos manteniendo los metadatos
        all_splits = text_splitter.split_documents(documents)
        
        # Asegurarse de que cada split mantenga los metadatos originales
        for split in all_splits:
            # Asegurarse de que los metadatos contengan tanto la pregunta como la respuesta
            if 'question' not in split.metadata or 'answer' not in split.metadata:
                original_doc = next(d for d in documents if d.metadata['question'] == split.metadata['question'])
                split.metadata = original_doc.metadata
            split.id = str(uuid4())  # Asignar un nuevo ID único a cada split

        vector_store = Chroma(
            collection_name="faq-collection",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,  # Where to save data locally, remove if not necessary
        )

        # Crear y persistir la base de datos vectorial
        self.knowledge_db = vector_store.from_documents(
            documents=all_splits,
            embedding=self.embeddings,
            collection_name="faq-collection",
            persist_directory=self.persist_directory,
            ids=[doc.id for doc in all_splits]  # Pasar los IDs explícitamente
        )

    def search_faq(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        if not self.knowledge_db:
            raise ValueError("Vector store no inicializado.")
        
        results = self.knowledge_db.similarity_search_with_score(query, k=k)
        
        # Formatear los resultados manteniendo la información completa
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "question": doc.metadata['question'],
                "answer": doc.metadata['answer'],  # Usar la respuesta completa de metadata
                "score": score
            })
            
        return formatted_results

    def add_faq(self, question: str, answer: str):
        # Guardar en JSON
        self.json_adapter.save_faq(question, answer)
        
        # Crear nuevo documento con metadata completa
        new_doc = Document(
            page_content=answer,
            metadata={
                "question": question,
                "answer": answer
            },
            id=str(uuid4())  # Agregar un ID único
        )
        
        # Dividir el documento
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        splits = text_splitter.split_documents([new_doc])
        
        # Asegurar que cada split mantenga los metadatos completos
        for split in splits:
            split.metadata = new_doc.metadata
            split.id = str(uuid4())  # Asignar un nuevo ID único a cada split
            
        # Añadir a la base de datos vectorial
        self.knowledge_db.add_documents(documents=splits, ids=[doc.id for doc in splits])

    def __del__(self):
        # Check if persist_directory exists before trying to delete it
        if hasattr(self, 'persist_directory'):
            shutil.rmtree(self.persist_directory, ignore_errors=True)

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

    def get_all_faqs(self) -> List[Dict[str, str]]:
        return self.json_adapter.get_all_faqs()

class TicketDatabase:
    def __init__(self, database_file: str):
        self.database_file = database_file

    def save_ticket(self, user_data: Dict[str, str], query: str, response: str) -> str:
        with open(self.database_file, 'r+') as f:
            database = json.load(f)
            ticket_id = f"TICKET-{len(database['tickets']) + 1:04d}"
            database['tickets'].append({
                "id": ticket_id,
                "user_data": user_data,
                "conversation": [
                    {"role": "system", "content": query},
                    {"role": "assistant", "content": response}
                ]
            })
            f.seek(0)
            f.truncate()
            json.dump(database, f, indent=2)
        return ticket_id

    def update_ticket(self, ticket_id: str, role: str, content: str):
        with open(self.database_file, 'r+') as f:
            database = json.load(f)
            for ticket in database['tickets']:
                if ticket['id'] == ticket_id:
                    ticket['conversation'].append({"role": role, "content": content})
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
