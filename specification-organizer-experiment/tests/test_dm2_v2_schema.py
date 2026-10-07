import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "dm2-semantic-extraction-record-v2.schema.json"


def load_validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


BASE = {
    "unit_id": "u0001",
    "line_start": 13,
    "line_end": 15,
    "source_text": "The system SHALL preserve canonical evidence.",
    "semantic_kind": "Requirement",
    "semantic_evidence": {
        "phrases": ["SHALL preserve canonical evidence"],
        "lines": [13],
    },
    "semantic_attributes": {
        "modality": "shall",
        "structural_form": "paragraph",
        "semantic_strength": "strong",
        "semantic_scope": "system-wide",
    },
}


def validate(record):
    errors = list(load_validator().iter_errors(record))
    assert not errors, "\n".join(
        f"{e.json_path}: {e.message}" for e in errors
    )


def validate_rejected(record):
    errors = list(load_validator().iter_errors(record))
    assert errors, "Expected schema rejection"


def test_resolved_valid():
    record = {
        **BASE,
        "resolution": {
            "status": "resolved",
            "reason": None,
        },
    }
    validate(record)


def test_unknown_valid():
    record = {
        **BASE,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "unknown",
            "reason": "insufficient_evidence",
        },
    }
    validate(record)


def test_ambiguous_valid():
    record = {
        **BASE,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "ambiguous",
            "reason": "multiple_plausible_interpretations",
            "candidate_kinds": [
                "Requirement",
                "Constraint",
            ],
        },
    }
    validate(record)


def test_resolved_with_reason_rejected():
    record = {
        **BASE,
        "resolution": {
            "status": "resolved",
            "reason": "unresolved",
        },
    }
    validate_rejected(record)


def test_resolved_with_candidates_rejected():
    record = {
        **BASE,
        "resolution": {
            "status": "resolved",
            "reason": None,
            "candidate_kinds": [
                "Requirement",
                "Constraint",
            ],
        },
    }
    validate_rejected(record)


def test_unknown_non_unclassified_rejected():
    record = {
        **BASE,
        "semantic_kind": "Requirement",
        "resolution": {
            "status": "unknown",
            "reason": "insufficient_evidence",
        },
    }
    validate_rejected(record)


def test_unknown_with_candidates_rejected():
    record = {
        **BASE,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "unknown",
            "reason": "insufficient_evidence",
            "candidate_kinds": [
                "Requirement",
                "Constraint",
            ],
        },
    }
    validate_rejected(record)


def test_ambiguous_non_unclassified_rejected():
    record = {
        **BASE,
        "semantic_kind": "Requirement",
        "resolution": {
            "status": "ambiguous",
            "reason": "multiple_plausible_interpretations",
            "candidate_kinds": [
                "Requirement",
                "Constraint",
            ],
        },
    }
    validate_rejected(record)


def test_ambiguous_wrong_reason_rejected():
    record = {
        **BASE,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "ambiguous",
            "reason": "insufficient_evidence",
            "candidate_kinds": [
                "Requirement",
                "Constraint",
            ],
        },
    }
    validate_rejected(record)


def test_ambiguous_single_candidate_rejected():
    record = {
        **BASE,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "ambiguous",
            "reason": "multiple_plausible_interpretations",
            "candidate_kinds": [
                "Requirement",
            ],
        },
    }
    validate_rejected(record)


def test_unknown_multiple_plausible_interpretations_rejected():
    record = {
        **BASE,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "unknown",
            "reason": "multiple_plausible_interpretations",
        },
    }
    validate_rejected(record)


def test_candidate_kind_outside_vocabulary_rejected():
    record = {
        **BASE,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "ambiguous",
            "reason": "multiple_plausible_interpretations",
            "candidate_kinds": [
                "Requirement",
                "MadeUpCategory",
            ],
        },
    }
    validate_rejected(record)


def test_unknown_no_matching_category_valid():
    record = {
        **BASE,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "unknown",
            "reason": "no_matching_category",
        },
    }
    validate(record)


def test_unknown_context_required_valid():
    record = {
        **BASE,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "unknown",
            "reason": "context_required",
        },
    }
    validate(record)


def test_unknown_unresolved_valid():
    record = {
        **BASE,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "unknown",
            "reason": "unresolved",
        },
    }
    validate(record)

def test_resolved_unclassified_rejected():
    record = {
        **BASE,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "resolved",
            "reason": None,
        },
    }
    validate_rejected(record)


def test_ambiguous_unclassified_candidate_rejected():
    record = {
        **BASE,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "ambiguous",
            "reason": "multiple_plausible_interpretations",
            "candidate_kinds": [
                "Requirement",
                "Unclassified",
            ],
        },
    }
    validate_rejected(record)
