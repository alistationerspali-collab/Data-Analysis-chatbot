"""Loads the golden dataset for evaluation."""
import json
import os

DATASET_PATH = os.path.join(os.path.dirname(__file__), "golden_dataset.json")


def load_golden_dataset() -> list[dict]:
    with open(DATASET_PATH) as f:
        return json.load(f)