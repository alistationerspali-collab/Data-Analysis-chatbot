"""Guards against unsafe SQL before execution."""
import re

BLOCKED_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
    "TRUNCATE", "EXEC", "EXECUTE", "MERGE", "GRANT", "REVOKE",
]


class UnsafeSQLError(Exception):
    pass


def validate_sql(sql: str, max_rows: int = 200) -> str:
    normalized = sql.strip().upper()

    if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
        raise UnsafeSQLError("Only SELECT statements (or WITH...SELECT CTEs) are allowed.")

    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", normalized):
            raise UnsafeSQLError(f"Blocked keyword detected: {keyword}")

    has_top = "TOP " in normalized
    has_offset_fetch = "OFFSET" in normalized and "FETCH" in normalized

    if not has_top and not has_offset_fetch and normalized.startswith("SELECT"):
        sql = re.sub(
            r"^SELECT\s+", f"SELECT TOP {max_rows} ", sql, count=1, flags=re.IGNORECASE
        )

    return sql