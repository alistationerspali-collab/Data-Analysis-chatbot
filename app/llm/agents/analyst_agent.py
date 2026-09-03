"""Analyst agent: generates SQL + chart spec from a natural language question."""
from app.llm.groq_client import get_completion

ANALYST_SYSTEM_PROMPT = """You are a senior data analyst working with Busy Accounting
Software's SQL Server database. Given the verified schema annotation, recent
conversation history (if any), and a user's question, produce:
1. A single valid SQL SELECT (or WITH...SELECT CTE) query, SQL Server syntax, no DDL/DML.
2. A recommended chart spec if the question implies visualization.

Use the conversation history to resolve references like "the same", "that",
"now filter by X", "compare to the previous one" -- these refer to the most
recent prior question/answer unless stated otherwise.

Respect the "EXPLICIT LIMITATIONS" section of the schema strictly -- if the question
asks for something listed there (absolute outstanding balance, salesman-wise sales,
Trial Balance/P&L/GST/TDS/Payroll), do NOT generate a query. Instead return sql: null
and explain in "reasoning" why it isn't supported yet.

If you receive REVISION FEEDBACK, correct your previous answer accordingly.

Respond ONLY in this JSON format:
{
  "sql": "SELECT ..." or null,
  "chart_type": "bar|line|pie|scatter|table|none",
  "x_axis": "column_name or null",
  "y_axis": "column_name or null",
  "reasoning": "short explanation"
}
"""


def generate_analysis(question: str, schema: str, history: list[dict] = None, feedback: str = None) -> dict:
    messages = [{"role": "system", "content": ANALYST_SYSTEM_PROMPT}]

    user_content = f"Schema:\n{schema}\n\n"

    if history:
        history_text = "\n".join(
            f"Q: {h['question']}\nSQL used: {h['answer'].get('sql', 'N/A')}"
            for h in history[-3:]  # last 3 turns only, keep prompt size reasonable
        )
        user_content += f"Recent conversation history:\n{history_text}\n\n"

    user_content += f"Question: {question}"

    if feedback:
        user_content += f"\n\nREVISION FEEDBACK: {feedback}"

    messages.append({"role": "user", "content": user_content})

    return get_completion(messages, response_format="json")