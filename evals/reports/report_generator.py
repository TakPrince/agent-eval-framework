import json
from utils.logger import get_logger

# Phase 5: LLM insight integration
from evals.insights.insight_generator import generate_insight, generate_summary_insights

logger = get_logger()


def generate_report(results: list, output_path="evals/reports/report.json", llm_runner=None):
    """
    Save detailed results to JSON file.
    Phase 5: appends "insight" field to each result if llm_runner is provided.
    """
    try:
        enriched = []
        for result in results:
            r = dict(result)  # shallow copy — never mutate the original

            # ── Phase 5: per-result LLM insight ──────────────────
            if llm_runner is not None:
                try:
                    r["insight"] = generate_insight(r, llm_runner)
                except Exception as e:
                    r["insight"] = f"[Insight generation failed: {e}]"
            else:
                r["insight"] = "[Insight not requested]"
            # ─────────────────────────────────────────────────────

            enriched.append(r)

        with open(output_path, "w") as f:
            json.dump(enriched, f, indent=4)

        logger.info(f"Report saved to {output_path}")

    except Exception as e:
        logger.error(f"Report generation failed: {e}")


def generate_summary(results: list, llm_runner=None) -> dict:
    """
    Generate overall summary statistics.
    Phase 5: appends batch_insight key if llm_runner is provided.
    """
    if not results:
        return {}

    total      = len(results)
    avg_sql    = sum(r["final"]["sql_score"]          for r in results) / total
    avg_agent  = sum(r["final"]["agent_score"]         for r in results) / total
    avg_perf   = sum(r["final"]["performance_score"]   for r in results) / total
    avg_final  = sum(r["final"]["final_score"]         for r in results) / total

    # ── Phase 4/5: trajectory aggregate ──────────────────────────
    avg_traj = sum(
        r["final"].get("trajectory_eval", {}).get("trajectory_score", 1.0)
        for r in results
    ) / total

    total_retries = sum(
        r["final"].get("trajectory_eval", {}).get("recovery_attempts", 0)
        for r in results
    )
    # ─────────────────────────────────────────────────────────────

    summary = {
        "total_queries":         total,
        "avg_sql_score":         avg_sql,
        "avg_agent_score":       avg_agent,
        "avg_performance_score": avg_perf,
        "avg_final_score":       avg_final,
        # Phase 4 / 5 additions
        "avg_trajectory_score":  avg_traj,
        "total_retries":         total_retries,
    }

    # ── Phase 5: batch-level LLM insight ─────────────────────────
    if llm_runner is not None:
        try:
            summary["batch_insight"] = generate_summary_insights(results, llm_runner)
        except Exception as e:
            summary["batch_insight"] = f"[Batch insight failed: {e}]"
    # ─────────────────────────────────────────────────────────────

    return summary  