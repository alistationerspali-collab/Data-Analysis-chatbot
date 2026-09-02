"""
Loads the schema context fed to the LLM.

IMPORTANT: Busy's database uses generic, cryptic table/column names
(Tran2, Master1, Value1/2/3, MasterCode1/2, etc.) reverse-engineered manually.
Raw INFORMATION_SCHEMA output is NOT enough for the LLM to generate correct SQL.
We use the hand-verified annotated schema instead (see busy_schema_annotation.py).
"""
from app.database.busy_schema_annotation import BUSY_SCHEMA_ANNOTATION


def load_schema(force_refresh: bool = False) -> str:
    return BUSY_SCHEMA_ANNOTATION