"""
evals/graph/state.py
--------------------
Defines the shared state object passed between every node in the
LangGraph pipeline.

Design notes
~~~~~~~~~~~~
* Plain dataclass — no LangGraph-specific base class required for
  Stage 1.  LangGraph accepts any dict-serialisable object when you
  pass it through graph.invoke().
* `steps` accumulates a structured audit trail of every node that
  ran.  This is the primary observability primitive for Stage 1.
* All fields except `query` are Optional so the graph can be invoked
  with just the query and let each node fill in its own outputs.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Step record — one entry appended per node execution
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StepRecord:
    """Immutable record of a single node's execution."""
    agent_name: str
    success: bool
    output: Any = None          # the primary output produced by the node
    error: Optional[str] = None # stringified exception if success=False
    latency: float = 0.0        # wall-clock seconds for this node


# ─────────────────────────────────────────────────────────────────────────────
# Main state
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AgentState:
    """
    Shared mutable state threaded through every LangGraph node.

    Fields
    ------
    query            : the natural-language question being evaluated
    schema           : optional DB schema injected by a future extractor node
    plan             : optional reasoning plan (future planner node)
    sql              : SQL string produced by the generator node
    execution_result : raw rows / result from the executor node
    error            : last unrecovered error message (any node)
    steps            : ordered list of StepRecord — full execution trace
    model            : name tag of the runner that produced `sql`
    latency          : total end-to-end latency across all nodes (seconds)
    """

    # ── required ──────────────────────────────────────────────────
    query: str

    # ── optional pipeline slots ───────────────────────────────────
    schema: Optional[Any] = None
    plan: Optional[str] = None
    sql: Optional[str] = None
    execution_result: Optional[Any] = None
    error: Optional[str] = None

    # ── observability ─────────────────────────────────────────────
    steps: list[StepRecord] = field(default_factory=list)
    model: Optional[str] = None
    latency: float = 0.0

    # ── internal helpers ──────────────────────────────────────────

    def append_step(
        self,
        agent_name: str,
        success: bool,
        output: Any = None,
        error: Optional[str] = None,
        latency: float = 0.0,
    ) -> None:
        """Convenience method so nodes never construct StepRecord manually."""
        self.steps.append(
            StepRecord(
                agent_name=agent_name,
                success=success,
                output=output,
                error=error,
                latency=latency,
            )
        )

    def to_response_dict(self) -> dict:
        """
        Convert state back into the flat dict that the existing
        evaluation loop expects.

        Keys match what runner.run() historically returned so that
        evaluate_sql / evaluate_agent / evaluate_performance receive
        identical inputs.
        """
        return {
            "sql": self.sql,
            "execution_result": self.execution_result,
            "error": self.error,
            # 'steps' is NEW — downstream metrics ignore unknown keys,
            # so adding it here is backward-safe.
            "steps": [vars(s) for s in self.steps],
        }