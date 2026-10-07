#!/usr/bin/env python3
# tests/test_normalize_boundaries.py

import pytest
from tools.a1_segment import (
    normalize_boundaries,
    validate_raw_observation,
)


LINES = [
    "# Constitution\n",
    "\n",
    "The kernel is deterministic.\n",
    "  \n",
    "History is canonical truth.\n",
]


def test_normalize_assigns_sequential_unit_ids():
    observation = {
        "boundaries": [
            {"line_start": 1, "line_end": 1},
            {"line_start": 3, "line_end": 3},
            {"line_start": 5, "line_end": 5},
        ]
    }

    validate_raw_observation(observation, LINES)
    units = normalize_boundaries(observation, LINES)

    assert [u["unit_id"] for u in units] == [
        "u0001",
        "u0002",
        "u0003",
    ]


def test_normalize_regenerates_exact_source_text():
    observation = {
        "boundaries": [
            {"line_start": 1, "line_end": 1},
            {"line_start": 3, "line_end": 3},
        ]
    }

    validate_raw_observation(observation, LINES)
    units = normalize_boundaries(observation, LINES)

    assert units[0]["source_text"] == "# Constitution\n"
    assert units[1]["source_text"] == (
        "The kernel is deterministic.\n"
    )


def test_normalize_preserves_line_spans_and_order():
    observation = {
        "boundaries": [
            {"line_start": 1, "line_end": 2},
            {"line_start": 3, "line_end": 5},
        ]
    }

    validate_raw_observation(observation, LINES)
    units = normalize_boundaries(observation, LINES)

    assert [
        (u["line_start"], u["line_end"]) for u in units
    ] == [(1, 2), (3, 5)]

    assert units[0]["source_text"] == (
        "# Constitution\n\n"
    )
    assert units[1]["source_text"] == (
        "The kernel is deterministic.\n"
        "  \n"
        "History is canonical truth.\n"
    )


def test_invalid_whitespace_only_span_is_rejected_before_normalization():
    observation = {
        "boundaries": [
            {"line_start": 4, "line_end": 4},
        ]
    }

    with pytest.raises(
        ValueError,
        match="whitespace-only span",
    ):
        validate_raw_observation(observation, LINES)


def test_invalid_observation_is_rejected_before_normalization():
    observation = {
        "boundaries": [
            {"line_start": 3, "line_end": 3},
            {"line_start": 1, "line_end": 1},
        ]
    }

    with pytest.raises(ValueError):
        validate_raw_observation(observation, LINES)


def test_normalization_does_not_modify_observation():
    observation = {
        "boundaries": [
            {"line_start": 1, "line_end": 1},
            {"line_start": 3, "line_end": 3},
        ]
    }

    original = {
        "boundaries": [
            {"line_start": 1, "line_end": 1},
            {"line_start": 3, "line_end": 3},
        ]
    }

    validate_raw_observation(observation, LINES)
    normalize_boundaries(observation, LINES)

    assert observation == original