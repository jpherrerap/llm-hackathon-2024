import os
import json
from pathlib import Path
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

### Ingest code - you may need to run this the first time

# Load output from gpt crawler
path_to_json = Path(__file__).parent.parent / "db_knowledge.json"
data = json.loads(Path(path_to_json).read_text())
data = data["faq"]
docs = [
    Document(
        page_content=dict_["question"],
        metadata={"answer": dict_["answer"]},
    )
    for dict_ in data
]

embedding_model = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))

# Split
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1800, chunk_overlap=100)
all_splits = text_splitter.split_documents(docs)


vectorstore = Chroma.from_documents(
    documents=docs,
    collection_name="rag-faq",
    embedding=embedding_model
)

print("DB Done!")
retriever = vectorstore.as_retriever(search_kwargs={"5": 10})