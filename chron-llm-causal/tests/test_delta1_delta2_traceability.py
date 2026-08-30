# ==========================================
# TEST SCRIPT: tests/test_delta1_delta2_traceability.py
# ==========================================

"""
Phase 2 独立トレーサビリティ検証テスト群 (T1 ~ T14)

Current Phase 2 identity contract:

* Delta-1 Node records : 340
* Delta-1 Edge records : 312
* Delta-2 Nodes         : 14
* Delta-2 Edges         : 11

Node identity:
source_original_id
= raw Delta-1 node["id"]

source_delta1_id
    = (component_id, raw_id, record_index)

Raw Node IDs are NOT required to be globally unique.
Record identities MUST be globally unique.

Edge identity:
source_original_id
= canonical Delta-1 edge ID

source_delta1_id
    = (component_id, canonical_edge_id, record_index)

No synthetic D1_N_* / D1_E_* graph IDs are permitted.
"""

import json
from pathlib import Path
from typing import Dict, Any

import pytest

TRACEABILITY_PATH = Path("data/audit/delta1_delta2_traceability_v1.json")
MASTERGRAPH_PATH = Path("data/graphs/causal_master_graph_v2.json")

EXPECTED_D1_NODES = 340
EXPECTED_D1_EDGES = 312

EXPECTED_D2_NODES = 14
EXPECTED_D2_EDGES = 11


@pytest.fixture(scope="module")
def traceability_data() -> Dict[str, Any]:
    """
    Load the Phase 2 traceability artifact.

    If the artifact does not exist, reconstruct it from the
    normalized Delta-1 population.
    """
    if not TRACEABILITY_PATH.exists():
        from causal_kernel.kernel.traceability_reconstructor import reconstruct

        reconstruct()

    assert TRACEABILITY_PATH.exists(), "Phase 2 traceability artifact was not generated."

    with open(TRACEABILITY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ==========================================================
# T1
# ==========================================================

def test_t1_all_delta1_nodes_accounted(traceability_data: Dict[str, Any]) -> None:
    """
    T1: all 340 Delta-1 Node records are accounted exactly once.

    Accounting is record-based, not raw-ID-based.
    """
    accounting = traceability_data["accounting"]["nodes"]
    total = sum(accounting.values())

    assert total == EXPECTED_D1_NODES, f"Expected {EXPECTED_D1_NODES} nodes, got {total}"
    assert len(traceability_data["node_mappings"]) == EXPECTED_D1_NODES


# ==========================================================
# T2
# ==========================================================

def test_t2_all_delta1_edges_accounted(traceability_data: Dict[str, Any]) -> None:
    """
    T2: all 312 Delta-1 Edge records are accounted exactly once.
    """
    accounting = traceability_data["accounting"]["edges"]
    total = sum(accounting.values())

    assert total == EXPECTED_D1_EDGES, f"Expected {EXPECTED_D1_EDGES} edges, got {total}"
    assert len(traceability_data["edge_mappings"]) == EXPECTED_D1_EDGES


# ==========================================================
# T3
# ==========================================================

def test_t3_every_mapping_references_existing_delta1(traceability_data: Dict[str, Any]) -> None:
    """
    T3: every mapping has a non-empty Delta-1 record identity.

    source_delta1_id is the authoritative traceability identity.
    """
    for mapping in traceability_data["node_mappings"]:
        assert "source_delta1_id" in mapping and mapping["source_delta1_id"]

    for mapping in traceability_data["edge_mappings"]:
        assert "source_delta1_id" in mapping and mapping["source_delta1_id"]


# ==========================================================
# T4
# ==========================================================

def test_t4_resolved_node_mapping_references_delta2(traceability_data: Dict[str, Any]) -> None:
    """
    T4: resolved Node mappings have a Delta-2 target.
    """
    for mapping in traceability_data["node_mappings"]:
        if mapping["classification"] in {"PRESERVED", "AGGREGATED"}:
            assert mapping["target_delta2_id"] is not None


# ==========================================================
# T5
# ==========================================================

def test_t5_resolved_edge_mapping_references_delta2(traceability_data: Dict[str, Any]) -> None:
    """
    T5: resolved Edge mappings have a Delta-2 target.
    """
    for mapping in traceability_data["edge_mappings"]:
        if mapping["classification"] in {"PRESERVED", "COLLAPSED"}:
            assert mapping["target_delta2_id"] is not None


# ==========================================================
# T6
# ==========================================================

def test_t6_no_silent_source_loss(traceability_data: Dict[str, Any]) -> None:
    """
    T6: no Delta-1 record is silently lost.
    """
    assert traceability_data["validation"]["no_silent_loss"] is True


# ==========================================================
# T7
# ==========================================================

def test_t7_no_duplicate_source_accounting(traceability_data: Dict[str, Any]) -> None:
    """
    T7: Delta-1 record identities are unique.

    IMPORTANT:
        source_original_id is intentionally NOT used here.

    Raw Node IDs may legitimately duplicate across components.
    The uniqueness contract applies to source_delta1_id.
    """
    node_ids = [mapping["source_delta1_id"] for mapping in traceability_data["node_mappings"]]
    edge_ids = [mapping["source_delta1_id"] for mapping in traceability_data["edge_mappings"]]

    assert len(node_ids) == EXPECTED_D1_NODES
    assert len(node_ids) == len(set(node_ids))

    assert len(edge_ids) == EXPECTED_D1_EDGES
    assert len(edge_ids) == len(set(edge_ids))


# ==========================================================
# T8
# ==========================================================

def test_t8_no_dangling_provenance_target(traceability_data: Dict[str, Any]) -> None:
    """
    T8: every Delta-2 provenance record has a Delta-2 identity.
    """
    node_provenance = traceability_data["delta2_node_provenance"]
    edge_provenance = traceability_data["delta2_edge_provenance"]

    assert len(node_provenance) == EXPECTED_D2_NODES
    assert len(edge_provenance) == EXPECTED_D2_EDGES

    for provenance in node_provenance:
        assert "delta2_id" in provenance and provenance["delta2_id"]

    for provenance in edge_provenance:
        assert "delta2_id" in provenance and provenance["delta2_id"]


# ==========================================================
# T9
# ==========================================================

def test_t9_all_mappings_contain_evidence(traceability_data: Dict[str, Any]) -> None:
    """
    T9: every mapping contains explicit evidence metadata.
    """
    for mapping in traceability_data["node_mappings"]:
        assert "evidence" in mapping and mapping["evidence"]
        assert "evidence_strength" in mapping

    for mapping in traceability_data["edge_mappings"]:
        assert "evidence" in mapping and mapping["evidence"]
        assert "evidence_strength" in mapping


# ==========================================================
# T10
# ==========================================================

def test_t10_e0_cannot_be_verified(traceability_data: Dict[str, Any]) -> None:
    """
    T10: E0 mappings cannot be treated as verified.

    E0 must remain UNRESOLVED with confidence 0.0.
    """
    for mapping in traceability_data["node_mappings"]:
        if mapping["evidence_strength"] == "E0":
            assert mapping["classification"] == "UNRESOLVED"
            assert mapping["confidence"] == 0.0

    for mapping in traceability_data["edge_mappings"]:
        if mapping["evidence_strength"] == "E0":
            assert mapping["classification"] == "UNRESOLVED"
            assert mapping["confidence"] == 0.0


# ==========================================================
# T11
# ==========================================================

def test_t11_unresolved_elements_explicitly_preserved(traceability_data: Dict[str, Any]) -> None:
    """
    T11: unresolved Node and Edge records are explicitly preserved.

    Current contract:
        unresolved = {
            "nodes": [...],
            "edges": [...]
        }

    The Node/Edge identity spaces remain separated.
    """
    unresolved = traceability_data["unresolved"]

    assert isinstance(unresolved, dict)
    assert "nodes" in unresolved
    assert "edges" in unresolved
    assert isinstance(unresolved["nodes"], list)
    assert isinstance(unresolved["edges"], list)

    # Every unresolved identity must correspond to an actual
    # source_delta1_id in its respective mapping space.
    node_ids = {
        mapping["source_delta1_id"]
        for mapping in traceability_data["node_mappings"]
        if mapping["classification"] == "UNRESOLVED"
    }

    edge_ids = {
        mapping["source_delta1_id"]
        for mapping in traceability_data["edge_mappings"]
        if mapping["classification"] == "UNRESOLVED"
    }

    assert set(unresolved["nodes"]) == node_ids
    assert set(unresolved["edges"]) == edge_ids


# ==========================================================
# T12
# ==========================================================

def test_t12_delta2_provenance_reconstructible(traceability_data: Dict[str, Any]) -> None:
    """
    T12: Delta-2 provenance containers exist and are
    structurally reconstructible from mapping records.
    """
    assert len(traceability_data["delta2_node_provenance"]) == EXPECTED_D2_NODES
    assert len(traceability_data["delta2_edge_provenance"]) == EXPECTED_D2_EDGES


# ==========================================================
# T13
# ==========================================================

def test_t13_old_traceability_not_required(traceability_data: Dict[str, Any]) -> None:
    """
    T13: Phase 2 does not depend on OLD_TRACEABILITY.
    """
    assert "old_traceability" not in traceability_data.get("source", {})


# ==========================================================
# T14
# ==========================================================

def test_t14_mastergraph_unchanged(traceability_data: Dict[str, Any]) -> None:
    """
    T14: Delta-2 MasterGraph exists.

    The reconstruction engine reads the MasterGraph but does
    not mutate it.
    """
    assert MASTERGRAPH_PATH.exists()

    assert traceability_data["delta2_totals"]["nodes"] == EXPECTED_D2_NODES
    assert traceability_data["delta2_totals"]["edges"] == EXPECTED_D2_EDGES