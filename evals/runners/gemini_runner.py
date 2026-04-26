# evals/runners/gemini_runner.py

import time
import google.generativeai as genai
from utils.logger import get_logger

logger = get_logger()


class GeminiRunner:
    """
    Runner for Gemini models (NL → SQL)
    Compatible with existing evaluation pipeline
    """

    def __init__(self, api_key: str, model_name: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def build_prompt(self, query: str) -> str:
        """
        Prompt to convert NL → SQL
        """
        return f"""
You are an expert SQL generator.

Convert the following natural language query into SQL.

Rules:
- Return ONLY SQL query
- No explanation
- Use simple SQL syntax

Query:
{query}
"""

    def run(self, query: str) -> dict:
        """
        Execute query using Gemini model
        Returns same format as dummy agent
        """
        start_time = time.time()

        try:
            prompt = self.build_prompt(query)

            response = self.model.generate_content(prompt)
            sql_output = response.text.strip()

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
            logger.error(f"Gemini API failed: {e}")

            return {
                "query": query,
                "sql": None,
                "answer": None,
                "steps": [],
                "total_latency": None,
                "error": str(e)
            }