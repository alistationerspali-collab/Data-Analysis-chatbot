"""Tests for the SQL safety guard.

Includes a regression test for the WITH(NOLOCK)-alias bug where the regex
incorrectly matched SQL keywords (e.g. WHERE) as table aliases and consumed
them, corrupting the query.
"""
import pytest
from app.security.sql_guard import validate_sql, add_nolock_hints, UnsafeSQLError


# --- Basic safety checks ---

def test_blocks_drop():
    with pytest.raises(UnsafeSQLError):
        validate_sql("DROP TABLE Master1")


def test_blocks_delete():
    with pytest.raises(UnsafeSQLError):
        validate_sql("DELETE FROM Master1 WHERE Code = 1")


def test_blocks_update():
    with pytest.raises(UnsafeSQLError):
        validate_sql("UPDATE Master1 SET Name = 'x' WHERE Code = 1")


def test_blocks_insert():
    with pytest.raises(UnsafeSQLError):
        validate_sql("INSERT INTO Master1 (Name) VALUES ('x')")


def test_rejects_non_select_non_with():
    with pytest.raises(UnsafeSQLError):
        validate_sql("EXEC sp_who")


def test_allows_select():
    result = validate_sql("SELECT * FROM Master1")
    assert "SELECT" in result.upper()


def test_allows_with_cte():
    result = validate_sql("WITH x AS (SELECT 1 AS a) SELECT * FROM x")
    assert result.strip().upper().startswith("WITH")


# --- TOP / OFFSET-FETCH handling ---

def test_adds_top_when_missing():
    result = validate_sql("SELECT Name FROM Master1")
    assert "TOP 200" in result.upper()


def test_does_not_duplicate_top():
    result = validate_sql("SELECT TOP 5 Name FROM Master1")
    assert result.upper().count("TOP") == 1


def test_does_not_add_top_when_offset_fetch_present():
    sql = "SELECT Name FROM Master1 ORDER BY Name OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY"
    result = validate_sql(sql)
    assert "TOP" not in result.upper()
    assert "OFFSET" in result.upper()


# --- NOLOCK hint placement ---

def test_nolock_added_simple_from():
    result = add_nolock_hints("SELECT * FROM Master1")
    assert "Master1 WITH (NOLOCK)" in result


def test_nolock_added_with_alias():
    result = add_nolock_hints("SELECT m.Name FROM Master1 m")
    assert "Master1 m WITH (NOLOCK)" in result


def test_nolock_added_on_join():
    result = add_nolock_hints("SELECT * FROM Tran2 t JOIN Master1 m ON t.MasterCode1 = m.Code")
    assert "Tran2 t WITH (NOLOCK)" in result
    assert "Master1 m WITH (NOLOCK)" in result


def test_nolock_regression_where_not_consumed_as_alias():
    """
    Regression test for the exact bug hit during development:
    the original regex matched 'WHERE' immediately after a table name
    as if it were an alias, consuming it and corrupting the query into
    invalid SQL (e.g. 'FROM Master1 WITH (NOLOCK) Name = ...' with WHERE
    silently deleted).
    """
    sql = "SELECT * FROM Master1 WHERE Name = 'Books House' AND MasterType = 5"
    result = add_nolock_hints(sql)

    # WHERE must be preserved, not swallowed by the alias-matching regex
    assert "WHERE" in result.upper()
    assert "Name = 'Books House'" in result
    # NOLOCK should be attached directly to the table, not to "WHERE"
    assert "Master1 WITH (NOLOCK)" in result
    assert "WHERE WITH (NOLOCK)" not in result


def test_nolock_regression_group_by_not_consumed_as_alias():
    """Same bug class, but for GROUP BY immediately following a table name."""
    sql = "SELECT m.Name, SUM(t.Value1) FROM Tran2 t JOIN Master1 m ON t.MasterCode1 = m.Code GROUP BY m.Name"
    result = add_nolock_hints(sql)

    assert "GROUP BY m.Name" in result
    assert "GROUP WITH (NOLOCK)" not in result


def test_nolock_regression_recursive_cte_full_query():
    """
    Full regression test using the exact recursive CTE query that originally
    triggered the bug (group-wise sales for 'Books House').
    """
    sql = """WITH RecursiveCTE AS (
    SELECT Code, Name, MasterType, ParentGrp
    FROM Master1
    WHERE Name = 'Books House' AND MasterType = 5
    UNION ALL
    SELECT m.Code, m.Name, m.MasterType, m.ParentGrp
    FROM Master1 m
    JOIN RecursiveCTE r ON m.ParentGrp = r.Code
    WHERE m.MasterType IN (5,6)
)
SELECT TOP 5 i.Name AS ItemName, SUM(t.Value3) AS TotalSalesAmount
FROM RecursiveCTE r
JOIN Master1 i ON i.Code = r.Code AND i.MasterType = 6
JOIN Tran2 t ON t.MasterCode1 = i.Code
GROUP BY i.Name
ORDER BY TotalSalesAmount DESC"""

    result = add_nolock_hints(sql)

    # Both WHERE clauses must survive intact
    assert result.count("WHERE") == 2
    assert "Name = 'Books House' AND MasterType = 5" in result
    assert "m.MasterType IN (5,6)" in result

    # GROUP BY / ORDER BY must survive intact
    assert "GROUP BY i.Name" in result
    assert "ORDER BY TotalSalesAmount DESC" in result

    # RecursiveCTE is not a known table so should NOT get a NOLOCK hint
    assert "RecursiveCTE WITH (NOLOCK)" not in result

    # Real tables should each get NOLOCK, correctly placed after any alias
    assert "Master1 WITH (NOLOCK)" in result  # first FROM Master1, no alias
    assert "Master1 m WITH (NOLOCK)" in result  # aliased occurrence
    assert "Master1 i WITH (NOLOCK)" in result  # aliased occurrence
    assert "Tran2 t WITH (NOLOCK)" in result


def test_nolock_not_duplicated_if_already_present():
    sql = "SELECT * FROM Master1 WITH (NOLOCK)"
    result = add_nolock_hints(sql)
    assert result.upper().count("NOLOCK") == 1