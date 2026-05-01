import re
from evals.metrics.db_utils import create_connection, setup_dummy_db, execute_query
from utils.logger import get_logger

logger = get_logger()


# -----------------------------
# 🔹 NORMALIZATION
# -----------------------------
def normalize_sql(sql: str) -> str:
    if not sql:
        return ""

    sql = sql.strip()

    if "```" in sql:
        parts = sql.split("```")
        if parts[0].lower().strip().startswith("select"):
            sql = parts[0].strip()
        else:
            sql = parts[1].strip()
            if sql.lower().startswith("sql"):
                sql = sql[3:].strip()

    sql = sql.rstrip(";").strip()
    sql = re.sub(r'\s*,\s*', ', ', sql)

    return " ".join(sql.lower().strip().split())


# -----------------------------
# 🔹 BASIC SQL VALIDATION
# -----------------------------
def is_valid_sql(sql: str) -> bool:
    if not sql:
        return False
    sql = sql.lower().strip()
    return "select" in sql and "from" in sql


# -----------------------------
# 🔹 EXACT MATCH
# -----------------------------
def exact_match(predicted_sql: str, expected_sql: str) -> int:
    if not predicted_sql or not expected_sql:
        return 0
    return 1 if normalize_sql(predicted_sql) == normalize_sql(expected_sql) else 0


# -----------------------------
# 🔹 PARTIAL MATCH
# -----------------------------
def contains_match(predicted_sql: str, expected_sql: str) -> int:
    if not predicted_sql or not expected_sql:
        return 0

    if not is_valid_sql(predicted_sql):
        return 0

    pred = normalize_sql(predicted_sql)
    exp = normalize_sql(expected_sql)

    return 1 if exp in pred else 0


# -----------------------------
# 🔹 RESULT NORMALIZATION (NEW)
# -----------------------------
def normalize_result(result):
    """
    Normalize SQL execution results:
    - Handle None / NULL consistently
    - Convert to comparable tuples
    - Sort rows (ignore ordering differences)
    """
    if result is None:
        return []

    normalized = []
    for row in result:
        normalized_row = tuple(None if v is None else v for v in row)
        normalized.append(normalized_row)

    return sorted(normalized)


# -----------------------------
# 🔹 EXECUTION MATCH (FIXED)
# -----------------------------
def execution_match(predicted_sql: str, expected_sql: str) -> int:
    if not predicted_sql or not expected_sql:
        return 0

    conn = create_connection()
    if not conn:
        return 0

    try:
        setup_dummy_db(conn)

        # ✅ Normalize SQL before execution
        clean_predicted = normalize_sql(predicted_sql)
        clean_expected = normalize_sql(expected_sql)

        pred_result = execute_query(conn, clean_predicted)
        exp_result = execute_query(conn, clean_expected)

        if pred_result is None or exp_result is None:
            return 0

        # ✅ Normalize outputs before comparing
        pred_norm = normalize_result(pred_result)
        exp_norm = normalize_result(exp_result)

        return 1 if pred_norm == exp_norm else 0

    except Exception as e:
        logger.warning(f"Execution match failed: {e}")
        return 0

    finally:
        conn.close()


# -----------------------------
# 🔹 MAIN EVALUATOR
# -----------------------------
def evaluate_sql(predicted_sql: str, expected_sql: str) -> dict:
    try:
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