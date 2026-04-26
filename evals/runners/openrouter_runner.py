import requests
import time
from utils.logger import get_logger

logger = get_logger()


class OpenRouterRunner:
    """
    Runner for OpenRouter API
    """

    def __init__(self, api_key: str, model_name: str = "openrouter/auto"):
        self.api_key = api_key
        self.model_name = model_name
        self.url = "https://openrouter.ai/api/v1/chat/completions"

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
                    {"role": "system", "content": "You are an expert SQL generator."},
                    {"role": "user", "content": self.build_prompt(query)}
                ],
                "temperature": 0
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost",
                "X-Title": "agent-eval-framework"
            }

            with requests.Session() as session:
                response = session.post(
                    self.url,
                    json=payload,
                    headers=headers,
                    # FIX: Increased read timeout from 10s → 60s
                    # openrouter/auto routes to slower models that need more time
                    # (5, 10) was causing mid-request SSL crash on slow responses
                    timeout=(10, 60)  # (connect_timeout, read_timeout)
                )
                response.raise_for_status()

            data = response.json()
            raw_output = data["choices"][0]["message"]["content"].strip()

            # Clean SQL output — strip markdown code fences if present
            sql_output = raw_output
            if "```" in sql_output:
                sql_output = sql_output.split("```")[1]
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

        # FIX: Catch timeout separately before generic Exception
        # Previously both fell into the same except block — now we get clear error types
        except requests.exceptions.Timeout:
            logger.error("OpenRouter timeout — read took longer than 60s, check model or network")
            return {
                "query": query,
                "sql": None,
                "answer": None,
                "steps": [],
                "total_latency": None,
                "error": "timeout"
            }

        # FIX: Added explicit ConnectionError catch for network-level failures
        except requests.exceptions.ConnectionError as e:
            logger.error(f"OpenRouter connection error: {e}")
            return {
                "query": query,
                "sql": None,
                "answer": None,
                "steps": [],
                "total_latency": None,
                "error": "connection_error"
            }

        except Exception as e:
            logger.error(f"OpenRouter failed: {e}")
            return {
                "query": query,
                "sql": None,
                "answer": None,
                "steps": [],
                "total_latency": None,
                "error": str(e)
            }