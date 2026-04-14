# evals/metrics/agent_metrics.py

from utils.logger import get_logger

logger = get_logger()


def extract_tools(steps: list) -> list:
    """
    Extract tool names from steps.
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
    Fewer steps (close to expected) = better
    """
    if not steps:
        return 0.0

    actual_steps = len(steps)

    if expected_steps:
        return expected_steps / actual_steps if actual_steps else 0.0

    # fallback: fewer steps = better
    return 1 / actual_steps


def failure_rate(steps: list) -> float:
    """
    Calculate how many steps failed.
    """
    if not steps:
        return 1.0

    failures = sum(1 for step in steps if step.get("status") == "failure")
    return failures / len(steps)


def evaluate_agent(response: dict, test_case: dict = None) -> dict:
    """
    Main agent evaluation function
    """
    try:
        steps = response.get("steps", [])

        predicted_tools = extract_tools(steps)

        expected_tools = []
        expected_steps = None

        # optional (if multi_agent.json used later)
        if test_case:
            expected_tools = test_case.get("expected_tools", [])
            expected_steps = test_case.get("expected_steps")

        tool_score = tool_accuracy(predicted_tools, expected_tools)
        efficiency_score = step_efficiency(steps, expected_steps)
        fail_rate = failure_rate(steps)

        # final score (simple weighted)
        final_score = (
            (tool_score * 0.4) +
            (efficiency_score * 0.3) +
            ((1 - fail_rate) * 0.3)
        )

        return {
            "tool_accuracy": tool_score,
            "efficiency": efficiency_score,
            "failure_rate": fail_rate,
            "score": final_score
        }

    except Exception as e:
        logger.error(f"Agent evaluation failed: {e}")
        return {
            "tool_accuracy": 0,
            "efficiency": 0,
            "failure_rate": 1,
            "score": 0
        }