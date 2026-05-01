from utils.logger import get_logger

logger = get_logger()


# ─────────────────────────────────────────────────────────────────────────────
# Helper: Extract tools (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
def extract_tools(steps: list) -> list:
    if not steps:
        return []
    return [step.get("tool") for step in steps if "tool" in step]


# ─────────────────────────────────────────────────────────────────────────────
# Helper: Tool accuracy (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
def tool_accuracy(predicted_tools: list, expected_tools: list) -> float:
    if not expected_tools:
        return 0.0
    correct = len(set(predicted_tools) & set(expected_tools))
    return correct / len(expected_tools)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: Efficiency (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
def step_efficiency(steps: list, expected_steps: int = None) -> float:
    if not steps:
        return 0.0
    actual_steps = len(steps)
    if expected_steps:
        return expected_steps / actual_steps if actual_steps else 0.0
    return 1 / actual_steps


# ─────────────────────────────────────────────────────────────────────────────
# Helper: Failure rate (FIXED → uses success field)
# ─────────────────────────────────────────────────────────────────────────────
def failure_rate(steps: list) -> float:
    if not steps:
        return 1.0
    failures = sum(1 for step in steps if step.get("success") is False)
    return failures / len(steps)


# ─────────────────────────────────────────────────────────────────────────────
# 🔥 FIXED: Multi-agent detection (Phase 3+ compatible)
# ─────────────────────────────────────────────────────────────────────────────
def detect_mode(steps: list) -> str:

    if not steps:
        return "single_agent"

    agent_names = set()
    models = set()

    for step in steps:

        if not isinstance(step, dict):
            continue

        name = step.get("agent_name")

        if not name or name == "executor":
            continue

        if name == "retry_generator":
            agent_names.add("generator")
        else:
            agent_names.add(name)

        # SAFE model extraction
        output = step.get("output")
        if isinstance(output, dict):
            model = output.get("model")
            if model:
                models.add(model)

    if len(agent_names) <= 1:
        return "single_agent"

    if len(models) > 1:
        return "multi_agent"

    return "multi_stage"

    # ─────────────
    # LOGIC
    # ─────────────

    # single stage
    if len(agent_names) <= 1:
        return "single_agent"

    # 🔥 KEY: real multi-agent (different models)
    if len(models) > 1:
        return "multi_agent"

    # otherwise pipeline only
    return "multi_stage"

# ─────────────────────────────────────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def evaluate_agent(response: dict, test_case: dict = None) -> dict:
    try:
        steps = response.get("steps", [])
        error = response.get("error")

        # 🔥 NEW: detect mode
        mode = detect_mode(steps)

        # --------------------------------------------------
        # MULTI-STAGE / MULTI-AGENT
        # --------------------------------------------------
        if mode in ["multi_stage", "multi_agent"]:

            tool_score = 1.0 if steps else 0.0

            total_agents = len(steps)
            successful_agents = sum(
                1 for step in steps if step.get("success") is True
            )

            efficiency_score = (
                successful_agents / total_agents if total_agents else 0.0
            )

            agent_latencies = {
                step.get("agent_name", f"step_{i}"): step.get("latency")
                for i, step in enumerate(steps)
            }

            fail_rate = 1.0 if error else (
                1.0 if any(s.get("success") is False for s in steps) else 0.0
            )

            final_score = (
                (tool_score * 0.3) +
                (efficiency_score * 0.3) +
                ((1 - fail_rate) * 0.4)
            )

            return {
                "mode": mode,   # 🔥 IMPORTANT
                "agents_run": total_agents,
                "agents_succeeded": successful_agents,
                "agent_latencies": agent_latencies,
                "tool_accuracy": tool_score,
                "efficiency": round(efficiency_score, 4),
                "failure_rate": fail_rate,
                "score": round(final_score, 4)
            }

        # --------------------------------------------------
        # SINGLE AGENT
        # --------------------------------------------------
        else:

            tool_score = 1.0 if steps else 0.0

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
            "mode": "error",   # 🔥 better debugging
            "tool_accuracy": 0,
            "efficiency": 0,
            "failure_rate": 1,
            "score": 0
        }