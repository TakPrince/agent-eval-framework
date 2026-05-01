from utils.logger import get_logger

logger = get_logger()


# ─────────────────────────────────────────────────────────────
# Latency → score mapping (LLM realistic thresholds)
# ─────────────────────────────────────────────────────────────
def latency_score(latency: float) -> float:
    """
    Convert latency into score (lower is better).
    Tuned for LLM inference (2–10s typical).
    """
    if latency is None:
        return 0.0

    if latency < 2:
        return 1.0
    elif latency < 4:
        return 0.7
    elif latency < 7:
        return 0.5
    else:
        return 0.2


# ─────────────────────────────────────────────────────────────
# Error detection
# ─────────────────────────────────────────────────────────────
def error_rate(response: dict) -> int:
    return 1 if response.get("error") else 0


# ─────────────────────────────────────────────────────────────
# 🔥 REAL LATENCY EXTRACTION (CORE FIX)
# ─────────────────────────────────────────────────────────────
def extract_total_latency(response: dict) -> float:
    """
    Get real total latency from:
    1. response["total_latency"] (if exists)
    2. sum of step latencies (source of truth)
    """

    # 1. direct latency (if future system sets it)
    if response.get("total_latency") is not None:
        return response["total_latency"]

    # 2. fallback → sum of steps
    steps = response.get("steps", [])

    if not steps:
        return None

    total = 0.0

    for step in steps:
        if isinstance(step, dict):
            total += step.get("latency", 0) or 0

    return total if total > 0 else None


# ─────────────────────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────────────────────
def evaluate_performance(response: dict) -> dict:
    """
    Real performance evaluation based on execution latency.

    Fixes:
    - Uses step-level latency (real data)
    - Keeps compatibility with total_latency
    - Error short-circuit (no reward for failed runs)
    """

    try:
        error = error_rate(response)

        # 🔥 extract real latency
        latency = extract_total_latency(response)

        # ─────────────────────────────
        # ERROR SHORT-CIRCUIT
        # ─────────────────────────────
        if error:
            return {
                "latency": round(latency, 4) if latency else None,
                "latency_score": 0.0,
                "error": 1,
                "score": 0.0
            }

        # ─────────────────────────────
        # NORMAL CASE
        # ─────────────────────────────
        latency_sc = latency_score(latency)

        # keep your weighting (professional consistency)
        final_score = (latency_sc * 0.7) + ((1 - error) * 0.3)

        return {
            "latency": round(latency, 4) if latency else None,
            "latency_score": latency_sc,
            "error": error,
            "score": round(final_score, 4)
        }

    except Exception as e:
        logger.error(f"Performance evaluation failed: {e}")
        return {
            "latency": None,
            "latency_score": 0.0,
            "error": 1,
            "score": 0.0
        }