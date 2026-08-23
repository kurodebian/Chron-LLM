import json
from pathlib import Path
import pytest
from causal_kernel.kernel.phase6_full_specification_causal_extraction import run_phase6_pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = PROJECT_ROOT / "data" / "audit"

@pytest.fixture(scope="module")
def phase6_data():
    summary = run_phase6_pipeline()
    units = json.loads((AUDIT_DIR / "phase6_spec_units_v1.json").read_text(encoding="utf-8"))
    relations = json.loads((AUDIT_DIR / "phase6_causal_relations_v1.json").read_text(encoding="utf-8"))
    conflicts = json.loads((AUDIT_DIR / "phase6_conflicts_v1.json").read_text(encoding="utf-8"))
    unresolved = json.loads((AUDIT_DIR / "phase6_unresolved_v1.json").read_text(encoding="utf-8"))
    return {
        "summary": summary,
        "units": units,
        "relations": relations,
        "conflicts": conflicts,
        "unresolved": unresolved
    }

def test_assert_source_files_accounted(phase6_data):
    summary = phase6_data["summary"]
    assert summary["source_file_count"] > 0
    assert summary["specification_unit_count"] == summary["source_file_count"]

def test_assert_no_silent_loss(phase6_data):
    summary = phase6_data["summary"]
    assert summary["source_lines"] == summary["extracted_lines"]
    assert summary["source_lines"] > 0

def test_assert_provenance_complete(phase6_data):
    units = phase6_data["units"]
    for u in units:
        assert "provenance" in u
        assert u["provenance"]["provenance_complete"] is True
        assert u["provenance"]["line_number_start"] >= 1
        assert "ast" in u

def test_assert_global_ids_unique(phase6_data):
    units = phase6_data["units"]
    unit_ids = [u["unit_id"] for u in units]
    assert len(unit_ids) == len(set(unit_ids))

def test_assert_all_relations_have_sources(phase6_data):
    relations = phase6_data["relations"]
    for r in relations:
        assert "source_unit" in r
        assert "target_unit" in r
        assert "classification" in r
        assert r["classification"] in ["EXPLICIT", "INFERRED"]
        assert "evidence" in r and len(r["evidence"]) > 0

def test_assert_unresolved_explicit(phase6_data):
    unresolved = phase6_data["unresolved"]
    for un in unresolved:
        assert "type" in un
        assert "reason" in un
        assert "provenance" in un