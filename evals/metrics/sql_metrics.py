# evals/metrics/sql_metrics.py

from evals.metrics.db_utils import create_connection, setup_dummy_db, execute_query
from utils.logger import get_logger

logger = get_logger()


# -----------------------------
# 🔹 NORMALIZATION
# -----------------------------
def normalize_sql(sql: str) -> str:
    """
    Normalize SQL string for comparison.
    - Lowercase
    - Remove extra spaces
    """
    if not sql:
        return ""

    return " ".join(sql.lower().strip().split())


# -----------------------------
# 🔹 BASIC SQL VALIDATION
# -----------------------------
def is_valid_sql(sql: str) -> bool:
    """
    Basic SQL validation (safe, minimal)
    """
    if not sql:
        return False

    sql = sql.lower().strip()

    # minimal rule (safe, not strict)
    return "select" in sql and "from" in sql


# -----------------------------
# 🔹 EXACT MATCH
# -----------------------------
def exact_match(predicted_sql: str, expected_sql: str) -> int:
    """
    Returns 1 if SQL matches exactly after normalization, else 0.
    """
    if not predicted_sql or not expected_sql:
        return 0

    pred = normalize_sql(predicted_sql)
    exp = normalize_sql(expected_sql)

    return 1 if pred == exp else 0


# -----------------------------
# 🔹 PARTIAL MATCH (SAFE)
# -----------------------------
def contains_match(predicted_sql: str, expected_sql: str) -> int:
    """
    Partial match (loose check).
    FIXED: Handles None / invalid SQL safely
    """
    if not predicted_sql or not expected_sql:
        return 0

    # ❗ prevent invalid SQL from getting score
    if not is_valid_sql(predicted_sql):
        return 0

    pred = normalize_sql(predicted_sql)
    exp = normalize_sql(expected_sql)

    if exp in pred or pred in exp:
        return 1

    return 0


# -----------------------------
# 🔹 EXECUTION MATCH
# -----------------------------
def execution_match(predicted_sql: str, expected_sql: str) -> int:
    """
    Execute both SQL queries and compare results.
    """
    if not predicted_sql or not expected_sql:
        return 0

    conn = create_connection()
    if not conn:
        return 0

    try:
        setup_dummy_db(conn)

        pred_result = execute_query(conn, predicted_sql)
        exp_result = execute_query(conn, expected_sql)

        if pred_result is None or exp_result is None:
            return 0

        return 1 if pred_result == exp_result else 0

    except Exception as e:
        logger.warning(f"Execution match failed: {e}")
        return 0

    finally:
        conn.close()


# -----------------------------
# 🔹 MAIN EVALUATOR
# -----------------------------
def evaluate_sql(predicted_sql: str, expected_sql: str) -> dict:
    """
    Combined evaluation: execution + string match
    SAFE + ROBUST version
    """
    try:
        # ❗ Case: model returned nothing
        if not predicted_sql:
            return {
                "execution_match": 0,
                "exact_match": 0,
                "partial_match": 0,
                "score": 0
            }

        exec_score = execution_match(predicted_sql, expected_sql)
        exact = exact_match(predicted_sql, expected_sql)
        partial = contains_match(predicted_sql, expected_sql)

        # 🔥 priority scoring (unchanged logic)
        if exec_score == 1:
            final_score = 1
        elif exact == 1:
            final_score = 0.8
        elif partial == 1:
            final_score = 0.5
        else:
            final_score = 0

        return {
            "execution_match": exec_score,
            "exact_match": exact,
            "partial_match": partial,
            "score": final_score
        }

    except Exception as e:
        logger.error(f"SQL evaluation failed: {e}")
        return {
            "execution_match": 0,
            "exact_match": 0,
            "partial_match": 0,
            "score": 0
        }