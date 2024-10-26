import re
from typing import List, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from langchain.agents import AgentType, initialize_agent
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.tools import Tool
from dotenv import load_dotenv
import os

load_dotenv()

# TODO: Convertir a scraper generico a partir url base
# TODO: Añadir funcionalidades de OpenAI Swarm o implementacion con Mistral
# TODO: Arreglar warnings de LangChain en _s xd

class FalabellaScraper:
    def __init__(self, openai_api_key: str):
        self.base_url = "https://www.falabella.com/falabella-cl/page/"
        self.visited_urls = set()
        self.results = []

        # Initialize LangChain agent
        llm = ChatOpenAI(temperature=0, model="gpt-4o-mini", openai_api_key=openai_api_key)
        tools = [
            Tool(
                name="Group Text",
                func=self._group_text,
                description="Groups text under appropriate headers",
            )
        ]
        self.agent = initialize_agent(tools, llm, agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

    def scrape(self, start_url: str) -> List[Tuple[str, str]]:
        self._scrape_recursive(start_url)
        return self.results

    def _scrape_recursive(self, url: str):
        if url in self.visited_urls:
            return

        self.visited_urls.add(url)
        response = requests.get(url, timeout=30)  # Add a 30-second timeout
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract text content
        text_content = soup.get_text(separator='\n', strip=True)

        # Use LangChain agent to group text
        grouped_text = self.agent.run(f"Group the following text under appropriate headers:\n\n{text_content}")
        self.results.append((url, grouped_text))

        # Find and follow links
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            if full_url.startswith(self.base_url) and full_url not in self.visited_urls:
                self._scrape_recursive(full_url)

    def _group_text(self, text: str) -> str:
        # This is a placeholder for the actual grouping logic
        # The LangChain agent will use this function to group the text
        return text

def main():
    openai_api_key = os.environ["OPENAI_API_KEY"]
    start_url = "https://www.falabella.com/falabella-cl/page/contactanos"

    scraper = FalabellaScraper(openai_api_key)
    results = scraper.scrape(start_url)

    for url, grouped_text in results:
        print(f"URL: {url}")
        print("Grouped Text:")
        print(grouped_text)
        print("-" * 50)

if __name__ == "__main__":
    main()
