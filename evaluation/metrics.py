"""Scoring functions for evaluation."""


def sql_executed_successfully(response: dict) -> bool:
    return "error" not in response and not response.get("declined", False)


def correctly_declined(response: dict, should_decline: bool) -> bool:
    """Checks whether the system's decline/answer behavior matches expectation."""
    actually_declined = response.get("declined", False)
    return actually_declined == should_decline


def chart_type_matches(response: dict, expected_chart_type: str) -> bool:
    actual = response.get("chart_spec", {}).get("chart_type")
    return actual == expected_chart_type


def has_data(response: dict) -> bool:
    return bool(response.get("data"))