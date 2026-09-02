"""Executes validated SQL queries safely and returns rows as dicts."""
from sqlalchemy import text
from app.database.connection import engine


def execute_query(sql: str) -> list[dict]:
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        columns = result.keys()
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows