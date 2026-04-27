import requests
import time
from utils.logger import get_logger

logger = get_logger()


class GroqRunner:
    """
    Runner for Groq API (OpenAI-compatible)
    """

    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model_name = model_name
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def build_prompt(self, query: str) -> str:
        return f"""
You are an expert SQL generator.

DATABASE SCHEMA:
- Table: singer (id, name, country, birthday)

Rules:
- Use ONLY given schema
- Return ONLY SQL
- No explanation

Query:
{query}
"""

    def run(self, query: str) -> dict:
        start_time = time.time()

        try:
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": self.build_prompt(query)
                    }
                ],
                "temperature": 0,
                "max_tokens": 200
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                self.url,
                json=payload,
                headers=headers,
                timeout=(10, 30)
            )
            response.raise_for_status()

            data = response.json()
            raw_output = data["choices"][0]["message"]["content"]

            # Clean SQL — strip leading text, keep only from SELECT onward
            sql_output = raw_output.strip()
            if "select" in sql_output.lower():
                sql_output = sql_output[sql_output.lower().find("select"):]

            # FIX: keep only the first SQL statement
            # Groq sometimes returns "SELECT COUNT(*) FROM singer;\n```" or
            # multiple statements separated by ";"
            # SQLite raises "You can only execute one statement at a time"
            # Splitting on ";" and taking parts[0] gives the clean statement only
            sql_output = sql_output.split(";")[0].strip()

            latency = round(time.time() - start_time, 2)

            return {
                "query": query,
                "sql": sql_output,
                "answer": None,
                "steps": [{"tool": "llm", "status": "success", "latency": latency}],
                "total_latency": latency,
                "error": None
            }

        except requests.exceptions.Timeout:
            logger.error("Groq timeout — request took longer than 30s")
            return {
                "query": query,
                "sql": None,
                "answer": None,
                "steps": [],
                "total_latency": None,
                "error": "timeout"
            }

        except requests.exceptions.HTTPError as e:
            logger.error(f"Groq HTTP error: {e} | Response: {e.response.text}")
            return {
                "query": query,
                "sql": None,
                "answer": None,
                "steps": [],
                "total_latency": None,
                "error": str(e)
            }

        except Exception as e:
            logger.error(f"Groq failed: {e}")
            return {
                "query": query,
                "sql": None,
                "answer": None,
                "steps": [],
                "total_latency": None,
                "error": str(e)
            }