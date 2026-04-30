# evals/metrics/db_utils.py
import sqlite3
from utils.logger import get_logger

logger = get_logger()


def create_connection(db_path=":memory:"):
    """
    Create SQLite connection.
    FIX: Changed from file-based "test.db" to in-memory ":memory:"
    - File-based DB persists stale schema between runs, causing ghost table errors
    - In-memory DB is always fresh, no cleanup needed, faster for evals
    """
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        return None


def setup_dummy_db(conn):
    """
    Create singer table with sample data for testing.
    FIX: Was creating a "sales" table — but ALL eval queries use "singer".
    Every execution_match was returning None → 0 because the table didn't exist.
    """
    try:
        cursor = conn.cursor()

        # FIX: create singer table (matches schema used in all runners and prompts)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS singer (
                id       INTEGER PRIMARY KEY,
                name     TEXT,
                country  TEXT,
                birthday TEXT
            )
        """)

        # Clear and re-insert so each eval run starts clean
        cursor.execute("DELETE FROM singer")

        # Sample data — covers all query types in the Spider dataset:
        # COUNT, ORDER BY birthday, WHERE country, MIN/MAX id, DISTINCT country
        cursor.executemany(
            "INSERT INTO singer (id, name, country, birthday) VALUES (?, ?, ?, ?)",
            [
                (1, "Alice",   "France", "1985-03-12"),
                (2, "Bob",     "USA",    "1990-07-25"),
                (3, "Charlie", "France", "1978-11-05"),
                (4, "Diana",   "UK",     "2001-06-18"),
                (5, "Eve",     "USA",    "2001-02-28"),
            ]
        )

        conn.commit()

    except Exception as e:
        logger.error(f"DB setup failed: {e}")


def execute_query(conn, query):
    """
    Execute SQL and return result.
    """
    if not query:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Exception as e:
        logger.warning(f"Query execution failed: {e}")
        return None
    
import sqlite3

def execute_sql(sql):
    """
    Execute SQL query on in-memory SQLite DB.
    This reuses the same schema used in sql_metrics.
    """

    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # 🔥 SAME TABLE YOU USED EARLIER
    cursor.execute("""
        CREATE TABLE singer (
            id INTEGER,
            name TEXT,
            country TEXT,
            birthday TEXT
        )
    """)

    # Sample data (same as before)
    cursor.executemany(
        "INSERT INTO singer VALUES (?, ?, ?, ?)",
        [
            (1, "A", "USA", "1990"),
            (2, "B", "UK", "1985"),
            (3, "C", "USA", "1992"),
        ]
    )

    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        return result

    finally:
        conn.close()