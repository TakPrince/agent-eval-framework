import time
from utils.logger import get_logger

logger = get_logger()


class MultiAgentRunner:
    """
    Multi-agent runner:
    - Agent 1 (Planner)   → Groq      → analyzes query, identifies schema elements needed
    - Agent 2 (Generator) → OpenRouter → takes planner output, generates final SQL

    Both runners are passed in from run_eval.py — no new API logic here,
    reuses GroqRunner and OpenRouterRunner exactly as-is.
    """

    def __init__(self, planner, generator):
        # planner   → GroqRunner instance
        # generator → OpenRouterRunner instance
        self.planner = planner
        self.generator = generator

    def build_planner_prompt(self, query: str) -> str:
        """
        Planner prompt — Groq analyzes the NL query and returns a structured plan.
        Does NOT generate SQL. Only identifies what is needed.
        """
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
        """
        Generator prompt — OpenRouter takes the planner's analysis and writes SQL.
        """
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

    def run(self, query: str) -> dict:
        total_start = time.time()
        steps = []

        # --------------------------------------------------
        # AGENT 1: Planner (Groq)
        # Temporarily swaps build_prompt to use planner prompt,
        # then restores it — reuses all GroqRunner HTTP/auth logic unchanged
        # --------------------------------------------------
        try:
            planner_start = time.time()

            original_build = self.planner.build_prompt
            self.planner.build_prompt = self.build_planner_prompt
            planner_response = self.planner.run(query)
            self.planner.build_prompt = original_build  # always restore

            planner_latency = round(time.time() - planner_start, 2)

            if planner_response.get("error"):
                # Planner failed — no point calling generator without a plan
                logger.error(f"Planner agent failed: {planner_response['error']}")
                steps.append({
                    "agent": "planner", "tool": "groq",
                    "status": "failed", "latency": planner_latency
                })
                return {
                    "query": query,
                    "sql": None,
                    "answer": None,
                    "steps": steps,
                    "total_latency": round(time.time() - total_start, 2),
                    "error": f"planner failed: {planner_response['error']}"
                }

            # Planner output comes back in "sql" field (runner structure reuse)
            # but here it contains the plan text, not actual SQL
            plan = planner_response.get("sql") or ""
            steps.append({
                "agent": "planner", "tool": "groq",
                "status": "success", "latency": planner_latency,
                "output": plan
            })
            logger.info(f"Planner output:\n{plan}")

        except Exception as e:
            logger.error(f"Planner agent exception: {e}")
            return {
                "query": query,
                "sql": None,
                "answer": None,
                "steps": steps,
                "total_latency": round(time.time() - total_start, 2),
                "error": str(e)
            }

        # --------------------------------------------------
        # AGENT 2: Generator (OpenRouter)
        # Injects planner's plan into the generator prompt,
        # then restores original build_prompt — reuses all OpenRouterRunner logic
        # --------------------------------------------------
        try:
            generator_start = time.time()

            def generator_prompt_with_plan(q: str) -> str:
                return self.build_generator_prompt(q, plan)

            original_gen_build = self.generator.build_prompt
            self.generator.build_prompt = generator_prompt_with_plan
            generator_response = self.generator.run(query)
            self.generator.build_prompt = original_gen_build  # always restore

            generator_latency = round(time.time() - generator_start, 2)

            if generator_response.get("error"):
                logger.error(f"Generator agent failed: {generator_response['error']}")
                steps.append({
                    "agent": "generator", "tool": "openrouter",
                    "status": "failed", "latency": generator_latency
                })
                return {
                    "query": query,
                    "sql": None,
                    "answer": None,
                    "steps": steps,
                    "total_latency": round(time.time() - total_start, 2),
                    "error": f"generator failed: {generator_response['error']}"
                }

            sql_output = generator_response.get("sql")
            steps.append({
                "agent": "generator", "tool": "openrouter",
                "status": "success", "latency": generator_latency,
                "output": sql_output
            })

        except Exception as e:
            logger.error(f"Generator agent exception: {e}")
            return {
                "query": query,
                "sql": None,
                "answer": None,
                "steps": steps,
                "total_latency": round(time.time() - total_start, 2),
                "error": str(e)
            }

        return {
            "query": query,
            "sql": sql_output,
            "answer": None,
            "steps": steps,
            "total_latency": round(time.time() - total_start, 2),
            "error": None
        }