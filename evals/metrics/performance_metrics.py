# evals/metrics/performance_metrics.py
from utils.logger import get_logger

logger = get_logger()


def latency_score(latency: float) -> float:
    """
    Convert latency into score (lower is better).
    FIX: Thresholds updated for LLM API reality — original thresholds (<1s, <2s, <3s)
    were designed for normal REST APIs. LLMs typically take 2–10s, so almost every
    real response was scoring 0.2 (worst bucket) even on fast successful calls.
    """
    if latency is None:
        return 0.0

    # tuned for LLM inference latency
    if latency < 2:
        return 1.0
    elif latency < 4:
        return 0.7
    elif latency < 7:
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
    Main performance evaluation function.
    FIX: Added explicit error short-circuit at the top.
    Previously, an errored request with a latency value would still compute
    a partial latency score (e.g. latency=0.5s but error=True → score=0.49).
    A failed request should always return score=0 regardless of latency.
    """
    try:
        error = error_rate(response)

        # FIX: if request errored, score is 0 — no partial credit for fast failures
        if error:
            return {
                "latency": response.get("total_latency"),
                "latency_score": 0,
                "error": 1,
                "score": 0
            }

        latency = response.get("total_latency")
        latency_sc = latency_score(latency)

        # final performance score (weights unchanged)
        final_score = (latency_sc * 0.7) + ((1 - error) * 0.3)

        return {
            "latency": latency,
            "latency_score": latency_sc,
            "error": error,
            "score": round(final_score, 4)
        }

    except Exception as e:
        logger.error(f"Performance evaluation failed: {e}")
        return {
            "latency": None,
            "latency_score": 0,
            "error": 1,
            "score": 0
        }