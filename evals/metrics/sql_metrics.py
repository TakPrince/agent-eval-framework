# evals/metrics/sql_metrics.py
import re
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
    - Strip markdown code fences (```sql ... ```) in case runner cleanup missed them
    - FIX: Also strip a trailing ``` that appears AFTER the SQL (no opening fence)
      e.g. "SELECT name FROM singer;\n```" — split on ``` gives parts[0] as the SQL
    - FIX: Strip trailing semicolon after fence cleanup
      e.g. predicted "ORDER BY birthday ASC;" vs expected "ORDER BY birthday ASC"
      causes exact_match=0 and partial_match=0 even though the SQL is correct
    """
    if not sql:
        return ""

    sql = sql.strip()

    if "```" in sql:
        parts = sql.split("```")
        if parts[0].lower().strip().startswith("select"):
            # FIX: trailing fence case — SQL is in parts[0], closing ``` is parts[1]
            # e.g. "SELECT name FROM singer;\n```"
            sql = parts[0].strip()
        else:
            # wrapped fence case — SQL is in parts[1]
            # e.g. "```sql\nSELECT ...\n```"
            sql = parts[1].strip()
            if sql.lower().startswith("sql"):
                sql = sql[3:].strip()

    # FIX: remove trailing semicolon — it causes exact/partial match failure
    # "SELECT name FROM singer;" != "SELECT name FROM singer"
    sql = sql.rstrip(";").strip()

    # FIX: normalize comma spacing — "name , country" vs "name, country" are identical
    sql = re.sub(r'\s*,\s*', ', ', sql)

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
    FIX: Only check `exp in pred` direction (not `pred in exp`)
    - `pred in exp` was a false-positive trap: a short/incomplete predicted SQL
      (e.g. "select count ( * ) from singer") would match inside a longer expected SQL
      even when the prediction is missing clauses like WHERE, ORDER BY, etc.
    - Correct direction: does the prediction *contain* the expected core?
    """
    if not predicted_sql or not expected_sql:
        return 0

    # prevent invalid SQL from getting score
    if not is_valid_sql(predicted_sql):
        return 0

    pred = normalize_sql(predicted_sql)
    exp = normalize_sql(expected_sql)

    # FIX: removed `pred in exp` — only keep `exp in pred`
    # pred in exp gave scores to incomplete/truncated predictions
    if exp in pred:
        return 1
    return 0


# -----------------------------
# 🔹 EXECUTION MATCH
# -----------------------------
def execution_match(predicted_sql: str, expected_sql: str) -> int:
    """
    Execute both SQL queries and compare results.
    FIX: normalize both SQLs before execution — raw predicted SQL often contains
    \n newlines and trailing ; which can cause SQLite execute() to fail or
    return wrong results even when the query is logically correct
    """
    if not predicted_sql or not expected_sql:
        return 0

    conn = create_connection()
    if not conn:
        return 0

    try:
        setup_dummy_db(conn)

        # FIX: strip semicolon and newlines before executing
        # SQLite accepts semicolons in some cases but it's safer to remove them
        clean_predicted = predicted_sql.rstrip(";").strip()
        clean_expected = expected_sql.rstrip(";").strip()

        pred_result = execute_query(conn, clean_predicted)
        exp_result = execute_query(conn, clean_expected)

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
        # Case: model returned nothing
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

        # priority scoring (unchanged logic)
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