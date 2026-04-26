# evals/runners/ollama_runner.py

import requests
import time
from utils.logger import get_logger

logger = get_logger()


class OllamaRunner:
    """
    Runner for local LLMs via Ollama
    Compatible with existing evaluation pipeline
    """

    def __init__(self, model_name: str = "llama3"):
        self.model_name = model_name
        self.url = "http://localhost:11434/api/generate"

    def build_prompt(self, query: str) -> str:
        """
        Prompt for NL → SQL
        """
        return f"""
You are an expert SQL generator.

Convert the following natural language query into SQL.

Rules:
- Return ONLY SQL query
- No explanation
- No markdown
- Use simple SQL syntax

Query:
{query}
"""

    def run(self, query: str) -> dict:
        start_time = time.time()

        try:
            payload = {
                "model": self.model_name,
                "prompt": self.build_prompt(query),
                "stream": False
            }

            response = requests.post(self.url, json=payload)
            response.raise_for_status()

            data = response.json()
            sql_output = data.get("response", "").strip()

            total_latency = round(time.time() - start_time, 2)

            return {
                "query": query,
                "sql": sql_output,
                "answer": None,
                "steps": [
                    {"tool": "llm", "status": "success", "latency": total_latency}
                ],
                "total_latency": total_latency,
                "error": None
            }

        except Exception as e:
            logger.error(f"Ollama API failed: {e}")

            return {
                "query": query,
                "sql": None,
                "answer": None,
                "steps": [],
                "total_latency": None,
                "error": str(e)
            }