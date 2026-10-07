import pytest

from tools.dm2_extraction import extract_dm2_record_llm


CANONICAL_UNIT = {
    "unit_id": "u0001",
    "line_start": 13,
    "line_end": 15,
    "source_text": "The system SHALL preserve canonical evidence.",
}


@pytest.mark.llm_e2e
def test_dm2_real_llm_one_unit_e2e():
    record = extract_dm2_record_llm(
        canonical_unit=CANONICAL_UNIT,
    )

    # A-1a canonical identity/span must survive unchanged.
    assert record["unit_id"] == CANONICAL_UNIT["unit_id"]
    assert record["line_start"] == CANONICAL_UNIT["line_start"]
    assert record["line_end"] == CANONICAL_UNIT["line_end"]
    assert record["source_text"] == CANONICAL_UNIT["source_text"]

    # DM-2 record must contain the complete V2 structure.
    assert set(record) == {
        "unit_id",
        "line_start",
        "line_end",
        "source_text",
        "semantic_kind",
        "semantic_evidence",
        "semantic_attributes",
        "resolution",
    }

    # Closed semantic vocabulary.
    assert record["semantic_kind"] in {
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
    }

    # No causal/graph leakage.
    forbidden = {
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

    assert forbidden.isdisjoint(record)
