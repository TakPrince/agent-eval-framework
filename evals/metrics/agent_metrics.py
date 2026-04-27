# evals/metrics/agent_metrics.py
from utils.logger import get_logger

logger = get_logger()


def extract_tools(steps: list) -> list:
    """
    Extract tool names from steps.
    Works for both single-agent (tool: "llm") and
    multi-agent (tool: "groq", "openrouter", etc.)
    """
    if not steps:
        return []
    return [step.get("tool") for step in steps if "tool" in step]


def tool_accuracy(predicted_tools: list, expected_tools: list) -> float:
    """
    Compare predicted tools with expected tools.
    """
    if not expected_tools:
        return 0.0
    correct = len(set(predicted_tools) & set(expected_tools))
    return correct / len(expected_tools)


def step_efficiency(steps: list, expected_steps: int = None) -> float:
    """
    Evaluate how efficient the agent is.
    Fewer steps (close to expected) = better.
    """
    if not steps:
        return 0.0
    actual_steps = len(steps)
    if expected_steps:
        return expected_steps / actual_steps if actual_steps else 0.0
    return 1 / actual_steps


def failure_rate(steps: list) -> float:
    """
    Calculate how many steps failed.
    """
    if not steps:
        return 1.0
    failures = sum(1 for step in steps if step.get("status") == "failure")
    return failures / len(steps)


def is_multi_agent(steps: list) -> bool:
    """
    Detect if this response came from a multi-agent runner.
    Multi-agent steps have an "agent" key (planner, generator).
    Single-agent steps only have "tool" key.
    """
    if not steps:
        return False
    return any("agent" in step for step in steps)


def evaluate_agent(response: dict, test_case: dict = None) -> dict:
    """
    Agent evaluation — handles both single-LLM and multi-agent runners.

    Single-agent: 1 step expected → efficiency=1.0 for 1 step
    Multi-agent:  2 steps expected → efficiency scored per-agent success rate,
                  NOT penalized for having more than 1 step
    """
    try:
        steps = response.get("steps", [])
        error = response.get("error")

        # --------------------------------------------------
        # MULTI-AGENT PATH
        # Steps have "agent" key: planner, generator etc.
        # --------------------------------------------------
        if is_multi_agent(steps):

            # Tool usage — did all expected agents run?
            tool_score = 1.0 if steps else 0.0

            # FIX: Efficiency for multi-agent = ratio of successful agent steps
            # Old logic (len(steps)==1 → 1.0, else 0.5) always penalized multi-agent
            # New logic: count how many agents succeeded vs total agents that ran
            total_agents = len(steps)
            successful_agents = sum(
                1 for step in steps if step.get("status") == "success"
            )
            efficiency_score = successful_agents / total_agents if total_agents else 0.0

            # Per-agent latency breakdown for Shivam's benchmarking report
            agent_latencies = {
                step.get("agent", f"step_{i}"): step.get("latency")
                for i, step in enumerate(steps)
            }

            # Failure — pipeline error OR any individual agent failed
            fail_rate = 1.0 if error else (
                1.0 if any(s.get("status") == "failed" for s in steps) else 0.0
            )

            final_score = (
                (tool_score * 0.3) +
                (efficiency_score * 0.3) +
                ((1 - fail_rate) * 0.4)
            )

            return {
                "mode": "multi_agent",
                "agents_run": total_agents,
                "agents_succeeded": successful_agents,
                "agent_latencies": agent_latencies,
                "tool_accuracy": tool_score,
                "efficiency": round(efficiency_score, 4),
                "failure_rate": fail_rate,
                "score": round(final_score, 4)
            }

        # --------------------------------------------------
        # SINGLE-AGENT PATH (original logic — unchanged)
        # Steps have only "tool" key: "llm"
        # --------------------------------------------------
        else:

            tool_score = 1.0 if steps else 0.0

            if not steps:
                efficiency_score = 0.0
            else:
                # single LLM should complete in exactly 1 step
                efficiency_score = 1.0 if len(steps) == 1 else 0.5

            fail_rate = 1.0 if error else 0.0

            final_score = (
                (tool_score * 0.3) +
                (efficiency_score * 0.3) +
                ((1 - fail_rate) * 0.4)
            )

            return {
                "mode": "single_agent",
                "tool_accuracy": tool_score,
                "efficiency": efficiency_score,
                "failure_rate": fail_rate,
                "score": round(final_score, 4)
            }

    except Exception as e:
        logger.error(f"Agent evaluation failed: {e}")
        return {
            "tool_accuracy": 0,
            "efficiency": 0,
            "failure_rate": 1,
            "score": 0
        }