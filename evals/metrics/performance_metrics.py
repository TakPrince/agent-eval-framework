# evals/metrics/performance_metrics.py

from utils.logger import get_logger

logger = get_logger()


def latency_score(latency: float) -> float:
    """
    Convert latency into score (lower is better).
    """
    if latency is None:
        return 0.0

    # simple normalization (you can tune later)
    if latency < 1:
        return 1.0
    elif latency < 2:
        return 0.7
    elif latency < 3:
        return 0.5
    else:
        return 0.2


def error_rate(response: dict) -> int:
    """
    Check if request failed.
    """
    return 1 if response.get("error") else 0


def evaluate_performance(response: dict) -> dict:
    """
    Main performance evaluation function
    """
    try:
        latency = response.get("total_latency")

        latency_sc = latency_score(latency)
        error = error_rate(response)

        # final performance score
        final_score = (latency_sc * 0.7) + ((1 - error) * 0.3)

        return {
            "latency": latency,
            "latency_score": latency_sc,
            "error": error,
            "score": final_score
        }

    except Exception as e:
        logger.error(f"Performance evaluation failed: {e}")
        return {
            "latency": None,
            "latency_score": 0,
            "error": 1,
            "score": 0
        }