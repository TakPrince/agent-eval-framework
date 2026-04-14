# evals/metrics/db_utils.py

import sqlite3
from utils.logger import get_logger

logger = get_logger()


def create_connection(db_path="evals/metrics/test.db"):
    """
    Create SQLite connection
    """
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        return None


def setup_dummy_db(conn):
    """
    Create simple tables for testing
    """
    try:
        cursor = conn.cursor()

        # Create table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY,
            amount INTEGER
        )
        """)

        # Insert sample data
        cursor.execute("DELETE FROM sales")

        cursor.executemany(
            "INSERT INTO sales (amount) VALUES (?)",
            [(100,), (200,), (300,)]
        )

        conn.commit()

    except Exception as e:
        logger.error(f"DB setup failed: {e}")


def execute_query(conn, query):
    """
    Execute SQL and return result
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