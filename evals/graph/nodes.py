"""
evals/graph/nodes.py
--------------------
LangGraph node functions — Phase 3: retry loop added to executor.

Changes from Phase 2
~~~~~~~~~~~~~~~~~~~~
* MAX_RETRIES = 2 constant added
* make_executor_node() now accepts runner for retry regeneration
* executor_node retries up to MAX_RETRIES times on SQL failure:
    1. Log failed execution attempt
    2. Call runner with correction prompt  → log as "retry_generator"
    3. Re-attempt execution               → log as "executor" again
* generator_node and extractor_node are UNCHANGED
* Behaviour for successful queries is identical to Phase 2
"""

from __future__ import annotations

import time
from typing import Any, Callable

from evals.graph.state import AgentState
from evals.metrics.db_utils import execute_sql

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

MAX_RETRIES = 2


# ─────────────────────────────────────────────────────────────────────────────
# generator_node  (UNCHANGED from Phase 2)
# ─────────────────────────────────────────────────────────────────────────────

def make_generator_node(runner: Any) -> Callable[[AgentState], AgentState]:
    """Factory: closes over a runner, returns a LangGraph node function."""

    def generator_node(state: AgentState) -> AgentState:
        agent_name = "generator"
        t0 = time.perf_counter()

        try:
            raw_response: dict = runner.run(state.query)
            sql = raw_response.get("sql")
            latency = time.perf_counter() - t0

            state.sql = sql
            model_name = getattr(runner, "model_name", "unknown")

            state.append_step(
                agent_name=agent_name,
                success=True,
                output={
                    "sql": sql,
                    "model": model_name   # 🔥 CRITICAL FIX
                },
                latency=latency,
            )

        except Exception as exc:
            latency = time.perf_counter() - t0
            err_msg = f"{type(exc).__name__}: {exc}"
            state.error = err_msg
            state.append_step(
                agent_name=agent_name,
                success=False,
                error=err_msg,
                latency=latency,
            )

        return state

    generator_node.__name__ = "generator_node"
    return generator_node


# ─────────────────────────────────────────────────────────────────────────────
# executor_node  (Phase 3 — retry loop)
# ─────────────────────────────────────────────────────────────────────────────

def make_executor_node(runner: Any) -> Callable[[AgentState], AgentState]:
    """
    Factory: closes over runner for retry regeneration.

    Retry flow (triggered only on execution failure):
        executor (fail)
            → retry_generator: runner.run(correction_prompt)
            → executor (retry)
        Repeat up to MAX_RETRIES times, then give up and store error.

    For successful queries the behaviour is identical to Phase 2 —
    the retry branch is never entered.
    """

    def executor_node(state: AgentState) -> AgentState:

        # ── guard: no SQL from generator ─────────────────────────
        if not state.sql:
            t0 = time.perf_counter()
            state.append_step(
                agent_name="executor",
                success=False,
                error="Skipped: generator produced no SQL",
                latency=time.perf_counter() - t0,
            )
            return state

        # ── attempt 0 + up to MAX_RETRIES correction attempts ────
        last_error: str = ""

        for attempt in range(MAX_RETRIES + 1):   # 0 = first try, 1-2 = retries

            # ── execute current state.sql ─────────────────────────
            t0 = time.perf_counter()
            try:
                result  = execute_sql(state.sql)
                latency = time.perf_counter() - t0

                state.execution_result = result
                state.error            = None      # clear any previous error
                state.append_step(
                    agent_name="executor",
                    success=True,
                    output=result,
                    latency=latency,
                )
                return state                       # ✅ success — exit immediately

            except Exception as exc:
                latency    = time.perf_counter() - t0
                last_error = f"{type(exc).__name__}: {exc}"

                state.append_step(
                    agent_name="executor",
                    success=False,
                    error=last_error,
                    latency=latency,
                )

            # ── no retries left after final attempt ───────────────
            if attempt == MAX_RETRIES:
                break

            # ── retry_generator: ask runner to fix the SQL ────────
            correction_prompt = f"""
                                    You are an expert SQL fixer.
                                    The following SQL failed:
                                    {state.sql}
                                    Error:
                                    {last_error}
                                    Fix the SQL and return ONLY the corrected SQL query.
                                    Do not include explanations.
                                    """

            t0 = time.perf_counter()
            try:
                retry_response  = runner.run(correction_prompt)
                corrected_sql   = retry_response.get("sql") or state.sql
                latency         = time.perf_counter() - t0

                state.sql = corrected_sql          # update sql for next attempt
                model_name = getattr(runner, "model_name", "unknown")

                state.append_step(
                    agent_name="retry_generator",
                    success=True,
                    output={
                        "sql": corrected_sql,
                        "attempt": attempt + 1,
                        "model": model_name   # 🔥 IMPORTANT
                    },
                    latency=latency,
                )

            except Exception as rexc:
                latency = time.perf_counter() - t0
                rerr    = f"{type(rexc).__name__}: {rexc}"

                # Runner itself failed — log and stop retrying
                state.error = rerr
                state.append_step(
                    agent_name="retry_generator",
                    success=False,
                    error=rerr,
                    latency=latency,
                )
                break                              # no point retrying further

        # ── all attempts exhausted without success ────────────────
        state.error = last_error
        return state

    executor_node.__name__ = "executor_node"
    return executor_node