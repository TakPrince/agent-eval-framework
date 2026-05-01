import time
from utils.logger import get_logger

logger = get_logger()


class MultiAgentRunner:
    """
    Multi-agent runner:
    - Agent 1 (Planner)   → Groq
    - Agent 2 (Generator) → OpenRouter

    Updated:
    - Step format aligned with graph system (agent_name, success)
    - Model info added for proper multi-agent detection
    - Backward compatible (no breaking changes)
    """

    def __init__(self, planner, generator):
        self.planner = planner
        self.generator = generator

    # ─────────────────────────────────────────────────────────────
    # PROMPTS
    # ─────────────────────────────────────────────────────────────

    def build_planner_prompt(self, query: str) -> str:
        return f"""
You are a SQL query planner.

DATABASE SCHEMA:
- Table: singer (id, name, country, birthday)

Your job is to analyze the user query and produce a short plan:
- Which table(s) are needed
- Which column(s) are needed
- Any filters, ordering, or aggregation required
- Do NOT write SQL

Query:
{query}

Respond in this format:
Tables: <tables>
Columns: <columns>
Filters: <filters or None>
Ordering: <ordering or None>
Aggregation: <aggregation or None>
"""

    def build_generator_prompt(self, query: str, plan: str) -> str:
        return f"""
You are an expert SQL generator.

DATABASE SCHEMA:
- Table: singer (id, name, country, birthday)

A query planner has already analyzed the user query and produced this plan:
{plan}

Original Query:
{query}

Rules:
- Use ONLY the given schema
- Return ONLY SQL
- No explanation

SQL:
"""

    # ─────────────────────────────────────────────────────────────
    # MAIN EXECUTION
    # ─────────────────────────────────────────────────────────────

    def run(self, query: str) -> dict:
        total_start = time.time()
        steps = []

        # ==========================================================
        # AGENT 1: PLANNER (Groq)
        # ==========================================================
        try:
            planner_start = time.time()

            original_build = self.planner.build_prompt
            self.planner.build_prompt = self.build_planner_prompt

            planner_response = self.planner.run(query)

            # restore
            self.planner.build_prompt = original_build

            planner_latency = round(time.time() - planner_start, 4)

            if planner_response.get("error"):
                logger.error(f"Planner failed: {planner_response['error']}")

                steps.append({
                    "agent_name": "planner",
                    "success": False,
                    "error": planner_response["error"],
                    "latency": planner_latency,
                    "output": None
                })

                return {
                    "query": query,
                    "sql": None,
                    "steps": steps,
                    "error": f"planner failed: {planner_response['error']}"
                }

            plan = planner_response.get("sql") or ""

            steps.append({
                "agent_name": "planner",
                "success": True,
                "latency": planner_latency,
                "output": {
                    "plan": plan,
                    "model": getattr(self.planner, "model_name", "unknown")  # 🔥 FIX
                }
            })

        except Exception as e:
            logger.error(f"Planner exception: {e}")
            return {
                "query": query,
                "sql": None,
                "steps": steps,
                "error": str(e)
            }

        # ==========================================================
        # AGENT 2: GENERATOR (OpenRouter)
        # ==========================================================
        try:
            generator_start = time.time()

            def generator_prompt_with_plan(q: str) -> str:
                return self.build_generator_prompt(q, plan)

            original_build = self.generator.build_prompt
            self.generator.build_prompt = generator_prompt_with_plan

            generator_response = self.generator.run(query)

            # restore
            self.generator.build_prompt = original_build

            generator_latency = round(time.time() - generator_start, 4)

            if generator_response.get("error"):
                logger.error(f"Generator failed: {generator_response['error']}")

                steps.append({
                    "agent_name": "generator",
                    "success": False,
                    "error": generator_response["error"],
                    "latency": generator_latency,
                    "output": None
                })

                return {
                    "query": query,
                    "sql": None,
                    "steps": steps,
                    "error": f"generator failed: {generator_response['error']}"
                }

            sql_output = generator_response.get("sql")

            steps.append({
                "agent_name": "generator",
                "success": True,
                "latency": generator_latency,
                "output": {
                    "sql": sql_output,
                    "model": getattr(self.generator, "model_name", "unknown")  # 🔥 FIX
                }
            })

        except Exception as e:
            logger.error(f"Generator exception: {e}")
            return {
                "query": query,
                "sql": None,
                "steps": steps,
                "error": str(e)
            }

        # ==========================================================
        # FINAL RESPONSE
        # ==========================================================
        return {
            "query": query,
            "sql": sql_output,
            "steps": steps,
            "error": None
        }