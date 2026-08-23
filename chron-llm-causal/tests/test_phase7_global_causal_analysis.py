import json
from pathlib import Path
import pytest
from causal_kernel.kernel.phase7_global_causal_analysis import run_phase7_pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = PROJECT_ROOT / "data" / "audit"


@pytest.fixture(scope="module")
def phase7_data():
    summary = run_phase7_pipeline()
    graph = json.loads((AUDIT_DIR / "phase7_global_specification_graph_v1.json").read_text(encoding="utf-8"))
    causal = json.loads((AUDIT_DIR / "phase7_causal_analysis_v1.json").read_text(encoding="utf-8"))
    authority = json.loads((AUDIT_DIR / "phase7_authority_analysis_v1.json").read_text(encoding="utf-8"))
    invariants = json.loads((AUDIT_DIR / "phase7_invariant_analysis_v1.json").read_text(encoding="utf-8"))
    unresolved = json.loads((AUDIT_DIR / "phase7_unresolved_v1.json").read_text(encoding="utf-8"))
    return {
        "summary": summary,
        "graph": graph,
        "causal": causal,
        "authority": authority,
        "invariants": invariants,
        "unresolved": unresolved
    }


def test_graph_nodes_accounted(phase7_data):
    summary = phase7_data["summary"]
    graph = phase7_data["graph"]
    units = json.loads((AUDIT_DIR / "phase6_spec_units_v1.json").read_text(encoding="utf-8"))
    assert summary["graph_nodes"] == len(units)
    assert len(graph["nodes"]) == len(units)


def test_graph_edges_accounted(phase7_data):
    summary = phase7_data["summary"]
    graph = phase7_data["graph"]
    relations = json.loads((AUDIT_DIR / "phase6_causal_relations_v1.json").read_text(encoding="utf-8"))
    assert summary["graph_edges"] == len(relations)
    assert len(graph["edges"]) == len(relations)


def test_provenance_complete(phase7_data):
    summary = phase7_data["summary"]
    graph = phase7_data["graph"]
    assert summary["provenance_complete"] is True
    for node in graph["nodes"]:
        assert "provenance" in node
        assert node["provenance"]["provenance_complete"] is True


def test_no_silent_loss_and_merge(phase7_data):
    summary = phase7_data["summary"]
    assert summary["files"] == summary["specification_units"]
    assert summary["specification_units"] == summary["graph_nodes"]


def test_unresolved_explicit(phase7_data):
    unresolved = phase7_data["unresolved"]
    for u in unresolved:
        assert "type" in u
        assert "reason" in u
        assert "provenance" in u


def test_authority_paths_traceable(phase7_data):
    authority = phase7_data["authority"]
    assert "non_authoritative_to_canonical_paths" in authority
    assert "canonical_mutation_paths" in authority
    for path in authority["non_authoritative_to_canonical_paths"]:
        assert "source_unit" in path
        assert "target_unit" in path
        assert "path" in path


def test_invariant_paths_traceable(phase7_data):
    invariants = phase7_data["invariants"]
    assert "invariants" in invariants
    for inv in invariants["invariants"]:
        assert "source_unit" in inv
        assert "enforcing_operations" in inv
        assert "affected_state" in inv
        assert "downstream_propagation" in inv