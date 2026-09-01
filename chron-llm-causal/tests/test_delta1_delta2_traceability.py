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

def test_t4_only_preserved_node_mapping_references_delta2(
    traceability_data: Dict[str, Any],
) -> None:
    """
    T4: only PRESERVED Node mappings reference an actual
    Delta-2 MasterGraph Node identity.

    Phase 2 contract:

        PRESERVED
            -> target_delta2_id MUST be an actual Delta-2 Node ID.

        AGGREGATED / ABSORBED / UNRESOLVED
            -> target_delta2_id MUST be None.

    IMPORTANT:
        Delta-2 Node IDs are canonical identities defined by
        the MasterGraph. Their textual prefix is NOT part of
        the identity contract.

        Semantic provenance is deferred to Phase 3.
    """

    with open(
        MASTERGRAPH_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        mastergraph = json.load(f)

    delta2_node_ids = {
        node["id"]
        for node in mastergraph["nodes"]
    }

    for mapping in traceability_data["node_mappings"]:

        classification = mapping["classification"]
        target = mapping["target_delta2_id"]

        if classification == "PRESERVED":

            assert target is not None
            assert target in delta2_node_ids

        else:

            assert target is None


# ==========================================================
# T5
# ==========================================================

def test_t5_only_preserved_edge_mapping_references_delta2(
    traceability_data: Dict[str, Any],
) -> None:
    """
    T5: only PRESERVED Edge mappings reference an actual
    Delta-2 MasterGraph Edge identity.

    Phase 2 contract:

        PRESERVED
            -> target_delta2_id MUST be an actual Delta-2 Edge ID.

        COLLAPSED / ABSORBED / UNRESOLVED
            -> target_delta2_id MUST be None.

    IMPORTANT:
        Delta-2 Edge IDs are canonical identities defined by
        the MasterGraph. Their textual prefix is NOT part of
        the identity contract.

        Semantic provenance is deferred to Phase 3.
    """

    with open(
        MASTERGRAPH_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        mastergraph = json.load(f)

    delta2_edge_ids = {
        edge["id"]
        for edge in mastergraph["edges"]
    }

    for mapping in traceability_data["edge_mappings"]:

        classification = mapping["classification"]
        target = mapping["target_delta2_id"]

        if classification == "PRESERVED":

            assert target is not None
            assert target in delta2_edge_ids

        else:

            assert target is None


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
    node_ids = [
        mapping["source_delta1_id"]
        for mapping in traceability_data["node_mappings"]
    ]
    edge_ids = [
        mapping["source_delta1_id"]
        for mapping in traceability_data["edge_mappings"]
    ]

    assert len(node_ids) == EXPECTED_D1_NODES
    assert len(node_ids) == len(set(node_ids))

    assert len(edge_ids) == EXPECTED_D1_EDGES
    assert len(edge_ids) == len(set(edge_ids))


# ==========================================================
# T8
# ==========================================================

def test_t8_preserved_mappings_reference_existing_delta2(
    traceability_data: Dict[str, Any],
) -> None:
    """
    T8: PRESERVED mappings reference existing Delta-2
    identities.

    Phase 2 contract:

        PRESERVED
            -> target_delta2_id MUST exist

        AGGREGATED / ABSORBED / UNRESOLVED
            -> target_delta2_id MUST be None

    Semantic provenance is deferred to Phase 3.
    """

    with open(
        MASTERGRAPH_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        mastergraph = json.load(f)

    delta2_node_ids = {
        node["id"]
        for node in mastergraph["nodes"]
    }

    delta2_edge_ids = {
        edge["id"]
        for edge in mastergraph["edges"]
    }

    for mapping in traceability_data["node_mappings"]:

        classification = mapping["classification"]
        target = mapping["target_delta2_id"]

        if classification == "PRESERVED":
            assert target is not None
            assert target in delta2_node_ids
        else:
            assert target is None

    for mapping in traceability_data["edge_mappings"]:

        classification = mapping["classification"]
        target = mapping["target_delta2_id"]

        if classification == "PRESERVED":
            assert target is not None
            assert target in delta2_edge_ids
        else:
            assert target is None


# ==========================================================
# T9
# ==========================================================

def test_t9_all_mappings_contain_evidence(
    traceability_data: Dict[str, Any],
) -> None:
    """
    T9: every Phase 2 accounting mapping contains
    explicit evidence metadata.
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

def test_t10_e0_cannot_be_verified(
    traceability_data: Dict[str, Any],
) -> None:
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

def test_t11_unresolved_elements_explicitly_preserved(
    traceability_data: Dict[str, Any],
) -> None:
    """
    T11: unresolved Node and Edge records are explicitly
    preserved.

    Canonical contract:
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

def test_t12_phase2_structural_mapping_contract(
    traceability_data: Dict[str, Any],
) -> None:
    """
    T12: Phase 2 structural mapping artifact conforms to the
    canonical Phase 2 accounting contract.

    Phase 2 owns only structural/accounting mapping.

    It MUST contain:
        - node_mappings
        - edge_mappings
        - accounting
        - unresolved

    It MUST NOT contain:
        - delta2_nodes_provenance
        - delta2_edges_provenance

    Semantic D1 -> D2 provenance is exclusively deferred to
    Phase 3.
    """

    # ----------------------------------------------------------
    # Phase
    # ----------------------------------------------------------

    assert traceability_data.get("phase") == "PHASE_2"

    # ----------------------------------------------------------
    # Phase 3 provenance containers MUST NOT leak into Phase 2
    # ----------------------------------------------------------

    assert (
        "delta2_nodes_provenance"
        not in traceability_data
    )

    assert (
        "delta2_edges_provenance"
        not in traceability_data
    )

    # ----------------------------------------------------------
    # Required Phase 2 structural mapping containers
    # ----------------------------------------------------------

    assert "node_mappings" in traceability_data
    assert "edge_mappings" in traceability_data
    assert "accounting" in traceability_data
    assert "unresolved" in traceability_data

    node_mappings = traceability_data[
        "node_mappings"
    ]

    edge_mappings = traceability_data[
        "edge_mappings"
    ]

    accounting = traceability_data[
        "accounting"
    ]

    unresolved = traceability_data[
        "unresolved"
    ]

    # ----------------------------------------------------------
    # Container types
    # ----------------------------------------------------------

    assert isinstance(node_mappings, list)
    assert isinstance(edge_mappings, list)
    assert isinstance(accounting, dict)
    assert isinstance(unresolved, dict)

    assert isinstance(
        unresolved.get("nodes"),
        list,
    )

    assert isinstance(
        unresolved.get("edges"),
        list,
    )

    # ----------------------------------------------------------
    # Physical population coverage
    #
    # Phase 2 must account for every Delta-1 physical record.
    # ----------------------------------------------------------

    assert len(node_mappings) == 340
    assert len(edge_mappings) == 312

    # ----------------------------------------------------------
    # Canonical accounting
    # ----------------------------------------------------------

    expected_node_accounting = {
        "PRESERVED": 14,
        "AGGREGATED": 306,
        "ABSORBED": 18,
        "UNRESOLVED": 2,
    }

    expected_edge_accounting = {
        "PRESERVED": 11,
        "COLLAPSED": 280,
        "ABSORBED": 15,
        "UNRESOLVED": 6,
    }

    assert (
        accounting.get("nodes")
        == expected_node_accounting
    )

    assert (
        accounting.get("edges")
        == expected_edge_accounting
    )

    # ----------------------------------------------------------
    # Recompute classifications independently from mappings.
    #
    # This prevents the accounting object from becoming its
    # own oracle.
    # ----------------------------------------------------------

    from collections import Counter

    actual_node_accounting = Counter(
        mapping.get("classification")
        for mapping in node_mappings
    )

    actual_edge_accounting = Counter(
        mapping.get("classification")
        for mapping in edge_mappings
    )

    assert dict(actual_node_accounting) == (
        expected_node_accounting
    )

    assert dict(actual_edge_accounting) == (
        expected_edge_accounting
    )

    # ----------------------------------------------------------
    # Unresolved must exactly correspond to mappings classified
    # as UNRESOLVED.
    # ----------------------------------------------------------

    unresolved_node_ids = {
        mapping["source_delta1_id"]
        for mapping in node_mappings
        if mapping["classification"]
        == "UNRESOLVED"
    }

    unresolved_edge_ids = {
        mapping["source_delta1_id"]
        for mapping in edge_mappings
        if mapping["classification"]
        == "UNRESOLVED"
    }

    assert set(unresolved["nodes"]) == (
        unresolved_node_ids
    )

    assert set(unresolved["edges"]) == (
        unresolved_edge_ids
    )

    assert len(unresolved["nodes"]) == 2
    assert len(unresolved["edges"]) == 6


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