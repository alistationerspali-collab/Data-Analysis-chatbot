"""
create_structure.py
Creates the empty folder/file architecture for Data-Analysis-chatbot.
No content is written yet -- just folders + blank files.

Run from inside your already-cloned repo folder:
    cd Data-Analysis-chatbot
    python create_structure.py
"""

import os

FOLDERS = [
    "app",
    "app/database",
    "app/llm",
    "app/llm/agents",
    "app/chat",
    "app/security",
    "app/utils",
    "evaluation",
    "evaluation/reports",
    "frontend",
    "tests",
]

FILES = [
    "app/__init__.py",
    "app/config.py",
    "app/main.py",

    "app/database/__init__.py",
    "app/database/connection.py",
    "app/database/schema_loader.py",
    "app/database/busy_schema_annotation.py",
    "app/database/query_executor.py",

    "app/llm/__init__.py",
    "app/llm/groq_client.py",
    "app/llm/chart_recommender.py",

    "app/llm/agents/__init__.py",
    "app/llm/agents/analyst_agent.py",
    "app/llm/agents/critic_agent.py",
    "app/llm/agents/orchestrator.py",

    "app/chat/__init__.py",
    "app/chat/chat_handler.py",
    "app/chat/history.py",

    "app/security/__init__.py",
    "app/security/sql_guard.py",

    "app/utils/__init__.py",
    "app/utils/logger.py",

    "evaluation/__init__.py",
    "evaluation/golden_dataset.py",
    "evaluation/golden_dataset.json",
    "evaluation/metrics.py",
    "evaluation/judge_agent.py",
    "evaluation/run_eval.py",

    "frontend/streamlit_app.py",

    "tests/test_sql_guard.py",
    "tests/test_schema_annotation.py",
    "tests/test_analyst_agent.py",
    "tests/test_critic_agent.py",
    "tests/test_orchestrator.py",

    "requirements.txt",
    ".env.example",
    "run.py",
]


def create_structure():
    for folder in FOLDERS:
        os.makedirs(folder, exist_ok=True)
        print(f"Created folder: {folder}")

    for file_path in FILES:
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        if not os.path.exists(file_path):
            open(file_path, "w").close()
            print(f"Created file:   {file_path}")
        else:
            print(f"Skipped (exists): {file_path}")

    print("\nDone. Empty structure created -- files have no content yet.")


if __name__ == "__main__":
    create_structure()