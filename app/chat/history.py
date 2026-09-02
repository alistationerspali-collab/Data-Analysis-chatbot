"""In-memory session history (swap for Redis/DB for production)."""

_SESSIONS: dict[str, list[dict]] = {}


def get_history(session_id: str) -> list[dict]:
    return _SESSIONS.get(session_id, [])


def append_history(session_id: str, question: str, answer: dict) -> None:
    _SESSIONS.setdefault(session_id, []).append({"question": question, "answer": answer})