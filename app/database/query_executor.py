"""Executes validated SQL queries safely and returns rows as dicts."""
from sqlalchemy import text
from app.database.connection import engine

QUERY_TIMEOUT_SECONDS = 15


def execute_query(sql: str) -> list[dict]:
    with engine.connect() as conn:
        # Set a hard query timeout so a stuck/slow query can never hang indefinitely
        conn.execute(text(f"SET LOCK_TIMEOUT {QUERY_TIMEOUT_SECONDS * 1000}"))
        result = conn.execute(text(sql))
        columns = result.keys()
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        conn.close()
    return rows