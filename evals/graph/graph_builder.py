"""
evals/graph/graph_builder.py
----------------------------
Assembles the LangGraph pipeline.

Topology (Phase 2):
    START → extractor → generator → executor → END

Changes from Stage 1
~~~~~~~~~~~~~~~~~~~~
+ Imported make_extractor_node
+ extractor node added before generator
+ START now edges to extractor, not generator
! generator → executor → END edges are unchanged
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph, START, END  # type: ignore[import]

from evals.graph.state import AgentState
from evals.graph.nodes import make_generator_node, make_executor_node
from evals.graph.extractor import make_extractor_node          # Phase 2


def build_graph(runner: Any):
    """
    Build and compile the Phase 2 LangGraph pipeline.

    Parameters
    ----------
    runner : one of the existing runner instances
             (GeminiRunner | GroqRunner | OpenRouterRunner |
              OllamaRunner | MultiAgentRunner)

    Returns
    -------
    CompiledGraph
        A LangGraph compiled graph whose .invoke(AgentState) method
        returns the final AgentState after all nodes have run.
    """

    # ── instantiate node functions via factories ──────────────────
    extractor = make_extractor_node()          # Phase 2 — no runner needed
    generator = make_generator_node(runner)
    executor  = make_executor_node()

    # ── wire the graph ────────────────────────────────────────────
    graph = StateGraph(AgentState)

    graph.add_node("extractor", extractor)     # Phase 2
    graph.add_node("generator", generator)
    graph.add_node("executor",  executor)

    # Phase 2 topology: START → extractor → generator → executor → END
    graph.add_edge(START,        "extractor")  # changed from START → generator
    graph.add_edge("extractor",  "generator")  # new edge
    graph.add_edge("generator",  "executor")   # unchanged
    graph.add_edge("executor",   END)          # unchanged

    compiled = graph.compile()
    return compiled