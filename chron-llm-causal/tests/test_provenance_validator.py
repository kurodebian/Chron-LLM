"""Unit tests for ProvenanceValidator targeting Canonical Traceability (F4/F5 pure contract)."""

import pytest
from causal_kernel.kernel.validator.provenance_validator import ProvenanceValidator


@pytest.fixture
def mock_master_graph():
    """MasterGraph の参照チェック用モック"""
    return {
        "nodes": [
            {"id": "NODE_AUTH_001"},
            {"id": "NODE_WAL_001"},
        ],
        "edges": [
            {"id": "E001"},
            {"id": "E002"},
        ],
    }


@pytest.fixture
def valid_f4_traceability():
    """正常な F4 契約準拠 Traceability データ構造"""
    return {
        "delta2_nodes_provenance": [
            {
                "delta2_node_id": "NODE_AUTH_001",
                "source_delta1_node_ids": [
                    "comp_a:raw_node_1:0",
                    "comp_a:raw_node_2:1",
                ],
                "provenance_complete": True,
            }
        ],
        "delta2_edges_provenance": [
            {
                "delta2_edge_id": "E001",
                "source_delta1_edge_ids": [
                    "comp_b:raw_edge_1:0",
                ],
                "provenance_complete": True,
            }
        ],
    }


def test_valid_canonical_provenance(valid_f4_traceability, mock_master_graph):
    """正常系: F4 契約に完全準拠したデータの検証成功"""
    validator = ProvenanceValidator(master_graph=mock_master_graph)
    result = validator.validate(valid_f4_traceability)
    assert result.is_valid, f"Expected PASS, got errors: {result.errors}"


def test_missing_target_delta2_node_id(valid_f4_traceability, mock_master_graph):
    """異常系: MasterGraph に存在しない delta2_node_id の検出"""
    validator = ProvenanceValidator(master_graph=mock_master_graph)
    valid_f4_traceability["delta2_nodes_provenance"][0]["delta2_node_id"] = "NON_EXISTENT_NODE"

    result = validator.validate(valid_f4_traceability)
    assert not result.is_valid
    assert any("does not exist in MasterGraph" in err for err in result.errors)


def test_missing_target_delta2_edge_id(valid_f4_traceability, mock_master_graph):
    """異常系: MasterGraph に存在しない delta2_edge_id の検出"""
    validator = ProvenanceValidator(master_graph=mock_master_graph)
    valid_f4_traceability["delta2_edges_provenance"][0]["delta2_edge_id"] = "NON_EXISTENT_EDGE"

    result = validator.validate(valid_f4_traceability)
    assert not result.is_valid
    assert any("does not exist in MasterGraph" in err for err in result.errors)


def test_empty_source_node_ids_when_complete(valid_f4_traceability):
    """異常系: provenance_complete == True なのに source_delta1_node_ids が空"""
    validator = ProvenanceValidator()
    valid_f4_traceability["delta2_nodes_provenance"][0]["source_delta1_node_ids"] = []
    valid_f4_traceability["delta2_nodes_provenance"][0]["provenance_complete"] = True

    result = validator.validate(valid_f4_traceability)
    assert not result.is_valid
    assert any("is True but source_delta1_node_ids is empty" in err for err in result.errors)


def test_empty_source_edge_ids_when_complete(valid_f4_traceability):
    """異常系: provenance_complete == True なのに source_delta1_edge_ids が空"""
    validator = ProvenanceValidator()
    valid_f4_traceability["delta2_edges_provenance"][0]["source_delta1_edge_ids"] = []
    valid_f4_traceability["delta2_edges_provenance"][0]["provenance_complete"] = True

    result = validator.validate(valid_f4_traceability)
    assert not result.is_valid
    assert any("is True but source_delta1_edge_ids is empty" in err for err in result.errors)


def test_invalid_node_record_identity(valid_f4_traceability):
    """異常系: Record Identity フォーマット (component:raw_id:index) 違反の検出"""
    validator = ProvenanceValidator()
    valid_f4_traceability["delta2_nodes_provenance"][0]["source_delta1_node_ids"] = [
        "INVALID_NODE_ID_WITHOUT_COLONS"
    ]

    result = validator.validate(valid_f4_traceability)
    assert not result.is_valid
    assert any("invalid Canonical Record Identity" in err for err in result.errors)


def test_invalid_edge_record_identity(valid_f4_traceability):
    """異常系: Record Identity フォーマット (component:raw_id:index) 違反の検出"""
    validator = ProvenanceValidator()
    valid_f4_traceability["delta2_edges_provenance"][0]["source_delta1_edge_ids"] = [
        "INVALID_EDGE_ID"
    ]

    result = validator.validate(valid_f4_traceability)
    assert not result.is_valid
    assert any("invalid Canonical Record Identity" in err for err in result.errors)


def test_duplicate_source_node_ids(valid_f4_traceability):
    """異常系: source_delta1_node_ids 配列内の重複 ID 検出"""
    validator = ProvenanceValidator()
    valid_f4_traceability["delta2_nodes_provenance"][0]["source_delta1_node_ids"] = [
        "comp_a:raw_node_1:0",
        "comp_a:raw_node_1:0",
    ]

    result = validator.validate(valid_f4_traceability)
    assert not result.is_valid
    assert any("duplicate source Delta-1 record identity" in err for err in result.errors)


def test_duplicate_source_edge_ids(valid_f4_traceability):
    """異常系: source_delta1_edge_ids 配列内の重複 ID 検出"""
    validator = ProvenanceValidator()
    valid_f4_traceability["delta2_edges_provenance"][0]["source_delta1_edge_ids"] = [
        "comp_b:raw_edge_1:0",
        "comp_b:raw_edge_1:0",
    ]

    result = validator.validate(valid_f4_traceability)
    assert not result.is_valid
    assert any("duplicate source Delta-1 record identity" in err for err in result.errors)


def test_invalid_field_types(valid_f4_traceability):
    """異常系: provenance_complete が boolean 以外の型の検出"""
    validator = ProvenanceValidator()
    valid_f4_traceability["delta2_nodes_provenance"][0]["provenance_complete"] = "not_a_bool"

    result = validator.validate(valid_f4_traceability)
    assert not result.is_valid
    assert any("must be a boolean" in err for err in result.errors)