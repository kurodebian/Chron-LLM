#!/usr/bin/env python3
# tests/test_validate_raw_observation.py

import pytest
from tools.a1_segment import validate_raw_observation


LINES = [
    f"LINE {i}\n"
    for i in range(1, 201)
]

LINE_COUNT = len(LINES)


# ------------------------------------------------------------
# VALID CASES
# ------------------------------------------------------------

def test_valid_single_span():
    observation = {
        "boundaries": [
            {"line_start": 1, "line_end": 10}
        ]
    }

    validate_raw_observation(observation, LINES)


def test_valid_multiple_spans():
    observation = {
        "boundaries": [
            {"line_start": 1, "line_end": 5},
            {"line_start": 6, "line_end": 10},
            {"line_start": 11, "line_end": 20}
        ]
    }

    validate_raw_observation(observation, LINES)


def test_valid_single_line_span():
    observation = {
        "boundaries": [
            {"line_start": 10, "line_end": 10}
        ]
    }

    validate_raw_observation(observation, LINES)


# ------------------------------------------------------------
# INVALID CASES
# ------------------------------------------------------------

def test_invalid_line_start_lt_1():
    observation = {
        "boundaries": [
            {"line_start": 0, "line_end": 5}
        ]
    }

    with pytest.raises(ValueError):
        validate_raw_observation(observation, LINES)


def test_invalid_line_end_lt_line_start():
    observation = {
        "boundaries": [
            {"line_start": 10, "line_end": 5}
        ]
    }

    with pytest.raises(ValueError):
        validate_raw_observation(observation, LINES)


def test_invalid_line_end_gt_document():
    observation = {
        "boundaries": [
            {"line_start": 10, "line_end": 500}
        ]
    }

    with pytest.raises(ValueError):
        validate_raw_observation(observation, LINES)


def test_invalid_unsorted_spans():
    observation = {
        "boundaries": [
            {"line_start": 10, "line_end": 20},
            {"line_start": 5, "line_end": 9}
        ]
    }

    with pytest.raises(ValueError):
        validate_raw_observation(observation, LINES)


def test_invalid_overlapping_spans():
    observation = {
        "boundaries": [
            {"line_start": 1, "line_end": 10},
            {"line_start": 5, "line_end": 15}
        ]
    }

    with pytest.raises(ValueError):
        validate_raw_observation(observation, LINES)


def test_invalid_duplicate_spans():
    observation = {
        "boundaries": [
            {"line_start": 1, "line_end": 10},
            {"line_start": 1, "line_end": 10}
        ]
    }

    with pytest.raises(ValueError):
        validate_raw_observation(observation, LINES)


def test_invalid_forbidden_field():
    observation = {
        "boundaries": [
            {
                "line_start": 1,
                "line_end": 10,
                "semantic_kind": "TYPE"
            }
        ]
    }

    with pytest.raises(ValueError):
        validate_raw_observation(observation, LINES)


def test_invalid_root_structure():
    observation = {
        "unexpected": []
    }

    with pytest.raises(ValueError):
        validate_raw_observation(observation, LINES)


def test_invalid_boundaries_not_list():
    observation = {
        "boundaries": "not-a-list"
    }

    with pytest.raises(ValueError):
        validate_raw_observation(observation, LINES)


def test_invalid_whitespace_only_span():
    lines = [
        "content\n",
        "\n",
        "   \n",
        "content\n",
    ]

    observation = {
        "boundaries": [
            {"line_start": 2, "line_end": 3}
        ]
    }

    with pytest.raises(ValueError, match="whitespace-only span"):
        validate_raw_observation(observation, lines)


def test_invalid_observation_is_not_repaired():
    observation = {
        "boundaries": [
            {"line_start": 10, "line_end": 20},
            {"line_start": 5, "line_end": 9},
        ]
    }

    original = {
        "boundaries": [
            {"line_start": 10, "line_end": 20},
            {"line_start": 5, "line_end": 9},
        ]
    }

    with pytest.raises(ValueError):
        validate_raw_observation(observation, LINES)

    assert observation == original