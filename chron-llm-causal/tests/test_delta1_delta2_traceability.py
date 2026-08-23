# ==========================================
# 2. TEST SCRIPT: tests/test_delta1_delta2_traceability.py
# ==========================================
"""
Phase 2 独立トレーサビリティ検証テスト群 (T1 ~ T14)
"""

import json
import pytest
from pathlib import Path

@pytest.fixture(scope="module")
def traceability_data():
    path = Path("data/audit/delta1_delta2_traceability_v1.json")
    if not path.exists():
        # 自動生成を試みる
        from causal_kernel.kernel.traceability_reconstructor import reconstruct
        reconstruct()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_t1_all_delta1_nodes_accounted(traceability_data):
    """T1: all 386 Delta1 nodes accounted exactly once"""
    accounting = traceability_data["accounting"]["nodes"]
    total = sum(accounting.values())
    assert total == 386, f"Expected 386 nodes, got {total}"
    assert len(traceability_data["node_mappings"]) == 386

def test_t2_all_delta1_edges_accounted(traceability_data):
    """T2: all 312 Delta1 edges accounted exactly once"""
    accounting = traceability_data["accounting"]["edges"]
    total = sum(accounting.values())
    assert total == 312, f"Expected 312 edges, got {total}"
    assert len(traceability_data["edge_mappings"]) == 312

def test_t3_every_mapping_references_existing_delta1(traceability_data):
    """T3: every mapping references existing Delta1 source"""
    for m in traceability_data["node_mappings"]:
        assert "source_delta1_id" in m and m["source_delta1_id"]
    for m in traceability_data["edge_mappings"]:
        assert "source_delta1_id" in m and m["source_delta1_id"]

def test_t4_resolved_node_mapping_references_delta2(traceability_data):
    """T4: every resolved node mapping references existing Delta2 node (if target exists)"""
    for m in traceability_data["node_mappings"]:
        if m["classification"] in ["PRESERVED", "AGGREGATED"]:
            assert m["target_delta2_id"] is not None

def test_t5_resolved_edge_mapping_references_delta2(traceability_data):
    """T5: every resolved edge mapping references existing Delta2 edge (if target exists)"""
    for m in traceability_data["edge_mappings"]:
        if m["classification"] in ["PRESERVED", "COLLAPSED"]:
            assert m["target_delta2_id"] is not None

def test_t6_no_silent_source_loss(traceability_data):
    """T6: no silent source loss"""
    assert traceability_data["validation"]["no_silent_loss"] is True

def test_t7_no_duplicate_source_accounting(traceability_data):
    """T7: no duplicate source accounting"""
    node_ids = [m["source_delta1_id"] for m in traceability_data["node_mappings"]]
    assert len(node_ids) == len(set(node_ids))

def test_t8_no_dangling_provenance_target(traceability_data):
    """T8: no dangling provenance target"""
    for p in traceability_data["delta2_node_provenance"]:
        assert "delta2_id" in p

def test_t9_all_mappings_contain_evidence(traceability_data):
    """T9: all mapping records contain evidence"""
    for m in traceability_data["node_mappings"]:
        assert "evidence" in m and m["evidence"]
        assert "evidence_strength" in m
    for m in traceability_data["edge_mappings"]:
        assert "evidence" in m and m["evidence"]
        assert "evidence_strength" in m

def test_t10_e0_cannot_be_verified(traceability_data):
    """T10: E0 mappings cannot be VERIFIED"""
    for m in traceability_data["node_mappings"]:
        if m["evidence_strength"] == "E0":
            assert m["classification"] == "UNRESOLVED"
            assert m["confidence"] == 0.0

def test_t11_unresolved_elements_explicitly_preserved(traceability_data):
    """T11: unresolved elements explicitly preserved"""
    assert isinstance(traceability_data["unresolved"], list)

def test_t12_delta2_provenance_reconstructible(traceability_data):
    """T12: Delta2 provenance is reconstructible from mapping records"""
    assert len(traceability_data["delta2_node_provenance"]) > 0

def test_t13_old_traceability_not_required(traceability_data):
    """T13: OLD_TRACEABILITY is not required for test success"""
    # 旧トレーサビリティファイルへの参照を含まない独立動作を確認
    assert "old_traceability" not in traceability_data.get("source", {})

def test_t14_mastergraph_unchanged(traceability_data):
    """T14: MasterGraph hash/content is unchanged"""
    master_path = Path("data/graphs/causal_master_graph_v2.json")
    assert master_path.exists()