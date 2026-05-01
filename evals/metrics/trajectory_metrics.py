"""
evals/metrics/trajectory_metrics.py
------------------------------------
Phase 4: Trajectory-level evaluation.

Measures HOW the system reached its answer, not just whether the
final SQL was correct.  Operates entirely on state.steps — no
dependency on runners, SQL metrics, or evaluation logic.

All inputs are defensive: missing keys, empty lists, and malformed
step dicts are handled gracefully so this never crashes the pipeline.
"""

from __future__ import annotations


# ─────────────────────────────────────────────────────────────────────────────
# Scoring constants  (single place to tune — never buried in logic)
# ─────────────────────────────────────────────────────────────────────────────

PENALTY_PER_ERROR   = 0.2
PENALTY_PER_RETRY   = 0.1
RECOVERY_BONUS      = 0.2


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_trajectory(steps: list) -> dict:
    """
    Compute trajectory metrics from the steps audit trail.

    Parameters
    ----------
    steps : list of dicts, each produced by StepRecord.__dict__
            Expected keys per step: agent_name, success, output, error, latency
            Missing keys are tolerated — defaults applied.

    Returns
    -------
    dict with keys:
        step_count          : int   — total nodes that ran
        error_steps         : int   — nodes that reported success=False
        recovery_attempts   : int   — retry_generator nodes fired
        recovery_success    : int   — 1 if system recovered from at least one failure
        trajectory_score    : float — 0.0 – 1.0 quality of the execution path
    """

    # ── guard: empty or invalid input ────────────────────────────
    if not steps or not isinstance(steps, list):
        return _empty_result()

    # ── raw counts ────────────────────────────────────────────────
    step_count        = len(steps)
    error_steps       = sum(1 for s in steps if not _success(s))
    recovery_attempts = sum(1 for s in steps if _agent(s) == "retry_generator")

    # ── recovery_success ─────────────────────────────────────────
    # True when: at least one executor step failed AND the LAST
    # executor step succeeded.  This means the retry loop fixed it.
    executor_steps   = [s for s in steps if _agent(s) == "executor"]
    had_failure      = any(not _success(s) for s in executor_steps)
    final_succeeded  = _success(executor_steps[-1]) if executor_steps else False
    recovery_success = int(had_failure and final_succeeded)

    # ── trajectory_score ─────────────────────────────────────────
    score = 1.0
    score -= error_steps       * PENALTY_PER_ERROR
    score -= recovery_attempts * PENALTY_PER_RETRY
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
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _success(step: dict) -> bool:
    """Return the success flag of a step dict; defaults to True if missing."""
    return bool(step.get("success", True))


def _agent(step: dict) -> str:
    """Return the agent_name of a step dict; defaults to empty string."""
    return step.get("agent_name", "")


def _empty_result() -> dict:
    """Safe default when no steps are available (e.g. fallback path)."""
    return {
        "step_count":        0,
        "error_steps":       0,
        "recovery_attempts": 0,
        "recovery_success":  0,
        "trajectory_score":  1.0,   # no evidence of failure → assume clean
    }