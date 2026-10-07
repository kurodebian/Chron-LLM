import pytest

from tools.validate_dm2 import (
    validate_semantic_extraction,
    validate_semantic_extraction_set,
)



CANONICAL_UNIT = {
    "unit_id": "u0001",
    "line_start": 13,
    "line_end": 15,
    "source_text": "The system SHALL preserve canonical evidence.",
}

RECORD = {
    **CANONICAL_UNIT,
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
    "resolution": {
        "status": "resolved",
        "reason": None,
    },
}


def test_valid_canonical_match():
    validate_semantic_extraction(CANONICAL_UNIT, RECORD)


def test_invalid_unit_id_mismatch():
    record = {**RECORD, "unit_id": "u0002"}

    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


def test_invalid_line_start_mismatch():
    record = {**RECORD, "line_start": 14}

    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


def test_invalid_line_end_mismatch():
    record = {**RECORD, "line_end": 16}

    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


def test_invalid_source_text_mismatch():
    record = {
        **RECORD,
        "source_text": "The system SHALL preserve different evidence.",
    }

    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


def test_record_is_not_repaired():
    record = {
        **RECORD,
        "source_text": "incorrect",
    }
    original = dict(record)

    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)

    assert record == original

def test_invalid_canonical_line_start():
    canonical = {
        **CANONICAL_UNIT,
        "line_start": 0,
    }

    record = {
        **RECORD,
        "line_start": 0,
    }

    with pytest.raises(ValueError):
        validate_semantic_extraction(canonical, record)


def test_invalid_canonical_line_range():
    canonical = {
        **CANONICAL_UNIT,
        "line_start": 15,
        "line_end": 13,
    }

    record = {
        **RECORD,
        "line_start": 15,
        "line_end": 13,
    }

    with pytest.raises(ValueError):
        validate_semantic_extraction(canonical, record)

# ------------------------------------------------------------
# V3 — Evidence / Provenance Integrity
# ------------------------------------------------------------

V3_CANONICAL_UNIT = {
    "unit_id": "u0002",
    "line_start": 13,
    "line_end": 15,
    "source_text": (
        "The system SHALL preserve canonical evidence.\n"
        "The system MUST NOT modify canonical input.\n"
        "Validation MUST be deterministic.\n"
    ),
}

def test_valid_evidence_phrase_exact_substring():
    record = {
        **RECORD,
        "semantic_evidence": {
            "phrases": ["SHALL preserve canonical evidence"],
            "lines": [13],
        },
    }

    validate_semantic_extraction(CANONICAL_UNIT, record)


def test_invalid_evidence_phrase_not_substring():
    record = {
        **RECORD,
        "semantic_evidence": {
            "phrases": ["SHALL preserve different evidence"],
            "lines": [13],
        },
    }

    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


def test_evidence_phrase_is_case_sensitive():
    record = {
        **RECORD,
        "semantic_evidence": {
            "phrases": ["shall preserve canonical evidence"],
            "lines": [13],
        },
    }

    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


def test_evidence_phrase_is_not_normalized():
    record = {
        **RECORD,
        "semantic_evidence": {
            "phrases": ["SHALL  preserve canonical evidence"],
            "lines": [13],
        },
    }

    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


def test_empty_evidence_phrases_are_structurally_valid():
    record = {
        **RECORD,
        "semantic_evidence": {
            "phrases": [],
            "lines": [13],
        },
    }

    validate_semantic_extraction(CANONICAL_UNIT, record)


def test_valid_evidence_line_within_canonical_span():
    record = {
        **RECORD,
        "semantic_evidence": {
            "phrases": ["SHALL preserve canonical evidence"],
            "lines": [14],
        },
    }

    validate_semantic_extraction(CANONICAL_UNIT, record)


def test_invalid_evidence_line_before_canonical_span():
    record = {
        **RECORD,
        "semantic_evidence": {
            "phrases": ["SHALL preserve canonical evidence"],
            "lines": [12],
        },
    }

    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


def test_invalid_evidence_line_after_canonical_span():
    record = {
        **RECORD,
        "semantic_evidence": {
            "phrases": ["SHALL preserve canonical evidence"],
            "lines": [16],
        },
    }

    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


def test_duplicate_evidence_lines_are_rejected():
    record = {
        **RECORD,
        "semantic_evidence": {
            "phrases": ["SHALL preserve canonical evidence"],
            "lines": [13, 13],
        },
    }

    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


def test_phrase_and_line_arrays_have_no_positional_mapping_requirement():
    record = {
        **RECORD,
        "unit_id": "u0002",
        "line_start": 13,
        "line_end": 15,
        "source_text": V3_CANONICAL_UNIT["source_text"],
        "semantic_evidence": {
            "phrases": [
                "The system SHALL preserve canonical evidence.",
                "Validation MUST be deterministic.",
            ],
            "lines": [15],
        },
    }

    validate_semantic_extraction(V3_CANONICAL_UNIT, record)

# ------------------------------------------------------------
# V4 — Semantic Vocabulary Integrity
# ------------------------------------------------------------

VALID_SEMANTIC_KINDS = (
    "Heading",
    "Requirement",
    "Constraint",
    "Definition",
    "Description",
    "Procedure",
    "State",
    "Event",
    "Exception",
    "Unclassified",
)


@pytest.mark.parametrize(
    "semantic_kind",
    VALID_SEMANTIC_KINDS,
)
def test_valid_semantic_kind_is_accepted(semantic_kind):
    record = {
        **RECORD,
        "semantic_kind": semantic_kind,
    }

    # V4 vocabulary acceptance.
    # Resolution is intentionally kept unchanged here because
    # V6 owns resolution/semantic_kind consistency.
    if semantic_kind == "Unclassified":
        record["resolution"] = {
            "status": "unknown",
            "reason": "insufficient_evidence",
        }

    validate_semantic_extraction(CANONICAL_UNIT, record)


@pytest.mark.parametrize(
    "semantic_kind",
    [
        "Unknown",
        "unknown",
        "requirement",
        "REQ",
        "RequirementType",
        "FreeForm",
        "",
    ],
)
def test_invalid_semantic_kind_is_rejected(semantic_kind):
    record = {
        **RECORD,
        "semantic_kind": semantic_kind,
    }

    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


def test_unclassified_is_explicitly_accepted():
    record = {
        **RECORD,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "unknown",
            "reason": "insufficient_evidence",
        },
    }

    validate_semantic_extraction(CANONICAL_UNIT, record)


@pytest.mark.parametrize(
    "semantic_kind",
    [
        "heading",
        "requirement",
        "constraint",
        "definition",
        "description",
        "procedure",
        "state",
        "event",
        "exception",
    ],
)
def test_semantic_kind_alias_or_lowercase_is_rejected(semantic_kind):
    record = {
        **RECORD,
        "semantic_kind": semantic_kind,
    }

    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)

# ------------------------------------------------------------
# V5 — Semantic Attributes Integrity
# ------------------------------------------------------------

VALID_MODALITIES = (
    "must",
    "shall",
    "should",
    "may",
    "cannot",
    "prohibited",
    "required",
    "optional",
    "none",
)

VALID_STRUCTURAL_FORMS = (
    "heading",
    "paragraph",
    "bullet-list",
    "numbered-list",
    "procedure-block",
    "other",
)

VALID_SEMANTIC_STRENGTHS = (
    "strong",
    "weak",
    "descriptive",
    "definitional",
    "none",
)

VALID_SEMANTIC_SCOPES = (
    "global",
    "system-wide",
    "component-specific",
    "local",
    "unspecified",
)


@pytest.mark.parametrize("modality", VALID_MODALITIES)
def test_valid_modality_is_accepted(modality):
    record = {
        **RECORD,
        "semantic_attributes": {
            **RECORD["semantic_attributes"],
            "modality": modality,
        },
    }
    validate_semantic_extraction(CANONICAL_UNIT, record)


@pytest.mark.parametrize(
    "modality",
    [
        "Must",
        "SHALL",
        "should-not",
        "required_by_system",
        "unknown",
        "",
    ],
)
def test_invalid_modality_is_rejected(modality):
    record = {
        **RECORD,
        "semantic_attributes": {
            **RECORD["semantic_attributes"],
            "modality": modality,
        },
    }
    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


@pytest.mark.parametrize("structural_form", VALID_STRUCTURAL_FORMS)
def test_valid_structural_form_is_accepted(structural_form):
    record = {
        **RECORD,
        "semantic_attributes": {
            **RECORD["semantic_attributes"],
            "structural_form": structural_form,
        },
    }
    validate_semantic_extraction(CANONICAL_UNIT, record)


@pytest.mark.parametrize(
    "structural_form",
    [
        "Heading",
        "Paragraph",
        "bullet_list",
        "number-list",
        "procedure",
        "unknown",
        "",
    ],
)
def test_invalid_structural_form_is_rejected(structural_form):
    record = {
        **RECORD,
        "semantic_attributes": {
            **RECORD["semantic_attributes"],
            "structural_form": structural_form,
        },
    }
    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


@pytest.mark.parametrize("semantic_strength", VALID_SEMANTIC_STRENGTHS)
def test_valid_semantic_strength_is_accepted(semantic_strength):
    record = {
        **RECORD,
        "semantic_attributes": {
            **RECORD["semantic_attributes"],
            "semantic_strength": semantic_strength,
        },
    }
    validate_semantic_extraction(CANONICAL_UNIT, record)


@pytest.mark.parametrize(
    "semantic_strength",
    [
        "Strong",
        "WEAK",
        "descriptive_strength",
        "definition",
        "unknown",
        "",
    ],
)
def test_invalid_semantic_strength_is_rejected(semantic_strength):
    record = {
        **RECORD,
        "semantic_attributes": {
            **RECORD["semantic_attributes"],
            "semantic_strength": semantic_strength,
        },
    }
    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


@pytest.mark.parametrize("semantic_scope", VALID_SEMANTIC_SCOPES)
def test_valid_semantic_scope_is_accepted(semantic_scope):
    record = {
        **RECORD,
        "semantic_attributes": {
            **RECORD["semantic_attributes"],
            "semantic_scope": semantic_scope,
        },
    }
    validate_semantic_extraction(CANONICAL_UNIT, record)


@pytest.mark.parametrize(
    "semantic_scope",
    [
        "Global",
        "SYSTEM-WIDE",
        "system_wide",
        "component",
        "component-wide",
        "unknown",
        "",
    ],
)
def test_invalid_semantic_scope_is_rejected(semantic_scope):
    record = {
        **RECORD,
        "semantic_attributes": {
            **RECORD["semantic_attributes"],
            "semantic_scope": semantic_scope,
        },
    }
    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)

# ------------------------------------------------------------
# V6 — Unknown / Ambiguous Integrity
# ------------------------------------------------------------

VALID_UNKNOWN_REASONS = (
    "insufficient_evidence",
    "no_matching_category",
    "context_required",
    "unresolved",
)

CLASSIFIED_SEMANTIC_KINDS = (
    "Heading",
    "Requirement",
    "Constraint",
    "Definition",
    "Description",
    "Procedure",
    "State",
    "Event",
    "Exception",
)


@pytest.mark.parametrize("reason", VALID_UNKNOWN_REASONS)
def test_valid_unknown_resolution_is_accepted(reason):
    record = {
        **RECORD,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "unknown",
            "reason": reason,
        },
    }
    validate_semantic_extraction(CANONICAL_UNIT, record)


@pytest.mark.parametrize(
    "reason",
    [
        None,
        "multiple_plausible_interpretations",
        "Unknown",
        "INSUFFICIENT_EVIDENCE",
        "",
        "free_form_reason",
    ],
)
def test_invalid_unknown_reason_is_rejected(reason):
    record = {
        **RECORD,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "unknown",
            "reason": reason,
        },
    }
    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


def test_unknown_requires_unclassified_semantic_kind():
    record = {
        **RECORD,
        "semantic_kind": "Requirement",
        "resolution": {
            "status": "unknown",
            "reason": "insufficient_evidence",
        },
    }
    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


def test_unknown_forbids_candidate_kinds():
    record = {
        **RECORD,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "unknown",
            "reason": "insufficient_evidence",
            "candidate_kinds": ["Requirement", "Constraint"],
        },
    }
    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


def test_valid_ambiguous_resolution_is_accepted():
    record = {
        **RECORD,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "ambiguous",
            "reason": "multiple_plausible_interpretations",
            "candidate_kinds": ["Requirement", "Constraint"],
        },
    }
    validate_semantic_extraction(CANONICAL_UNIT, record)


@pytest.mark.parametrize(
    "candidate_kinds",
    [
        [],
        ["Requirement"],
        ["Requirement", "Requirement"],
        ["Requirement", "Unclassified"],
        ["Requirement", "unknown"],
        ["Requirement", "FreeForm"],
    ],
)
def test_invalid_ambiguous_candidate_kinds_are_rejected(candidate_kinds):
    record = {
        **RECORD,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "ambiguous",
            "reason": "multiple_plausible_interpretations",
            "candidate_kinds": candidate_kinds,
        },
    }
    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


@pytest.mark.parametrize(
    "reason",
    [
        None,
        "insufficient_evidence",
        "unresolved",
        "free_form_reason",
    ],
)
def test_invalid_ambiguous_reason_is_rejected(reason):
    record = {
        **RECORD,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "ambiguous",
            "reason": reason,
            "candidate_kinds": ["Requirement", "Constraint"],
        },
    }
    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


def test_ambiguous_requires_unclassified_semantic_kind():
    record = {
        **RECORD,
        "semantic_kind": "Requirement",
        "resolution": {
            "status": "ambiguous",
            "reason": "multiple_plausible_interpretations",
            "candidate_kinds": ["Requirement", "Constraint"],
        },
    }
    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


@pytest.mark.parametrize(
    "resolution",
    [
        {"status": "unknown", "reason": "insufficient_evidence",
         "candidate_kinds": ["Requirement"]},
        {"status": "ambiguous", "reason": "multiple_plausible_interpretations"},
        {"status": "resolved", "reason": None,
         "candidate_kinds": ["Requirement"]},
        {"status": "invalid_status", "reason": None},
        {"status": "resolved", "reason": "unresolved"},
    ],
)
def test_invalid_resolution_structure_is_rejected(resolution):
    record = {
        **RECORD,
        "resolution": resolution,
    }
    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


@pytest.mark.parametrize("semantic_kind", CLASSIFIED_SEMANTIC_KINDS)
def test_resolved_classified_kind_is_accepted(semantic_kind):
    record = {
        **RECORD,
        "semantic_kind": semantic_kind,
        "resolution": {
            "status": "resolved",
            "reason": None,
        },
    }
    validate_semantic_extraction(CANONICAL_UNIT, record)


def test_resolved_unclassified_is_rejected():
    record = {
        **RECORD,
        "semantic_kind": "Unclassified",
        "resolution": {
            "status": "resolved",
            "reason": None,
        },
    }
    with pytest.raises(ValueError):
        validate_semantic_extraction(CANONICAL_UNIT, record)


# ---------------------------------------------------------------------------
# V7: Boundary Integrity
# ---------------------------------------------------------------------------

def test_v7_one_to_one_mapping_passes():
    validate_semantic_extraction_set(
        [CANONICAL_UNIT],
        [RECORD],
    )


def test_v7_split_duplicate_unit_is_rejected():
    record2 = {**RECORD}

    with pytest.raises(ValueError, match="V7"):
        validate_semantic_extraction_set(
            [CANONICAL_UNIT],
            [RECORD, record2],
        )


def test_v7_missing_record_is_rejected():
    canonical_unit_2 = {
        "unit_id": "u0002",
        "line_start": 16,
        "line_end": 18,
        "source_text": "Another canonical unit.",
    }

    with pytest.raises(ValueError, match="V7"):
        validate_semantic_extraction_set(
            [CANONICAL_UNIT, canonical_unit_2],
            [RECORD],
        )


def test_v7_unknown_record_unit_is_rejected():
    record2 = {**RECORD, "unit_id": "u0099"}

    with pytest.raises(ValueError, match="V7"):
        validate_semantic_extraction_set(
            [CANONICAL_UNIT],
            [record2],
        )


def test_v7_duplicate_canonical_unit_is_rejected():
    with pytest.raises(ValueError, match="V7"):
        validate_semantic_extraction_set(
            [CANONICAL_UNIT, CANONICAL_UNIT],
            [RECORD],
        )


def test_v7_duplicate_record_unit_is_rejected():
    record2 = {**RECORD}

    with pytest.raises(ValueError, match="V7"):
        validate_semantic_extraction_set(
            [CANONICAL_UNIT],
            [RECORD, record2],
        )


def test_v7_existing_v2_v6_validation_is_delegated():
    invalid_record = {
        **RECORD,
        "semantic_kind": "INVALID",
    }

    with pytest.raises(ValueError, match="V4"):
        validate_semantic_extraction_set(
            [CANONICAL_UNIT],
            [invalid_record],
        )

# ---------------------------------------------------------------------------
# V8: Forbidden Content Integrity
# ---------------------------------------------------------------------------

FORBIDDEN_DM2_FIELDS = (
    "claims",
    "entities",
    "actions",
    "conditions",
    "causes",
    "effects",
    "dependencies",
    "triggers",
    "mutations",
    "transitions",
    "causal_relations",
    "causal_confidence",
    "edges",
    "graph",
)


@pytest.mark.parametrize(
    "forbidden_field",
    FORBIDDEN_DM2_FIELDS,
)
def test_v8_forbidden_top_level_field_is_rejected(
    forbidden_field,
):
    record = {
        **RECORD,
        forbidden_field: [],
    }

    with pytest.raises(ValueError, match="V8"):
        validate_semantic_extraction(
            CANONICAL_UNIT,
            record,
        )


def test_v8_record_without_forbidden_fields_is_valid():
    validate_semantic_extraction(
        CANONICAL_UNIT,
        RECORD,
    )


def test_v8_forbidden_field_is_not_silently_removed():
    record = {
        **RECORD,
        "causes": ["u0002"],
    }

    with pytest.raises(ValueError, match="V8"):
        validate_semantic_extraction(
            CANONICAL_UNIT,
            record,
        )

    assert "causes" in record
    assert record["causes"] == ["u0002"]


def test_v8_causal_relation_is_rejected():
    record = {
        **RECORD,
        "causal_relations": [
            {
                "relation": "causes",
                "target": "u0002",
            }
        ],
    }

    with pytest.raises(ValueError, match="V8"):
        validate_semantic_extraction(
            CANONICAL_UNIT,
            record,
        )


def test_v8_graph_structure_is_rejected():
    record = {
        **RECORD,
        "graph": {
            "nodes": ["u0001"],
            "edges": [],
        },
    }

    with pytest.raises(ValueError, match="V8"):
        validate_semantic_extraction(
            CANONICAL_UNIT,
            record,
        )

# ---------------------------------------------------------------------------
# V0: Record Transport / JSON Validity
# ---------------------------------------------------------------------------

from tools.validate_dm2 import (
    validate_semantic_extraction_json,
)


def test_v0_valid_json_object_is_accepted():
    import json

    raw = json.dumps(RECORD)

    validate_semantic_extraction_json(
        CANONICAL_UNIT,
        raw,
    )


@pytest.mark.parametrize(
    "raw",
    [
        '{"unit_id": "u0001",',
        '{"unit_id": "u0001", "line_start": 13',
        '{"unit_id": "u0001", "line_start": }',
        'not-json',
        '',
    ],
)
def test_v0_malformed_json_is_rejected(raw):
    with pytest.raises(ValueError, match="V0"):
        validate_semantic_extraction_json(
            CANONICAL_UNIT,
            raw,
        )


def test_v0_non_object_root_is_rejected():
    raw = '["not", "an", "object"]'

    with pytest.raises(ValueError, match="V0"):
        validate_semantic_extraction_json(
            CANONICAL_UNIT,
            raw,
        )


def test_v0_duplicate_json_keys_are_rejected():
    raw = (
        '{"unit_id":"u0001",'
        '"unit_id":"u0002",'
        '"line_start":13,'
        '"line_end":15,'
        '"source_text":"The system SHALL preserve canonical evidence.",'
        '"semantic_kind":"Requirement",'
        '"semantic_evidence":{"phrases":["SHALL preserve canonical evidence"],"lines":[13]},'
        '"semantic_attributes":{"modality":"shall","structural_form":"paragraph",'
        '"semantic_strength":"strong","semantic_scope":"system-wide"},'
        '"resolution":{"status":"resolved","reason":null}}'
    )

    with pytest.raises(ValueError, match="V0"):
        validate_semantic_extraction_json(
            CANONICAL_UNIT,
            raw,
        )


# ---------------------------------------------------------------------------
# V1: Schema Validity
# ---------------------------------------------------------------------------

def test_v1_schema_valid_record_is_accepted():
    import json

    raw = json.dumps(RECORD)

    validate_semantic_extraction_json(
        CANONICAL_UNIT,
        raw,
    )


@pytest.mark.parametrize(
    "mutator",
    [
        lambda r: r.pop("unit_id"),
        lambda r: r.__setitem__("unit_id", "invalid"),
        lambda r: r.__setitem__("semantic_kind", "INVALID"),
        lambda r: r.__setitem__("unexpected", "forbidden"),
        lambda r: r.__setitem__("line_start", "13"),
        lambda r: r.__setitem__("semantic_evidence", {}),
        lambda r: r.__setitem__(
            "semantic_attributes",
            {
                "modality": "shall",
                "structural_form": "paragraph",
                "semantic_strength": "strong",
                "semantic_scope": "system-wide",
                "extra": "forbidden",
            },
        ),
    ],
)
def test_v1_schema_invalid_record_is_rejected(mutator):
    import json

    record = dict(RECORD)
    mutator(record)
    raw = json.dumps(record)

    with pytest.raises(ValueError, match="V1"):
        validate_semantic_extraction_json(
            CANONICAL_UNIT,
            raw,
        )


def test_v1_schema_rejects_unknown_top_level_field():
    import json

    record = {
        **RECORD,
        "claims": [],
    }

    raw = json.dumps(record)

    with pytest.raises(ValueError, match="V1"):
        validate_semantic_extraction_json(
            CANONICAL_UNIT,
            raw,
        )


def test_v1_schema_failure_does_not_repair_input():
    import json

    record = {
        **RECORD,
        "semantic_kind": "INVALID",
    }
    raw = json.dumps(record)

    with pytest.raises(ValueError, match="V1"):
        validate_semantic_extraction_json(
            CANONICAL_UNIT,
            raw,
        )

    assert json.loads(raw) == record
