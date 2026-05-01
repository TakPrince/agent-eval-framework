from __future__ import annotations


PENALTY_PER_ERROR   = 0.2
PENALTY_PER_RETRY   = 0.1
RECOVERY_BONUS      = 0.2

# 🔥 NEW (minimal additions)
FINAL_FAIL_PENALTY  = 0.5
ERROR_MSG_PENALTY   = 0.2
EXTERNAL_ERR_PENALTY = 0.3


def evaluate_trajectory(steps: list, response: dict = None) -> dict:
    """
    Phase 4.5 upgrade (minimal change)

    Added:
    - final execution validation
    - hidden error detection
    - optional external error awareness
    """

    if not steps or not isinstance(steps, list):
        return _empty_result()

    step_count        = len(steps)
    error_steps       = sum(1 for s in steps if not _success(s))
    recovery_attempts = sum(1 for s in steps if _agent(s) == "retry_generator")

    executor_steps   = [s for s in steps if _agent(s) == "executor"]
    had_failure      = any(not _success(s) for s in executor_steps)
    final_succeeded  = _success(executor_steps[-1]) if executor_steps else False
    recovery_success = int(had_failure and final_succeeded)

    # ─────────────────────────────
    # 🔥 NEW: additional signals
    # ─────────────────────────────

    # final execution failed
    final_executor_success = final_succeeded

    # any error messages present
    has_error_message = any(
        s.get("error") not in (None, "", "None")
        for s in steps
    )

    # external/system-level error (optional)
    external_error = False
    if response:
        external_error = bool(response.get("error"))

    # ─────────────────────────────
    # scoring (original + minimal extensions)
    # ─────────────────────────────

    score = 1.0
    score -= error_steps       * PENALTY_PER_ERROR
    score -= recovery_attempts * PENALTY_PER_RETRY

    # 🔥 NEW penalties
    if not final_executor_success:
        score -= FINAL_FAIL_PENALTY

    if has_error_message:
        score -= ERROR_MSG_PENALTY

    if external_error:
        score -= EXTERNAL_ERR_PENALTY

    if recovery_success:
        score += RECOVERY_BONUS

    trajectory_score = round(max(0.0, min(1.0, score)), 4)

    return {
        "step_count":        step_count,
        "error_steps":       error_steps,
        "recovery_attempts": recovery_attempts,
        "recovery_success":  recovery_success,
        "trajectory_score":  trajectory_score,
    }


# ─────────────────────────────────────────────────────────────────────────────
# helpers (UNCHANGED)
# ─────────────────────────────────────────────────────────────────────────────

def _success(step: dict) -> bool:
    return bool(step.get("success", True))


def _agent(step: dict) -> str:
    return step.get("agent_name", "")


def _empty_result() -> dict:
    return {
        "step_count":        0,
        "error_steps":       0,
        "recovery_attempts": 0,
        "recovery_success":  0,
        "trajectory_score":  1.0,
    }