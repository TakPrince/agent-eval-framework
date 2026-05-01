from utils.logger import get_logger
from evals.metrics.trajectory_metrics import evaluate_trajectory    # Phase 4
from evals.metrics.advanced_metrics import (                        # Phase 6
    compute_ves,
    compute_adjusted_score,
)

logger = get_logger()


def combine_scores(
    sql_eval:   dict,
    agent_eval: dict,
    perf_eval:  dict,
    steps:      list = None,    # Phase 4 — optional, safe default
) -> dict:
    """
    Combine all evaluation metrics into final score.
    Phase 4: trajectory_eval added as additive observability field.
    Phase 6: ves_score and adjusted_score added — final_score UNCHANGED.
    """
    try:
        sql_score   = sql_eval.get("score", 0)
        agent_score = agent_eval.get("score", 0)
        perf_score  = perf_eval.get("score", 0)

        # 🔥 WEIGHTS (unchanged)
        final_score = (
            (sql_score   * 0.5) +
            (agent_score * 0.3) +
            (perf_score  * 0.2)
        )

        # Phase 4 — trajectory is observability only, does not affect final_score
        trajectory_eval = evaluate_trajectory(steps or [])

        # Phase 6 — advanced scores (additive, never replace final_score)
        ves_score      = compute_ves(sql_eval, trajectory_eval, perf_eval)
        adjusted_score = compute_adjusted_score(final_score, trajectory_eval)

        return {
            "sql_score":         sql_score,
            "agent_score":       agent_score,
            "performance_score": perf_score,
            "final_score":       final_score,
            "trajectory_eval":   trajectory_eval,   # Phase 4
            "ves_score":         ves_score,          # Phase 6
            "adjusted_score":    adjusted_score,     # Phase 6
        }

    except Exception as e:
        logger.error(f"Final evaluation failed: {e}")
        return {
            "sql_score":         0,
            "agent_score":       0,
            "performance_score": 0,
            "final_score":       0,
            "trajectory_eval":   {},    # Phase 4 — safe empty fallback
            "ves_score":         0,     # Phase 6 — safe empty fallback
            "adjusted_score":    0,     # Phase 6 — safe empty fallback
        }