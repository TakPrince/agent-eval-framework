# evals/runners/agent_runner.py

import requests
import time
from utils.logger import get_logger

logger = get_logger()


class AgentRunner:
    """
    AgentRunner is responsible for:
    - Sending queries to agent API
    - Handling retries on failure
    - Validating responses
    - Returning clean structured output
    """

    def __init__(self, base_url: str, max_retries: int = 3, timeout: int = 5):
        self.base_url = base_url
        self.max_retries = max_retries
        self.timeout = timeout

    def run(self, query: str) -> dict:
        """
        Execute a query against the agent with retry logic.
        """
        attempt = 0

        while attempt < self.max_retries:
            try:
                response = requests.post(
                    f"{self.base_url}/query",
                    json={"query": query},
                    timeout=self.timeout
                )

                response.raise_for_status()
                data = response.json()

                # ✅ Validate response structure
                if not self.validate_response(data):
                    raise ValueError("Invalid response format")

                logger.info(f"Query executed successfully: {query}")
                return data

            except Exception as e:
                attempt += 1
                logger.warning(f"Attempt {attempt} failed for query: {query} | Error: {e}")

                # small delay before retry
                time.sleep(1)

        # ❌ If all retries fail
        logger.error(f"All retries failed for query: {query}")

        return {
            "query": query,
            "sql": None,
            "answer": None,
            "steps": [],
            "total_latency": None,
            "error": "Agent request failed after retries"
        }

    def validate_response(self, data: dict) -> bool:
        """
        Ensures the agent response contains required fields.
        """
        required_keys = ["query", "sql", "steps", "total_latency"]

        for key in required_keys:
            if key not in data:
                logger.error(f"Missing key in response: {key}")
                return False

        # steps should be list
        if not isinstance(data.get("steps"), list):
            logger.error("Invalid steps format")
            return False

        return True