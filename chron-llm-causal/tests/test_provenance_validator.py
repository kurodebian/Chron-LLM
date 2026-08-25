"""Unit tests for ProvenanceValidator targeting Canonical Traceability."""

import json
from pathlib import Path
import pytest
from causal_kernel.kernel.validator.provenance_validator import ProvenanceValidator


@pytest.fixture(scope="module")
def canonical_traceability():
    path = Path("delta1_delta2_traceability.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def master_graph():
    path = Path("data/graphs/causal_master_graph_v2.json")
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def test_valid_canonical_provenance(canonical_traceability, master_graph):
    """正常系: Canonical Traceability データの Provenance 検証が成功すること"""
    validator = ProvenanceValidator(master_graph=master_graph)
    result = validator.validate(canonical_traceability)
    assert result.is_valid, f"Expected PASS, got errors: {result.errors}"


def test_missing_target_delta2_node_id(canonical_traceability, master_graph):
    """異常系: MasterGraph に存在しない delta2_node_id の検出"""
    validator = ProvenanceValidator(master_graph=master_graph)
    data = json.loads(json.dumps(canonical_traceability))
    data["delta2_nodes_provenance"][0]["delta2_node_id"] = "NON_EXISTENT_NODE_999"

    result = validator.validate(data)
    assert not result.is_valid
    assert any("NON_EXISTENT_NODE_999" in err for err in result.errors)


def test_missing_target_delta2_edge_id(canonical_traceability, master_graph):
    """異常系: MasterGraph に存在しない delta2_edge_id の検出"""
    validator = ProvenanceValidator(master_graph=master_graph)
    data = json.loads(json.dumps(canonical_traceability))
    data["delta2_edges_provenance"][0]["delta2_edge_id"] = "NON_EXISTENT_EDGE_999"

    result = validator.validate(data)
    assert not result.is_valid
    assert any("NON_EXISTENT_EDGE_999" in err for err in result.errors)


def test_negative_source_node_count(canonical_traceability):
    """異常系: source_delta1_nodes_count が負の数値の検出"""
    validator = ProvenanceValidator()
    data = json.loads(json.dumps(canonical_traceability))
    data["delta2_nodes_provenance"][0]["source_delta1_nodes_count"] = -5

    result = validator.validate(data)
    assert not result.is_valid
    assert any("cannot be negative" in err for err in result.errors)


def test_negative_source_edge_count(canonical_traceability):
    """異常系: source_delta1_edges_count が負の数値の検出"""
    validator = ProvenanceValidator()
    data = json.loads(json.dumps(canonical_traceability))
    data["delta2_edges_provenance"][0]["source_delta1_edges_count"] = -1

    result = validator.validate(data)
    assert not result.is_valid
    assert any("cannot be negative" in err for err in result.errors)


def test_incomplete_provenance_flag_mismatch(canonical_traceability):
    """異常系: provenance_complete == True かつ count == 0 の論理矛盾の検出"""
    validator = ProvenanceValidator()
    data = json.loads(json.dumps(canonical_traceability))
    data["delta2_nodes_provenance"][0]["provenance_complete"] = True
    data["delta2_nodes_provenance"][0]["source_delta1_nodes_count"] = 0

    result = validator.validate(data)
    assert not result.is_valid
    assert any("provenance_complete' is True but source count is 0" in err for err in result.errors)


def test_invalid_field_types(canonical_traceability):
    """異常系: provenance_complete が boolean 以外の型の検出"""
    validator = ProvenanceValidator()
    data = json.loads(json.dumps(canonical_traceability))
    data["delta2_nodes_provenance"][0]["provenance_complete"] = "true_string"

    result = validator.validate(data)
    assert not result.is_valid
    assert any("must be a boolean" in err for err in result.errors)