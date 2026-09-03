"""Runs the full pipeline against the golden dataset and reports metrics."""
import json
import os
import time
from datetime import datetime

from app.chat.chat_handler import handle
from evaluation.golden_dataset import load_golden_dataset
from evaluation.judge_agent import judge_correctness
from evaluation.metrics import sql_executed_successfully, correctly_declined, chart_type_matches

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
DELAY_BETWEEN_CASES_SECONDS = 5  # avoid hitting Groq's tokens-per-minute limit


def run_evaluation() -> dict:
    cases = load_golden_dataset()
    results = []

    for i, case in enumerate(cases):
        if i > 0:
            time.sleep(DELAY_BETWEEN_CASES_SECONDS)

        try:
            response = handle(case["question"], session_id=f"eval_{case['id']}")
        except Exception as e:
            print(f"[{case['id']}] ERROR - {case['question']} -- {e}")
            results.append({
                "id": case["id"], "question": case["question"], "category": case.get("category"),
                "should_decline": case.get("should_decline", False),
                "sql_executed": False, "decline_correct": False, "chart_type_match": False,
                "semantic_correct": False, "judge_reason": f"Exception: {e}", "iterations": None,
            })
            continue

        result = {
            "id": case["id"],
            "question": case["question"],
            "category": case.get("category"),
            "should_decline": case.get("should_decline", False),
            "sql_executed": sql_executed_successfully(response),
            "decline_correct": correctly_declined(response, case.get("should_decline", False)),
            "chart_type_match": chart_type_matches(response, case.get("expected_chart_type")),
            "iterations": response.get("iterations"),
        }

        if response.get("declined") or "error" in response:
            result["semantic_correct"] = result["decline_correct"]
            result["judge_reason"] = response.get("reason", response.get("error", ""))
        else:
            try:
                verdict = judge_correctness(
                    case["question"], response.get("sql", ""), response.get("data", [])[:5]
                )
                result["semantic_correct"] = verdict.get("correct", False)
                result["judge_reason"] = verdict.get("reason", "")
            except Exception as e:
                result["semantic_correct"] = False
                result["judge_reason"] = f"Judge call failed: {e}"

        results.append(result)
        status = "PASS" if result["semantic_correct"] and result["decline_correct"] else "FAIL"
        print(f"[{result['id']}] {status} - {case['question']}")

    summary = summarize(results)
    save_report(summary)
    return summary


def summarize(results: list) -> dict:
    total = len(results) or 1
    return {
        "total_cases": len(results),
        "semantic_accuracy": sum(r["semantic_correct"] for r in results) / total,
        "decline_accuracy": sum(r["decline_correct"] for r in results) / total,
        "chart_type_match_rate": sum(r["chart_type_match"] for r in results) / total,
        "avg_iterations": sum(r["iterations"] or 0 for r in results) / total,
        "results": results,
    }


def save_report(summary: dict) -> None:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(REPORTS_DIR, f"eval_report_{timestamp}.json")
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nReport saved to {path}")


if __name__ == "__main__":
    result = run_evaluation()
    print(json.dumps({k: v for k, v in result.items() if k != "results"}, indent=2))