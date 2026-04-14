# evals/evaluators/final_evaluator.py

from utils.logger import get_logger

logger = get_logger()


def combine_scores(sql_eval: dict, agent_eval: dict, perf_eval: dict) -> dict:
    """
    Combine all evaluation metrics into final score
    """

    try:
        sql_score = sql_eval.get("score", 0)
        agent_score = agent_eval.get("score", 0)
        perf_score = perf_eval.get("score", 0)

        # 🔥 WEIGHTS (can be tuned later)
        final_score = (
            (sql_score * 0.5) +      # accuracy is most important
            (agent_score * 0.3) +    # behavior
            (perf_score * 0.2)       # performance
        )

        return {
            "sql_score": sql_score,
            "agent_score": agent_score,
            "performance_score": perf_score,
            "final_score": final_score
        }

    except Exception as e:
        logger.error(f"Final evaluation failed: {e}")
        return {
            "sql_score": 0,
            "agent_score": 0,
            "performance_score": 0,
            "final_score": 0
        }