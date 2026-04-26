import requests
import time
from utils.logger import get_logger

logger = get_logger()


class GroqRunner:
    """
    Runner for Groq API (OpenAI-compatible)
    """

    def __init__(self, api_key: str, model_name: str = "llama3-70b-8192"):
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
                        # FIX: was `"content": [self.build_prompt(query)]` (a list)
                        # Groq API requires content to be a plain string, not a list
                        # A list triggers 400 Bad Request every time
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

            # FIX: Added timeout=(10, 30) — without it, a hung request blocks forever
            # Groq is fast, so 30s read timeout is more than enough
            response = requests.post(
                self.url,
                json=payload,
                headers=headers,
                timeout=(10, 30)  # (connect_timeout, read_timeout)
            )
            response.raise_for_status()

            data = response.json()
            raw_output = data["choices"][0]["message"]["content"]

            # Clean SQL — strip leading text, keep only from SELECT onward
            sql_output = raw_output.strip()
            if "select" in sql_output.lower():
                sql_output = sql_output[sql_output.lower().find("select"):]
            sql_output = sql_output.strip()

            latency = round(time.time() - start_time, 2)

            return {
                "query": query,
                "sql": sql_output,
                "answer": None,
                "steps": [{"tool": "llm", "status": "success", "latency": latency}],
                "total_latency": latency,
                "error": None
            }

        # FIX: Split into specific except blocks for clearer error diagnosis
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
            # Logs the full HTTP error body so you can see exactly what Groq rejected
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