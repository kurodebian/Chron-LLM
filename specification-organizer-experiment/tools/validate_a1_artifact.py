#!/usr/bin/env python3
# tools/validate_a1_artifact.py

import json
import re


REQUIRED_ROOT_FIELDS = {
    "document_path",
    "units",
}

REQUIRED_UNIT_FIELDS = {
    "unit_id",
    "line_start",
    "line_end",
    "source_text",
}

FORBIDDEN_FIELDS = {
    "semantic_kind",
    "node_type",
    "causal_role",
    "normative_role",
    "state_role",
    "transition_role",
    "event_role",
    "relation_kind",
    "edges",
    "graph",
}

UNIT_ID_PATTERN = re.compile(r"^u\d{4}$")


def load_source(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.readlines()


def validate_units_json(units_json_path: str) -> None:
    """
    A-1a-V2: Artifact Validation.

    Validate semantic_units/*.units.json against the A-1.1
    canonical semantic-unit artifact contract.

    This validator validates.
    It does not repair, normalize, sort, or mutate the artifact.
    """

    with open(units_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ------------------------------------------------------------
    # Root structure
    # ------------------------------------------------------------

    if not isinstance(data, dict):
        raise ValueError(
            "INVALID_ARTIFACT: root must be an object"
        )

    if set(data.keys()) != REQUIRED_ROOT_FIELDS:
        raise ValueError(
            "INVALID_ARTIFACT: unexpected root fields"
        )

    document_path = data["document_path"]
    units = data["units"]

    if not isinstance(document_path, str):
        raise ValueError(
            "INVALID_ARTIFACT: document_path must be a string"
        )

    if not isinstance(units, list):
        raise ValueError(
            "INVALID_ARTIFACT: units must be an array"
        )

    # ------------------------------------------------------------
    # Original source
    # ------------------------------------------------------------

    original_lines = load_source(document_path)
    line_count = len(original_lines)

    # ------------------------------------------------------------
    # Unit validation
    # ------------------------------------------------------------

    seen_ids: set[str] = set()
    previous_start = 0
    previous_end = 0

    for index, unit in enumerate(units):

        if not isinstance(unit, dict):
            raise ValueError(
                f"INVALID_ARTIFACT: unit[{index}] must be an object"
            )

        # Explicit forbidden-field audit
        forbidden_present = FORBIDDEN_FIELDS.intersection(unit.keys())
        if forbidden_present:
            fields = ", ".join(sorted(forbidden_present))
            raise ValueError(
                f"INVALID_ARTIFACT: forbidden fields present: {fields}"
            )

        # Exact canonical unit structure
        if set(unit.keys()) != REQUIRED_UNIT_FIELDS:
            raise ValueError(
                f"INVALID_ARTIFACT: unit[{index}] has unexpected fields"
            )

        unit_id = unit["unit_id"]
        line_start = unit["line_start"]
        line_end = unit["line_end"]
        source_text = unit["source_text"]

        # --------------------------------------------------------
        # Types
        # --------------------------------------------------------

        if not isinstance(unit_id, str):
            raise ValueError(
                f"INVALID_ARTIFACT: unit[{index}].unit_id "
                "must be a string"
            )

        if not UNIT_ID_PATTERN.fullmatch(unit_id):
            raise ValueError(
                f"INVALID_ARTIFACT: invalid unit_id {unit_id!r}"
            )

        if (
            not isinstance(line_start, int)
            or isinstance(line_start, bool)
        ):
            raise ValueError(
                f"INVALID_ARTIFACT: {unit_id}.line_start "
                "must be an integer"
            )

        if (
            not isinstance(line_end, int)
            or isinstance(line_end, bool)
        ):
            raise ValueError(
                f"INVALID_ARTIFACT: {unit_id}.line_end "
                "must be an integer"
            )

        if not isinstance(source_text, str):
            raise ValueError(
                f"INVALID_ARTIFACT: {unit_id}.source_text "
                "must be a string"
            )

        # --------------------------------------------------------
        # Unit ID uniqueness
        # --------------------------------------------------------

        if unit_id in seen_ids:
            raise ValueError(
                f"INVALID_ARTIFACT: duplicate unit_id {unit_id}"
            )

        seen_ids.add(unit_id)

        # --------------------------------------------------------
        # Line span validity
        # --------------------------------------------------------

        if line_start < 1:
            raise ValueError(
                f"INVALID_ARTIFACT: {unit_id}.line_start < 1"
            )

        if line_end < line_start:
            raise ValueError(
                f"INVALID_ARTIFACT: {unit_id}.line_end "
                "< line_start"
            )

        if line_end > line_count:
            raise ValueError(
                f"INVALID_ARTIFACT: {unit_id}.line_end "
                f"exceeds source line count {line_count}"
            )

        # --------------------------------------------------------
        # Document order / non-overlap
        # --------------------------------------------------------

        if line_start <= previous_start:
            raise ValueError(
                f"INVALID_ARTIFACT: {unit_id} violates "
                "document order"
            )

        if line_start <= previous_end:
            raise ValueError(
                f"INVALID_ARTIFACT: {unit_id} overlaps "
                "previous unit"
            )

        previous_start = line_start
        previous_end = line_end

        # --------------------------------------------------------
        # Exact source-text provenance
        # --------------------------------------------------------

        expected_source_text = "".join(
            original_lines[line_start - 1:line_end]
        )

        if source_text != expected_source_text:
            raise ValueError(
                f"INVALID_ARTIFACT: source_text mismatch "
                f"in {unit_id}"
            )

        # --------------------------------------------------------
        # Whitespace-only units forbidden
        # --------------------------------------------------------

        if source_text.strip() == "":
            raise ValueError(
                f"INVALID_ARTIFACT: whitespace-only unit "
                f"{unit_id}"
            )