"""
tests/test_reference_validator.py
----------------------------------
ReferenceValidator (P1-A 参照存在性) の5点網羅テスト
"""

from causal_kernel.kernel.models import (
    Delta2MasterGraph,
    Delta2MasterGraphEdge,
    Delta2MasterGraphNode,
)
from causal_kernel.kernel.validator.reference_validator import ReferenceValidator


def _build_base_graph():
    return Delta2MasterGraph(
        nodes=[
            Delta2MasterGraphNode(
                id="N1",
                global_id="g1",
                local_id="l1",
                type="invariant",
                name="n1",
                description="",
            ),
            Delta2MasterGraphNode(
                id="N2",
                global_id="g2",
                local_id="l2",
                type="operation",
                name="n2",
                description="",
            ),
            Delta2MasterGraphNode(
                id="INV1",
                global_id="g3",
                local_id="l3",
                type="invariant",
                name="inv1",
                description="",
            ),
        ],
        edges=[
            Delta2MasterGraphEdge(
                id="E1",
                from_="N1",
                to="N2",
                pipeline="p1",
                morphism_type="m1",
                delta_level="L2",
                guard_invariant=["INV1"],
            )
        ],
    )


# 1. 全参照正常
def test_reference_validator_all_valid():
    graph = _build_base_graph()
    traceability = {
        "delta2_nodes_provenance": [{"delta2_node_id": "N1", "provenance_complete": True}],
        "delta2_edges_provenance": [{"delta2_edge_id": "E1", "provenance_complete": True}],
    }

    validator = ReferenceValidator(graph, traceability)
    result = validator.validate_all_references()

    assert result["is_valid"] is True
    assert all(len(v) == 0 for v in result["violations"].values())


# 2. Dangling Endpoint
def test_reference_validator_dangling_endpoint():
    graph = _build_base_graph()
    graph.edges[0].to = "MISSING_NODE"

    validator = ReferenceValidator(graph)
    result = validator.validate_all_references()

    assert result["is_valid"] is False
    assert len(result["violations"]["dangling_edge_endpoints"]) == 1
    assert result["violations"]["dangling_edge_endpoints"][0]["missing_id"] == "MISSING_NODE"


# 3. Dangling Guard Invariant
def test_reference_validator_dangling_guard_invariant():
    graph = _build_base_graph()
    graph.edges[0].guard_invariant = ["MISSING_INV"]

    validator = ReferenceValidator(graph)
    result = validator.validate_all_references()

    assert result["is_valid"] is False
    assert len(result["violations"]["dangling_guard_invariants"]) == 1
    assert result["violations"]["dangling_guard_invariants"][0]["missing_id"] == "MISSING_INV"


# 4. Dangling Node Provenance
def test_reference_validator_dangling_node_provenance():
    graph = _build_base_graph()
    traceability = {
        "delta2_nodes_provenance": [{"delta2_node_id": "MISSING_NODE_PROV"}],
    }

    validator = ReferenceValidator(graph, traceability)
    result = validator.validate_all_references()

    assert result["is_valid"] is False
    assert len(result["violations"]["dangling_node_provenance"]) == 1
    assert result["violations"]["dangling_node_provenance"][0]["missing_target_id"] == "MISSING_NODE_PROV"


# 5. Dangling Edge Provenance
def test_reference_validator_dangling_edge_provenance():
    graph = _build_base_graph()
    traceability = {
        "delta2_edges_provenance": [{"delta2_edge_id": "MISSING_EDGE_PROV"}],
    }

    validator = ReferenceValidator(graph, traceability)
    result = validator.validate_all_references()

    assert result["is_valid"] is False
    assert len(result["violations"]["dangling_edge_provenance"]) == 1
    assert result["violations"]["dangling_edge_provenance"][0]["missing_target_id"] == "MISSING_EDGE_PROV"