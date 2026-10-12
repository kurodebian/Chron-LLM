"""Characterization tests for the draft A1A-SCA JSON Schema.

These tests validate the current schema behavior only. They do not implement
semantic classification or the deterministic report validator.
"""

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "a1a_semantic_coverage_audit.schema.json"


def load_validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


BASE_COMPLETED = {
    "audit_version": "A1A-SCA.0.1",
    "document_id": "test-document",
    "source_digest": "a" * 64,
    "artifact_digest": "b" * 64,
    "status": "COMPLETED",
    "findings": [
        {
            "finding_id": "F0001",
            "classification": "STRUCTURAL_GAP",
            "source_line_start": 10,
            "source_line_end": 10,
            "covered_by_units": ["u0001"],
            "evidence": "Source line 10 contains a heading.",
            "reason": "The heading line is not covered by an existing unit.",
            "confidence": "MEDIUM",
            "review_required": True,
        }
    ],
    "summary": {
        "finding_count": 1,
        "by_classification": {
            "NON_SEMANTIC_GAP": 0,
            "STRUCTURAL_GAP": 1,
            "WHOLE_UNIT_OMISSION": 0,
            "PARTIAL_UNIT_OMISSION": 0,
            "AMBIGUOUS": 0,
        },
    },
}


def schema_errors(report):
    return list(load_validator().iter_errors(report))


def assert_schema_accepts(report):
    errors = schema_errors(report)
    assert not errors, "\n".join(
        f"{error.json_path}: {error.message}" for error in errors
    )


def assert_schema_rejects(report):
    errors = schema_errors(report)
    assert errors, "Expected JSON Schema rejection"


def test_schema_is_valid_draft_2020_12():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(schema)


def test_valid_completed_report_is_accepted():
    assert_schema_accepts(copy.deepcopy(BASE_COMPLETED))


def test_failed_report_without_input_digests_is_accepted():
    # A failed report may omit identity fields when an input cannot be read.
    report = {
        "status": "INPUT_INVALID",
        "error": {
            "code": "ARTIFACT_UNREADABLE",
            "message": "Artifact bytes could not be read.",
        },
    }
    assert_schema_accepts(report)


def test_invalid_classification_is_rejected():
    report = copy.deepcopy(BASE_COMPLETED)
    report["findings"][0]["classification"] = "MADE_UP_CLASSIFICATION"
    assert_schema_rejects(report)


def test_invalid_confidence_is_rejected():
    report = copy.deepcopy(BASE_COMPLETED)
    report["findings"][0]["confidence"] = "CERTAIN"
    assert_schema_rejects(report)


def test_unknown_top_level_property_is_rejected():
    report = copy.deepcopy(BASE_COMPLETED)
    report["unexpected"] = True
    assert_schema_rejects(report)


def test_reversed_line_range_is_not_rejected_by_schema_alone():
    # Characterizes a cross-field constraint delegated to a deterministic
    # validator; this is not a claim that the report is semantically valid.
    report = copy.deepcopy(BASE_COMPLETED)
    report["findings"][0]["source_line_start"] = 11
    report["findings"][0]["source_line_end"] = 10
    assert_schema_accepts(report)


def test_summary_count_mismatch_is_not_rejected_by_schema_alone():
    # Characterizes the need to compare summary fields with actual findings.
    report = copy.deepcopy(BASE_COMPLETED)
    report["summary"]["finding_count"] = 99
    assert_schema_accepts(report)


def test_summary_classification_mismatch_is_not_rejected_by_schema_alone():
    report = copy.deepcopy(BASE_COMPLETED)
    report["summary"]["by_classification"]["STRUCTURAL_GAP"] = 0
    assert_schema_accepts(report)


def test_failed_report_rejects_unknown_error_property():
    report = {
        "status": "AUDIT_FAILED",
        "error": {
            "code": "AUDIT_EXCEPTION",
            "message": "Audit failed.",
            "debug_object": {"unsafe": True},
        },
    }
    assert_schema_rejects(report)
