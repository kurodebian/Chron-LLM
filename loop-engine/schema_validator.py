import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).parent / "schemas" / "proposal.schema.json"


def validate_proposal_schema(proposal: dict[str, Any]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = Draft202012Validator(schema)
    validator.validate(proposal)
