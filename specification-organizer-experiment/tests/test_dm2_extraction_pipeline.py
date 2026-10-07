# tests/test_dm2_extraction_pipeline.py

import json

import pytest

from tools.dm2_extraction import (
    build_dm2_prompt,
    extract_dm2_record,
    extract_dm2_records,
)


CANONICAL_UNIT = {
    "unit_id": "u0001",
    "line_start": 13,
    "line_end": 15,
    "source_text": "The system SHALL preserve canonical evidence.",
}


VALID_RECORD = {
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


class FakeLLM:
    def __init__(self, output):
        self.output = output
        self.calls = []

    def __call__(self, prompt):
        self.calls.append(prompt)
        return self.output


def test_prompt_contains_canonical_unit_verbatim():
    prompt = build_dm2_prompt(CANONICAL_UNIT)

    assert CANONICAL_UNIT["unit_id"] in prompt
    assert CANONICAL_UNIT["source_text"] in prompt
    assert str(CANONICAL_UNIT["line_start"]) in prompt
    assert str(CANONICAL_UNIT["line_end"]) in prompt


def test_prompt_forbids_resegmentation_and_causal_extraction():
    prompt = build_dm2_prompt(CANONICAL_UNIT)

    assert "MUST NOT split" in prompt
    assert "MUST NOT merge" in prompt
    assert "MUST NOT reorder" in prompt
    assert "causal" in prompt.lower()


def test_extract_dm2_record_returns_validated_record():
    llm = FakeLLM(json.dumps(VALID_RECORD))

    result = extract_dm2_record(
        canonical_unit=CANONICAL_UNIT,
        llm_call=llm,
    )

    assert result == VALID_RECORD
    assert len(llm.calls) == 1


def test_extract_dm2_record_rejects_canonical_identity_change():
    invalid = dict(VALID_RECORD)
    invalid["unit_id"] = "u9999"

    llm = FakeLLM(json.dumps(invalid))

    with pytest.raises(ValueError):
        extract_dm2_record(
            canonical_unit=CANONICAL_UNIT,
            llm_call=llm,
        )


def test_extract_dm2_record_rejects_resegmentation():
    invalid = dict(VALID_RECORD)
    invalid["line_end"] = 14

    llm = FakeLLM(json.dumps(invalid))

    with pytest.raises(ValueError):
        extract_dm2_record(
            canonical_unit=CANONICAL_UNIT,
            llm_call=llm,
        )


def test_extract_dm2_record_rejects_causal_fields():
    invalid = {
        **VALID_RECORD,
        "causes": ["u0002"],
    }

    llm = FakeLLM(json.dumps(invalid))

    with pytest.raises(ValueError):
        extract_dm2_record(
            canonical_unit=CANONICAL_UNIT,
            llm_call=llm,
        )


def test_extract_dm2_record_does_not_repair_invalid_json():
    llm = FakeLLM('{"unit_id":"u0001"')

    with pytest.raises(ValueError):
        extract_dm2_record(
            canonical_unit=CANONICAL_UNIT,
            llm_call=llm,
        )


def test_extract_dm2_record_does_not_call_llm_more_than_once():
    llm = FakeLLM(json.dumps(VALID_RECORD))

    extract_dm2_record(
        canonical_unit=CANONICAL_UNIT,
        llm_call=llm,
    )

    assert len(llm.calls) == 1


def test_extract_dm2_records_preserves_canonical_unit_order():
    unit2 = {
        "unit_id": "u0002",
        "line_start": 20,
        "line_end": 21,
        "source_text": "The system MAY continue.",
    }

    record2 = {
        **unit2,
        "semantic_kind": "Requirement",
        "semantic_evidence": {
            "phrases": ["MAY continue"],
            "lines": [20],
        },
        "semantic_attributes": {
            "modality": "may",
            "structural_form": "paragraph",
            "semantic_strength": "weak",
            "semantic_scope": "system-wide",
        },
        "resolution": {
            "status": "resolved",
            "reason": None,
        },
    }

    outputs = [
        json.dumps(VALID_RECORD),
        json.dumps(record2),
    ]

    calls = []

    def llm_call(prompt):
        calls.append(prompt)
        return outputs[len(calls) - 1]

    result = extract_dm2_records(
        canonical_units=[CANONICAL_UNIT, unit2],
        llm_call=llm_call,
    )

    assert [r["unit_id"] for r in result] == ["u0001", "u0002"]


def test_extract_dm2_records_rejects_missing_result():
    llm = FakeLLM(json.dumps(VALID_RECORD))

    with pytest.raises(ValueError):
        extract_dm2_records(
            canonical_units=[CANONICAL_UNIT],
            llm_call=lambda prompt: "",
        )

def test_extract_dm2_record_llm_uses_call_llm(monkeypatch):
    from tools import dm2_extraction

    calls = {}

    class FakeObservation:
        raw_output = json.dumps(VALID_RECORD)

    def fake_call_llm(prompt, config):
        calls["prompt"] = prompt
        calls["config"] = config
        return FakeObservation()

    monkeypatch.setattr(
        dm2_extraction,
        "call_llm",
        fake_call_llm,
    )

    result = dm2_extraction.extract_dm2_record_llm(
        canonical_unit=CANONICAL_UNIT,
    )

    assert result == VALID_RECORD
    assert "u0001" in calls["prompt"]
    assert CANONICAL_UNIT["source_text"] in calls["prompt"]

    config = calls["config"]

    assert config.temperature == 0.0
    assert config.top_k == 40
    assert config.top_p == 1.0
    assert config.seed == 0
    assert config.single_turn is True
    assert config.reasoning == "off"


def test_extract_dm2_record_llm_validates_raw_output(monkeypatch):
    from tools import dm2_extraction

    class FakeObservation:
        raw_output = json.dumps({
            **VALID_RECORD,
            "unit_id": "u9999",
        })

    monkeypatch.setattr(
        dm2_extraction,
        "call_llm",
        lambda prompt, config: FakeObservation(),
    )

    with pytest.raises(ValueError):
        dm2_extraction.extract_dm2_record_llm(
            canonical_unit=CANONICAL_UNIT,
        )


def test_extract_dm2_record_llm_does_not_repair_output(monkeypatch):
    from tools import dm2_extraction

    class FakeObservation:
        raw_output = '{"unit_id":"u0001"'

    monkeypatch.setattr(
        dm2_extraction,
        "call_llm",
        lambda prompt, config: FakeObservation(),
    )

    with pytest.raises(ValueError):
        dm2_extraction.extract_dm2_record_llm(
            canonical_unit=CANONICAL_UNIT,
        )