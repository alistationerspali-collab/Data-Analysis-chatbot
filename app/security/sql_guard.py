"""Guards against unsafe SQL before execution, and protects the live Busy
database from being blocked/locked by chatbot queries."""
import re

BLOCKED_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
    "TRUNCATE", "EXEC", "EXECUTE", "MERGE", "GRANT", "REVOKE",
]

KNOWN_TABLES = ["Tran2", "Master1", "OrgSalePurc"]

SQL_RESERVED = {
    "WHERE", "JOIN", "ON", "GROUP", "ORDER", "HAVING", "UNION", "INNER",
    "LEFT", "RIGHT", "FULL", "CROSS", "AS", "SET", "AND", "OR", "BY",
    "INTO", "VALUES", "SELECT", "FROM", "WITH",
}


class UnsafeSQLError(Exception):
    pass


def add_nolock_hints(sql: str) -> str:
    """Adds WITH (NOLOCK) after known table names, anchored specifically to
    FROM/JOIN clauses. Uses a negative lookahead so SQL keywords are never
    mistaken for aliases and are never consumed by the match."""
    tables_pattern = "|".join(KNOWN_TABLES)
    reserved_pattern = "|".join(SQL_RESERVED)

    # Alias group only matches a word that is NOT a reserved SQL keyword
    pattern = (
        rf"\b(FROM|JOIN)\s+({tables_pattern})\b"
        rf"(\s+(?:AS\s+)?(?!(?:{reserved_pattern})\b)([a-zA-Z_][a-zA-Z0-9_]*))?"
    )

    def replacer(match):
        prefix = match.group(1)
        table = match.group(2)
        alias = match.group(4)
        if alias:
            return f"{prefix} {table} {alias} WITH (NOLOCK)"
        return f"{prefix} {table} WITH (NOLOCK)"

    return re.sub(pattern, replacer, sql, flags=re.IGNORECASE)


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

    sql = add_nolock_hints(sql)

    return sql