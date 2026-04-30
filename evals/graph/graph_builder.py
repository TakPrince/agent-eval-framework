"""
evals/graph/graph_builder.py
----------------------------
Assembles the Stage 1 LangGraph pipeline.

Topology (Stage 1 — fixed, no branching):
    START → generator → executor → END

Design notes
~~~~~~~~~~~~
* build_graph() accepts a runner and returns a compiled graph.
  The runner is injected so the same builder works for every runner
  type (Gemini, Groq, Ollama, Multi-Agent, …).
* StateGraph is typed with AgentState.  LangGraph will call each node
  with the state object and thread the return value to the next node.
* The compiled graph exposes .invoke(state) which is the only surface
  used by run_eval.py — identical interface regardless of how many
  nodes are wired inside.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph, START, END  # type: ignore[import]

from evals.graph.state import AgentState
from evals.graph.nodes import make_generator_node, make_executor_node


def build_graph(runner: Any):
    """
    Build and compile the Stage 1 LangGraph pipeline.

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
    generator = make_generator_node(runner)
    executor  = make_executor_node()

    # ── wire the graph ────────────────────────────────────────────
    # StateGraph is generic over the state type so LangGraph knows
    # how to route data between nodes.
    graph = StateGraph(AgentState)

    graph.add_node("generator", generator)
    graph.add_node("executor",  executor)

    # Linear topology — Stage 1 has no branching or loops
    graph.add_edge(START,       "generator")
    graph.add_edge("generator", "executor")
    graph.add_edge("executor",  END)

    # compile() validates the graph structure and returns an object
    # whose .invoke() / .stream() methods are the public API.
    compiled = graph.compile()

    return compiled 