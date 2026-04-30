"""
evals/graph/nodes.py
--------------------
LangGraph node functions for Stage 1.

Design rules (STRICT)
~~~~~~~~~~~~~~~~~~~~~
* Each node receives AgentState, mutates it in-place, and returns it.
* Nodes ONLY wrap existing functionality — they add NO new logic.
* generator_node  → delegates entirely to runner.run()
* executor_node   → delegates entirely to db_utils.execute_sql()
* Both nodes catch ALL exceptions so the graph never crashes the
  outer evaluation loop.  Errors are stored in state, not raised.
"""

from __future__ import annotations

import time
import traceback
from typing import Any, Callable

from evals.graph.state import AgentState


# ─────────────────────────────────────────────────────────────────────────────
# generator_node
# ─────────────────────────────────────────────────────────────────────────────

def make_generator_node(runner: Any) -> Callable[[AgentState], AgentState]:
    """
    Factory that closes over a runner instance and returns a LangGraph-
    compatible node function.

    Using a factory (rather than a class) keeps the node signature the
    simple `state → state` form that LangGraph expects, while still
    letting us inject different runner types at graph-build time.

    Parameters
    ----------
    runner : any existing runner (GeminiRunner, GroqRunner, …)
             Must expose a `.run(query: str) -> dict` method.

    Returns
    -------
    Callable[[AgentState], AgentState]
    """

    def generator_node(state: AgentState) -> AgentState:
        agent_name = "generator"
        t0 = time.perf_counter()

        try:
            # ── delegate entirely to the existing runner ──────────
            raw_response: dict = runner.run(state.query)

            sql = raw_response.get("sql")
            latency = time.perf_counter() - t0

            # ── mutate state ──────────────────────────────────────
            state.sql = sql
            # Preserve any extra keys the runner returned so that
            # executor_node or future nodes can inspect them.
            state._runner_response = raw_response  # type: ignore[attr-defined]

            state.append_step(
                agent_name=agent_name,
                success=True,
                output={"sql": sql},
                latency=latency,
            )

        except Exception as exc:  # noqa: BLE001
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

    # Attach a readable name for LangGraph's internal graph representation
    generator_node.__name__ = "generator_node"
    return generator_node


# ─────────────────────────────────────────────────────────────────────────────
# executor_node
# ─────────────────────────────────────────────────────────────────────────────

def make_executor_node() -> Callable[[AgentState], AgentState]:
    """
    Returns a LangGraph-compatible executor node that calls the existing
    db_utils.execute_sql() function.

    The import is deferred to inside the factory so that environments
    without a live DB (e.g. CI without credentials) can still import
    this module without crashing.
    """

    def executor_node(state: AgentState) -> AgentState:
        agent_name = "executor"
        t0 = time.perf_counter()

        # ── skip if upstream generator already failed ─────────────
        if state.sql is None:
            latency = time.perf_counter() - t0
            state.append_step(
                agent_name=agent_name,
                success=False,
                error="Skipped: no SQL produced by generator",
                latency=latency,
            )
            return state

        try:
            # ── import existing utility (NOT new logic) ───────────
            from evals.metrics.db_utils import execute_sql  # type: ignore[import]

            result = execute_sql(state.sql)
            latency = time.perf_counter() - t0

            state.execution_result = result
            state.append_step(
                agent_name=agent_name,
                success=True,
                output=result,
                latency=latency,
            )

        # except ImportError:
        #     # db_utils not available in this environment — record the
        #     # skip cleanly so metrics are not affected.
        #     latency = time.perf_counter() - t0
        #     state.append_step(
        #         agent_name=agent_name,
        #         success=False,
        #         error="db_utils not available in this environment (ImportError)",
        #         latency=latency,
        #     )

        except Exception as exc:  # noqa: BLE001
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

    executor_node.__name__ = "executor_node"
    return executor_node