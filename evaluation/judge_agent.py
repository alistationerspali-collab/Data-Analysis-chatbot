"""LLM-as-judge: checks semantic correctness against the golden dataset intent."""
from app.llm.groq_client import get_completion
from app.database.schema_loader import load_schema

JUDGE_PROMPT = """You are grading a text-to-SQL system built for Busy Accounting
Software's database. You MUST evaluate strictly against the VERIFIED SCHEMA below --
this schema was manually confirmed against real screenshots of Busy's UI (item HSN
codes, account ledgers, transaction amounts). Do NOT use general/generic assumptions
about how "most" Busy or ERP schemas work -- only use what's stated in this schema.

=== VERIFIED SCHEMA ===
{schema}
=== END SCHEMA ===

Question: {question}
Generated SQL: {sql}
Result sample (first few rows): {sample_rows}

Does this SQL correctly and completely answer the question, per the VERIFIED SCHEMA
above (not generic assumptions)? If sql is null/None, that means the system declined
to answer -- do not judge correctness in that case, just return correct: true.

Respond ONLY as JSON: {{"correct": true, "reason": "..."}}
"""


def judge_correctness(question: str, sql: str, sample_rows: list) -> dict:
    schema = load_schema()
    prompt = JUDGE_PROMPT.format(question=question, sql=sql, sample_rows=sample_rows, schema=schema)
    messages = [{"role": "user", "content": prompt}]
    return get_completion(messages, response_format="json")