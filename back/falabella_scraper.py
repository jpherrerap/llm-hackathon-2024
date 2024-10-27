import re
from typing import List, Tuple
from urllib.parse import urljoin
import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString
from langchain.agents import AgentType, initialize_agent, create_react_agent
from langchain.chat_models import ChatOpenAI
from langchain_mistralai import ChatMistralAI



from langchain.schema import HumanMessage, SystemMessage
from langchain.tools import Tool
from langchain_core.tools import tool

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
from typing import Annotated, List


import os

load_dotenv()
# TODO: Convertir a scraper generico a partir url base
# TODO: Añadir funcionalidades de OpenAI Swarm o implementacion con Mistral
# TODO: Arreglar warnings de LangChain en _s xd

class FAQScraper:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.visited_urls = set()
        self.results = []

        # Initialize LangChain agent
        self.model = model
        self.llm = ChatMistralAI(temperature=0, model=self.model)

    def scrape(self, start_url: str, max_depth: int = 2) -> List[dict]:
        self._scrape_recursive(start_url, max_depth)
        return self.results
    
    def scrape_page(self, url: str) -> List[dict]:
        self._scrape_recursive(url, max_depth=0)
        return self.results
    
    def _extract_relevant_text(self, text_content: str, topic: str) -> str:
        relevant_text = self.llm.invoke(f"Extrae del siguiente texto el contenido relacionado con el tema específico '{topic}', solamente entrega el contenido relevante  \n\n{text_content}").content
        return relevant_text
    

    def _scrape_recursive(self, url: str, max_depth: int = 2, current_depth: int = 0):
        if url in self.visited_urls:
            return

        self.visited_urls.add(url)
        print(f"Scraping URL: {url}")
        response = requests.get(url, timeout=10)  # Add a 30-second timeout
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract text content
        text_content = soup.get_text(separator='\n', strip=True)
        topic = text_content.split('\n')[0].split('|')[0].strip()

        # Use LangChain agent to group text
        relevant_text = self.llm.invoke(f"Extrae del siguiente texto el contenido relacionado con el siguiente tema: {topic}, solamente entrega el texto  \n\n{text_content}").content
        question_answer_list = []
        try:
            question_answer_list = self._group_text(relevant_text)
        except Exception:
            try:
                question_answer_list = self._group_text(relevant_text)
            except Exception as e:
                print(f"Error grouping text from url {url}: {e}")
        
        for qa in question_answer_list:
            qa["category"] = topic
        
        self.results.extend(question_answer_list)

        # Find and follow links
        if current_depth >= max_depth:
            return
        
        for link in soup.find_all('a', href=True):
            href = link['href'].split('?')[0]
            full_url = urljoin(url, href)
            if full_url.startswith(self.base_url) and full_url not in self.visited_urls:
                self._scrape_recursive(full_url, current_depth + 1, max_depth)

    def to_json(self, filename: str) -> None:
        db_knowledge = json.loads(Path(filename).read_text())
        db_knowledge["faq"].extend(self.results)
        Path(filename).write_text(json.dumps(db_knowledge, indent=2, ensure_ascii=False))


    # @tool("Agrupar texto en formato pregunta-respuesta")
    def _group_text(self, text: str) -> List[dict]:
        """
        Agrupa texto en una lista de objetos JSON con formato question-answer
        """
        llm = ChatMistralAI(temperature=0.1, model=self.model)
        prompt = ChatPromptTemplate.from_messages([("system", "Del siguiente texto, para cada punto escribe una pregunta respondida por el texto. Luego entrega una lista de objetos JSON con atributos 'question' y 'answer'. Donde 'question' es la pregunta y 'answer' es la respuesta tomada tal como aparece en el texto. A continuación, el texto (recuerda responder con un fragmento de código markdown de un blob json con una única acción, y NADA más): \n\n {text}")])
        chain = prompt | llm
        grouped_text = chain.invoke({"text": text})
        parsed_qas = "".join(grouped_text.content.split('\n')[1:-1])
        question_answer_list = json.loads(parsed_qas)
        return question_answer_list


def main():
    start_url = "https://www.falabella.com/falabella-cl/page/contactanos"

    scraper = FAQScraper(
        base_url="https://www.falabella.com/falabella-cl/page/",
        model="mistral-large-latest")

    scraper.scrape(start_url, max_depth=2)
    scraper.to_json("../db_knowledge.json")

if __name__ == "__main__":
    main()
