#!/usr/bin/env python3
# tools/validate_dm2.py

"""
DM-2-6 Semantic Extraction Validation.
"""

import json
from pathlib import Path

from jsonschema import Draft202012Validator


SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "dm2-semantic-extraction-record-v2.schema.json"
)

"""
DM-2-6 Semantic Extraction Validation.

Current implementation scope:
    V2: Canonical Identity / Span Integrity

The validator does not repair, normalize, sort, mutate, or otherwise
modify the canonical unit or semantic extraction record.
"""


CANONICAL_FIELDS = (
    "unit_id",
    "line_start",
    "line_end",
    "source_text",
)

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

# ------------------------------------------------------------
# V6 — Unknown / Ambiguous Integrity
# ------------------------------------------------------------

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

VALID_UNKNOWN_REASONS = (
    "insufficient_evidence",
    "no_matching_category",
    "context_required",
    "unresolved",
)

VALID_RESOLUTION_STATUSES = (
    "resolved",
    "unknown",
    "ambiguous",
)

# ------------------------------------------------------------
# V0 / V1 — Record Transport / Schema Validity
# ------------------------------------------------------------

def _reject_duplicate_json_keys(pairs):
    result = {}

    for key, value in pairs:
        if key in result:
            raise ValueError(
                "INVALID_DM2: V0 duplicate JSON key: "
                f"{key!r}"
            )
        result[key] = value

    return result


def validate_semantic_extraction_json(
    canonical_unit: dict,
    raw_record: str,
) -> None:
    """
    Validate a raw DM-2 semantic extraction JSON record.

    Validation order:
        V0 — JSON transport validity
        V1 — DM-2 v2 schema validity
        V2-V8 — semantic extraction validation

    Invalid input is rejected.
    No input is repaired or modified.
    """

    # --------------------------------------------------------
    # V0 — Record Transport / JSON Validity
    # --------------------------------------------------------

    if not isinstance(raw_record, str):
        raise ValueError(
            "INVALID_DM2: V0 raw_record must be a JSON string"
        )

    try:
        record = json.loads(
            raw_record,
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(
            "INVALID_DM2: V0 invalid JSON: "
            f"{exc}"
        ) from exc

    if not isinstance(record, dict):
        raise ValueError(
            "INVALID_DM2: V0 JSON root must be an object"
        )

    # --------------------------------------------------------
    # V1 — Schema Validity
    # --------------------------------------------------------

    try:
        schema = json.loads(
            SCHEMA_PATH.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "DM2 schema could not be loaded: "
            f"{exc}"
        ) from exc

    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: list(error.absolute_path),
    )

    if errors:
        error = errors[0]

        path = "".join(
            f"[{part!r}]"
            if isinstance(part, int)
            else f".{part}"
            for part in error.absolute_path
        )

        raise ValueError(
            "INVALID_DM2: V1 schema validation failed"
            f"{path}: {error.message}"
        )

    # --------------------------------------------------------
    # V2-V8
    # --------------------------------------------------------

    validate_semantic_extraction(
        canonical_unit,
        record,
    )
    
def validate_semantic_extraction(
    canonical_unit: dict,
    record: dict,
) -> None:
    """
    Validate the DM-2 semantic extraction record against its
    A-1a canonical unit.

    V2 requires:
        - canonical span validity:
            line_start >= 1
            line_end >= line_start
        - exact equality for:
            unit_id
            line_start
            line_end
            source_text

    Invalid input is rejected with ValueError.
    No input object is modified.
    """

    if not isinstance(canonical_unit, dict):
        raise ValueError(
            "INVALID_DM2: canonical_unit must be an object"
        )

    if not isinstance(record, dict):
        raise ValueError(
            "INVALID_DM2: record must be an object"
        )

    for field in CANONICAL_FIELDS:
        if field not in canonical_unit:
            raise ValueError(
                f"INVALID_DM2: canonical_unit missing field {field!r}"
            )

        if field not in record:
            raise ValueError(
                f"INVALID_DM2: record missing field {field!r}"
            )

    # ------------------------------------------------------------
    # V2 — Canonical Span Validity
    # ------------------------------------------------------------

    canonical_line_start = canonical_unit["line_start"]
    canonical_line_end = canonical_unit["line_end"]

    if (
        not isinstance(canonical_line_start, int)
        or isinstance(canonical_line_start, bool)
    ):
        raise ValueError(
            "INVALID_DM2: V2 canonical line_start must be an integer"
        )

    if (
        not isinstance(canonical_line_end, int)
        or isinstance(canonical_line_end, bool)
    ):
        raise ValueError(
            "INVALID_DM2: V2 canonical line_end must be an integer"
        )

    if canonical_line_start < 1:
        raise ValueError(
            "INVALID_DM2: V2 canonical line_start < 1"
        )

    if canonical_line_end < canonical_line_start:
        raise ValueError(
            "INVALID_DM2: V2 canonical line_end < line_start"
        )

    # ------------------------------------------------------------
    # V2 — Canonical Identity / Span Equality
    # ------------------------------------------------------------

    for field in CANONICAL_FIELDS:
        if record[field] != canonical_unit[field]:
            raise ValueError(
                f"INVALID_DM2: V2 canonical mismatch "
                f"at {field}: "
                f"observed={record[field]!r}, "
                f"expected={canonical_unit[field]!r}"
            )

    # ------------------------------------------------------------
    # V3 — Evidence / Provenance Integrity
    # ------------------------------------------------------------

    evidence = record["semantic_evidence"]

    for phrase in evidence["phrases"]:
        if phrase not in record["source_text"]:
            raise ValueError(
                "INVALID_DM2: V3 evidence phrase is not an "
                "exact substring of source_text: "
                f"{phrase!r}"
            )

    line_start = canonical_unit["line_start"]
    line_end = canonical_unit["line_end"]

    for evidence_line in evidence["lines"]:
        if not (
            line_start <= evidence_line <= line_end
        ):
            raise ValueError(
                "INVALID_DM2: V3 evidence line is outside "
                "canonical span: "
                f"{evidence_line}"
            )

    if len(evidence["lines"]) != len(set(evidence["lines"])):
        raise ValueError(
            "INVALID_DM2: V3 duplicate evidence line"
        )


    # ------------------------------------------------------------
    # V4 — Semantic Vocabulary Integrity
    # ------------------------------------------------------------

    semantic_kind = record["semantic_kind"]

    if semantic_kind not in VALID_SEMANTIC_KINDS:
        raise ValueError(
            "INVALID_DM2: V4 invalid semantic_kind: "
            f"{semantic_kind!r}"
        )

    # ------------------------------------------------------------
    # V5 — Semantic Attributes Integrity
    # ------------------------------------------------------------
    semantic_attributes = record["semantic_attributes"]

    if not isinstance(semantic_attributes, dict):
        raise ValueError(
            "INVALID_DM2: V5 semantic_attributes must be an object"
        )

    if set(semantic_attributes.keys()) != {
        "modality",
        "structural_form",
        "semantic_strength",
        "semantic_scope",
    }:
        raise ValueError(
            "INVALID_DM2: V5 semantic_attributes contains "
            "unexpected or missing fields"
        )

    modality = semantic_attributes["modality"]
    if modality not in VALID_MODALITIES:
        raise ValueError(
            "INVALID_DM2: V5 invalid modality: "
            f"{modality!r}"
        )

    structural_form = semantic_attributes["structural_form"]
    if structural_form not in VALID_STRUCTURAL_FORMS:
        raise ValueError(
            "INVALID_DM2: V5 invalid structural_form: "
            f"{structural_form!r}"
        )

    semantic_strength = semantic_attributes["semantic_strength"]
    if semantic_strength not in VALID_SEMANTIC_STRENGTHS:
        raise ValueError(
            "INVALID_DM2: V5 invalid semantic_strength: "
            f"{semantic_strength!r}"
        )

    semantic_scope = semantic_attributes["semantic_scope"]
    if semantic_scope not in VALID_SEMANTIC_SCOPES:
        raise ValueError(
            "INVALID_DM2: V5 invalid semantic_scope: "
            f"{semantic_scope!r}"
        )

    # ------------------------------------------------------------
    # V6 — Unknown / Ambiguous Integrity
    # ------------------------------------------------------------
    resolution = record["resolution"]

    if not isinstance(resolution, dict):
        raise ValueError(
            "INVALID_DM2: V6 resolution must be an object"
        )

    status = resolution.get("status")
    reason = resolution.get("reason")

    if status not in VALID_RESOLUTION_STATUSES:
        raise ValueError(
            "INVALID_DM2: V6 invalid resolution status: "
            f"{status!r}"
        )

    allowed_resolution_fields = {"status", "reason", "candidate_kinds"}
    if set(resolution.keys()) - allowed_resolution_fields:
        raise ValueError(
            "INVALID_DM2: V6 resolution contains "
            "unexpected fields"
        )

    semantic_kind = record["semantic_kind"]

    # --------------------------------------------------------
    # resolved
    # --------------------------------------------------------
    if status == "resolved":
        if semantic_kind not in CLASSIFIED_SEMANTIC_KINDS:
            raise ValueError(
                "INVALID_DM2: V6 resolved requires a classified "
                f"semantic_kind, got {semantic_kind!r}"
            )

        if reason is not None:
            raise ValueError(
                "INVALID_DM2: V6 resolved requires reason=null"
            )

        if "candidate_kinds" in resolution:
            raise ValueError(
                "INVALID_DM2: V6 resolved forbids candidate_kinds"
            )

    # --------------------------------------------------------
    # unknown
    # --------------------------------------------------------
    elif status == "unknown":
        if semantic_kind != "Unclassified":
            raise ValueError(
                "INVALID_DM2: V6 unknown requires "
                "semantic_kind=Unclassified"
            )

        if reason not in VALID_UNKNOWN_REASONS:
            raise ValueError(
                "INVALID_DM2: V6 invalid unknown reason: "
                f"{reason!r}"
            )

        if "candidate_kinds" in resolution:
            raise ValueError(
                "INVALID_DM2: V6 unknown forbids candidate_kinds"
            )

    # --------------------------------------------------------
    # ambiguous
    # --------------------------------------------------------
    elif status == "ambiguous":
        if semantic_kind != "Unclassified":
            raise ValueError(
                "INVALID_DM2: V6 ambiguous requires "
                "semantic_kind=Unclassified"
            )

        if reason != "multiple_plausible_interpretations":
            raise ValueError(
                "INVALID_DM2: V6 ambiguous requires "
                "reason=multiple_plausible_interpretations"
            )

        if "candidate_kinds" not in resolution:
            raise ValueError(
                "INVALID_DM2: V6 ambiguous requires "
                "candidate_kinds"
            )

        candidate_kinds = resolution["candidate_kinds"]

        if not isinstance(candidate_kinds, list):
            raise ValueError(
                "INVALID_DM2: V6 candidate_kinds must be an array"
            )

        if len(candidate_kinds) < 2:
            raise ValueError(
                "INVALID_DM2: V6 ambiguous requires at least "
                "two candidate_kinds"
            )

        if len(candidate_kinds) != len(set(candidate_kinds)):
            raise ValueError(
                "INVALID_DM2: V6 candidate_kinds must be unique"
            )

        for candidate_kind in candidate_kinds:
            if candidate_kind not in CLASSIFIED_SEMANTIC_KINDS:
                raise ValueError(
                    "INVALID_DM2: V6 invalid candidate_kind: "
                    f"{candidate_kind!r}"
                )
    # ------------------------------------------------------------
    # V8 — Forbidden Content Integrity
    # ------------------------------------------------------------

    forbidden_fields = {
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
    }

    present_forbidden_fields = (
        set(record.keys()) & forbidden_fields
    )

    if present_forbidden_fields:
        raise ValueError(
            "INVALID_DM2: V8 forbidden fields present: "
            f"{sorted(present_forbidden_fields)!r}"
        )

def validate_semantic_extraction_set(
    canonical_units: list[dict],
    records: list[dict],
) -> None:
    """
    Validate the one-to-one relationship between A-1a canonical
    units and DM-2 semantic extraction records.

    V7 requires:
        - exactly one record per canonical unit
        - no canonical unit is omitted
        - no canonical unit is duplicated
        - no record refers to an unknown canonical unit
        - no split of one canonical unit into multiple records
        - no merge of multiple canonical units into one record

    Existing V2-V6 validation is delegated to
    validate_semantic_extraction().
    """

    if not isinstance(canonical_units, list):
        raise ValueError(
            "INVALID_DM2: V7 canonical_units must be an array"
        )

    if not isinstance(records, list):
        raise ValueError(
            "INVALID_DM2: V7 records must be an array"
        )

    canonical_ids = []

    for canonical_unit in canonical_units:
        if not isinstance(canonical_unit, dict):
            raise ValueError(
                "INVALID_DM2: V7 canonical unit must be an object"
            )

        if "unit_id" not in canonical_unit:
            raise ValueError(
                "INVALID_DM2: V7 canonical unit missing unit_id"
            )

        unit_id = canonical_unit["unit_id"]

        if unit_id in canonical_ids:
            raise ValueError(
                "INVALID_DM2: V7 duplicate canonical unit_id: "
                f"{unit_id!r}"
            )

        canonical_ids.append(unit_id)

    record_ids = []

    for record in records:
        if not isinstance(record, dict):
            raise ValueError(
                "INVALID_DM2: V7 record must be an object"
            )

        if "unit_id" not in record:
            raise ValueError(
                "INVALID_DM2: V7 record missing unit_id"
            )

        unit_id = record["unit_id"]

        if unit_id in record_ids:
            raise ValueError(
                "INVALID_DM2: V7 duplicate record unit_id: "
                f"{unit_id!r}"
            )

        record_ids.append(unit_id)

    canonical_id_set = set(canonical_ids)
    record_id_set = set(record_ids)

    unknown_record_ids = record_id_set - canonical_id_set

    if unknown_record_ids:
        raise ValueError(
            "INVALID_DM2: V7 record refers to unknown "
            "canonical unit_id: "
            f"{sorted(unknown_record_ids)!r}"
        )

    missing_record_ids = canonical_id_set - record_id_set

    if missing_record_ids:
        raise ValueError(
            "INVALID_DM2: V7 canonical unit has no semantic "
            "record: "
            f"{sorted(missing_record_ids)!r}"
        )

    if len(records) != len(canonical_units):
        raise ValueError(
            "INVALID_DM2: V7 canonical unit / semantic record "
            "count mismatch: "
            f"canonical_units={len(canonical_units)}, "
            f"records={len(records)}"
        )

    canonical_by_id = {
        unit["unit_id"]: unit
        for unit in canonical_units
    }

    for record in records:
        unit_id = record["unit_id"]

        validate_semantic_extraction(
            canonical_by_id[unit_id],
            record,
        )