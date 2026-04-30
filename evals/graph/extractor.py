"""
evals/graph/extractor.py
------------------------
Phase 2: Rule-based schema extractor node.

Design rules
~~~~~~~~~~~~
* Pure rule-based logic — no LLM, no embeddings, no external calls
* Accepts AgentState, populates state.schema, returns AgentState
* Never crashes — all exceptions captured into state.steps
* Generator and executor are completely unaware of this node's existence
* schema is optional downstream — if unused, behaviour is identical to Stage 1
"""

from __future__ import annotations

import time
from typing import Callable

from evals.graph.state import AgentState


# ─────────────────────────────────────────────────────────────────────────────
# Rule tables
# ─────────────────────────────────────────────────────────────────────────────

# Each entry: (keyword_to_match, schema_key, value_to_add)
# All matching is case-insensitive on the lowercased query.

_TABLE_RULES: list[tuple[str, str]] = [
    ("singer", "singer"),
]

_COLUMN_RULES: list[tuple[str, str]] = [
    ("name",     "name"),
    ("country",  "country"),
    ("count",    "id"),      # "how many" / "count" both need id
    ("how many", "id"),
    ("birthday", "birthday"),
    ("average",  "id"),      # aggregate queries typically operate on id
    ("minimum",  "id"),
    ("maximum",  "id"),
]


def _extract_schema(query: str) -> dict:
    """
    Apply keyword rules to derive a minimal schema hint from the query.

    Returns
    -------
    dict with keys:
        "tables"  : list[str] — matched table names (deduplicated)
        "columns" : list[str] — matched column names (deduplicated)
    """
    q = query.lower()

    tables  = list(dict.fromkeys(val for kw, val in _TABLE_RULES  if kw in q))
    columns = list(dict.fromkeys(val for kw, val in _COLUMN_RULES if kw in q))

    return {"tables": tables, "columns": columns}


# ─────────────────────────────────────────────────────────────────────────────
# Node factory
# ─────────────────────────────────────────────────────────────────────────────

def make_extractor_node() -> Callable[[AgentState], AgentState]:
    """
    Returns a LangGraph-compatible extractor node function.

    The factory pattern is consistent with make_generator_node /
    make_executor_node so all nodes share the same construction style.
    """

    def extractor_node(state: AgentState) -> AgentState:
        agent_name = "extractor"
        t0 = time.perf_counter()

        try:
            schema  = _extract_schema(state.query)
            latency = time.perf_counter() - t0

            # Populate state — generator can optionally inspect this
            state.schema = schema

            state.append_step(
                agent_name=agent_name,
                success=True,
                output=schema,
                latency=latency,
            )

        except Exception as exc:          # noqa: BLE001
            latency = time.perf_counter() - t0
            err_msg = f"{type(exc).__name__}: {exc}"

            # Leave state.schema as None — generator still runs normally
            state.append_step(
                agent_name=agent_name,
                success=False,
                error=err_msg,
                latency=latency,
            )

        return state

    extractor_node.__name__ = "extractor_node"
    return extractor_node