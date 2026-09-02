"""Critic agent: reviews the analyst's SQL + chart spec for correctness and safety."""
from app.llm.groq_client import get_completion

CRITIC_SYSTEM_PROMPT = """You are a meticulous QA reviewer for SQL and data visualization
against Busy Accounting Software's database.

Check for:
- SQL correctness (valid columns/tables per the schema, correct joins, correct filters)
- SQL safety (must be SELECT/WITH only)
- Whether the query actually answers the question
- Whether the chart_type fits the data shape
- Whether the analyst correctly refused anything listed under "EXPLICIT LIMITATIONS"
  in the schema (absolute outstanding balance, salesman-wise, Trial Balance/P&L/GST/
  TDS/Payroll) -- if the analyst attempted a query for one of these, mark REVISE.

Respond ONLY in this JSON format:
{"status": "APPROVED" or "REVISE", "feedback": "specific feedback if REVISE, else empty string"}
"""


def review_analysis(question: str, schema: str, analyst_output: dict) -> dict:
    messages = [
        {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Schema:\n{schema}\n\nQuestion: {question}\n\nAnalyst output: {analyst_output}"
        )},
    ]
    return get_completion(messages, response_format="json")