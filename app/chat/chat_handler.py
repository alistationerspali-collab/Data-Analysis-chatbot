"""Orchestrates: question -> analyst/critic loop -> guard -> execute -> respond."""
from app.llm.agents.orchestrator import run_analyst_critic_loop
from app.security.sql_guard import validate_sql, UnsafeSQLError
from app.database.query_executor import execute_query
from app.database.schema_loader import load_schema
from app.chat.history import append_history


def handle(question: str, session_id: str) -> dict:
    schema = load_schema()
    loop_result = run_analyst_critic_loop(question, schema)
    analysis = loop_result["result"]

    if loop_result.get("declined"):
        response = {"declined": True, "reason": analysis.get("reasoning", "This isn't supported yet.")}
        append_history(session_id, question, response)
        return response

    if not loop_result["approved"]:
        return {"error": "Could not produce a safe, validated query.", "details": analysis}

    try:
        safe_sql = validate_sql(analysis["sql"])
    except UnsafeSQLError as e:
        return {"error": str(e)}

    rows = execute_query(safe_sql)

    response = {
        "sql": safe_sql,
        "data": rows,
        "chart_spec": {
            "chart_type": analysis.get("chart_type"),
            "x_axis": analysis.get("x_axis"),
            "y_axis": analysis.get("y_axis"),
        },
        "iterations": loop_result["iterations"],
    }

    append_history(session_id, question, response)
    return response