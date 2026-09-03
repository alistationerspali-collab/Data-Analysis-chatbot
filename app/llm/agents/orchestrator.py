"""Runs the Analyst <-> Critic feedback loop."""
from app.llm.agents.analyst_agent import generate_analysis
from app.llm.agents.critic_agent import review_analysis
from app.config import settings


def run_analyst_critic_loop(question: str, schema: str, history: list[dict] = None) -> dict:
    feedback = None
    last_output = None

    for i in range(settings.max_critic_iterations):
        analyst_output = generate_analysis(question, schema, history=history, feedback=feedback)
        last_output = analyst_output

        if not analyst_output.get("sql"):
            return {"result": analyst_output, "iterations": i + 1, "approved": True, "declined": True}

        review = review_analysis(question, schema, analyst_output)

        if review["status"] == "APPROVED":
            return {"result": analyst_output, "iterations": i + 1, "approved": True, "declined": False}

        feedback = review["feedback"]

    return {"result": last_output, "iterations": settings.max_critic_iterations, "approved": False, "declined": False}