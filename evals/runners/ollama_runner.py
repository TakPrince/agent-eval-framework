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
        Improved Prompt for NL → SQL (schema-aware)
        """

        return f"""
    You are an expert SQL generator.

You must convert natural language into SQL using the given database schema.

DATABASE SCHEMA:
- Table: singer (id, name, country, birthday)

STRICT RULES:
- Use ONLY the table and columns from schema
- Do NOT invent tables (e.g., singers, countries)
- Do NOT use JOIN unless necessary
- Use correct column names exactly as given
- Return ONLY SQL query
- No explanation, no markdown, no comments

EXAMPLES:
Q: How many singers do we have?
A: SELECT COUNT(*) FROM singer;

Q: Show name and country of all singers
A: SELECT name, country FROM singer;

NOW CONVERT:

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
            raw_output = data.get("response", "").strip()

            # 🔥 Clean unwanted text
            sql_output = raw_output

            # remove markdown if present
            if "```" in sql_output:
                sql_output = sql_output.split("```")[1]

            # remove leading text like "Here is SQL:"
            if "select" in sql_output.lower():
                sql_output = sql_output[sql_output.lower().find("select"):]

            sql_output = sql_output.strip()

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