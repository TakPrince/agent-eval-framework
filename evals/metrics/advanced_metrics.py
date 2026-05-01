"""
evals/metrics/advanced_metrics.py
-----------------------------------
Phase 6: Advanced scoring layer.

Two functions — both purely additive, never replacing existing scores:

    compute_ves()            → Valid Efficiency Score (0–1)
    compute_adjusted_score() → Trajectory-penalised final score (0–1)

Design rules
~~~~~~~~~~~~
* No imports from runners, metrics, or evaluators — zero coupling
* All inputs accessed defensively (.get with safe defaults)
* Neither function raises — bad inputs produce 0.0, not exceptions
"""

from __future__ import annotations


# ─────────────────────────────────────────────────────────────────────────────
# Weights & penalty constants  (one place to tune)
# ─────────────────────────────────────────────────────────────────────────────

# VES weights
_VES_SQL_WEIGHT        = 0.5
_VES_TRAJECTORY_WEIGHT = 0.3
_VES_LATENCY_WEIGHT    = 0.2

# Trajectory penalty constants
_PENALTY_PER_ERROR_STEP      = 0.05
_PENALTY_PER_RECOVERY_ATTEMPT = 0.03


# ─────────────────────────────────────────────────────────────────────────────
# Public: Valid Efficiency Score
# ─────────────────────────────────────────────────────────────────────────────

def compute_ves(
    sql_eval:         dict,
    trajectory_eval:  dict,
    performance_eval: dict,
) -> float:
    """
    Valid Efficiency Score — rewards correctness, clean trajectories,
    and low latency together in a single number.

    Parameters
    ----------
    sql_eval         : output of evaluate_sql()
    trajectory_eval  : output of evaluate_trajectory()
    performance_eval : output of evaluate_performance()

    Returns
    -------
    float in [0.0, 1.0]

    Score interpretation
    --------------------
    1.0  → correct SQL, no retries, fast response
    ~0.7 → correct SQL but required retries or slow
    ~0.5 → partially correct, struggled through retries
    0.0  → complete failure on all three dimensions
    """
    sql_score       = _safe_float(sql_eval,         "score")
    trajectory_score = _safe_float(trajectory_eval,  "trajectory_score")
    latency_score   = _safe_float(performance_eval,  "latency_score")

    ves = (
        (sql_score        * _VES_SQL_WEIGHT)
        + (trajectory_score * _VES_TRAJECTORY_WEIGHT)
        + (latency_score    * _VES_LATENCY_WEIGHT)
    )

    return round(max(0.0, min(1.0, ves)), 4)


# ─────────────────────────────────────────────────────────────────────────────
# Public: trajectory-aware adjusted score
# ─────────────────────────────────────────────────────────────────────────────

def compute_adjusted_score(final_score: float, trajectory_eval: dict) -> float:
    """
    Apply trajectory penalties to the existing final_score.

    Penalises models that needed error recovery to reach a correct answer —
    a model that generates correct SQL first-time should score higher than
    one that needed two retries to produce the same SQL.

    Parameters
    ----------
    final_score     : the original weighted final_score from combine_scores()
    trajectory_eval : output of evaluate_trajectory()

    Returns
    -------
    float in [0.0, 1.0]

    Penalty table
    -------------
    Each failed step      → −0.05
    Each retry attempt    → −0.03
    Floor                 →  0.0  (never goes negative)
    """
    error_steps       = _safe_int(trajectory_eval, "error_steps")
    recovery_attempts = _safe_int(trajectory_eval, "recovery_attempts")

    penalty = (
        (_PENALTY_PER_ERROR_STEP       * error_steps)
        + (_PENALTY_PER_RECOVERY_ATTEMPT * recovery_attempts)
    )

    adjusted = final_score - penalty
    return round(max(0.0, adjusted), 4)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _safe_float(d: dict, key: str, default: float = 0.0) -> float:
    """Return float from dict key; fall back to default on any failure."""
    try:
        return float((d or {}).get(key, default))
    except (TypeError, ValueError):
        return default


def _safe_int(d: dict, key: str, default: int = 0) -> int:
    """Return int from dict key; fall back to default on any failure."""
    try:
        return int((d or {}).get(key, default))
    except (TypeError, ValueError):
        return default