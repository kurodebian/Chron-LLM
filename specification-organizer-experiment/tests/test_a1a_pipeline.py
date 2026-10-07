#!/usr/bin/env python3
# tests/test_a1a_pipeline.py

import pytest
from pathlib import Path

from tools.a1_segment import (
    validate_raw_observation,
    normalize_boundaries,
    write_units,
    load_source,
)
from tools.validate_a1_artifact import validate_units_json


LINE_COUNT = 50  # fixture document line count


def make_fixture_document(tmp_path: Path) -> Path:
    """
    Create a temporary document with 50 lines.
    """
    doc = tmp_path / "fixture.md"
    lines = [
        f"LINE {i}\n"
        for i in range(1, LINE_COUNT + 1)
    ]
    doc.write_text(
        "".join(lines),
        encoding="utf-8",
    )
    return doc


def test_a1a_pipeline_valid(tmp_path):
    """
    VALID observation → validate → normalize → write_units → validate_units_json
    """

    # Create fixture document
    doc = make_fixture_document(tmp_path)
    lines = load_source(str(doc))

    # VALID raw observation
    observation = {
        "boundaries": [
            {"line_start": 1, "line_end": 5},
            {"line_start": 6, "line_end": 10},
            {"line_start": 11, "line_end": 20},
        ]
    }

    # Step 1: raw observation validation
    validate_raw_observation(observation, lines)

    # Step 2: normalization
    units = normalize_boundaries(
        observation,
        lines,
    )

    # Step 3: write units.json
    out = write_units(
        str(doc),
        units,
    )

    # Step 4: validate units.json
    validate_units_json(str(out))


def test_a1a_pipeline_invalid(tmp_path):
    """
    INVALID observation → validate_raw_observation must reject
    """

    doc = make_fixture_document(tmp_path)
    lines = load_source(str(doc))

    # INVALID: overlapping spans
    observation = {
        "boundaries": [
            {"line_start": 1, "line_end": 10},
            {"line_start": 5, "line_end": 15},
        ]
    }

    with pytest.raises(ValueError):
        validate_raw_observation(
            observation,
            lines,
        )