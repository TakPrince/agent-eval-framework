# evals/reports/report_generator.py

import json
from utils.logger import get_logger

logger = get_logger()


def generate_report(results: list, output_path="evals/reports/report.json"):
    """
    Save detailed results to JSON file
    """
    try:
        with open(output_path, "w") as f:
            json.dump(results, f, indent=4)

        logger.info(f"Report saved to {output_path}")

    except Exception as e:
        logger.error(f"Report generation failed: {e}")


def generate_summary(results: list) -> dict:
    """
    Generate overall summary statistics
    """
    if not results:
        return {}

    total = len(results)

    avg_sql = sum(r["final"]["sql_score"] for r in results) / total
    avg_agent = sum(r["final"]["agent_score"] for r in results) / total
    avg_perf = sum(r["final"]["performance_score"] for r in results) / total
    avg_final = sum(r["final"]["final_score"] for r in results) / total

    return {
        "total_queries": total,
        "avg_sql_score": avg_sql,
        "avg_agent_score": avg_agent,
        "avg_performance_score": avg_perf,
        "avg_final_score": avg_final
    }