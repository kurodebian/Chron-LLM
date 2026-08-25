"""
src/causal_kernel/kernel/validator/reference_validator.py
---------------------------------------------------------
JSON Schema パス後、NetworkX 変換前における
参照存在性 (Reference Existence - P1-A) の O(N+E) 線形検証
"""

from typing import Any, Dict, List, Set, Union
from ..models import Delta1Graph, Delta2MasterGraph


class ReferenceValidator:
    """ノード ID、エッジ端点、Guard Invariant、Provenance の参照存在性検証"""

    def __init__(
        self,
        container: Union[Delta1Graph, Delta2MasterGraph],
        traceability_data: Union[Dict[str, Any], None] = None,
    ):
        self.container = container
        self.traceability_data = traceability_data

    def validate_all_references(self) -> Dict[str, Any]:
        node_ids = {node.id for node in self.container.nodes}
        edge_ids = {edge.id for edge in self.container.edges}

        dangling_endpoints = self.check_edge_endpoints(node_ids)
        dangling_guards = self.check_guard_invariants(node_ids)
        dangling_node_prov, dangling_edge_prov = self.check_provenance_references(
            node_ids, edge_ids
        )

        violations = {
            "dangling_edge_endpoints": dangling_endpoints,
            "dangling_guard_invariants": dangling_guards,
            "dangling_node_provenance": dangling_node_prov,
            "dangling_edge_provenance": dangling_edge_prov,
        }

        is_valid = all(len(v) == 0 for v in violations.values())

        return {
            "is_valid": is_valid,
            "violations": violations,
        }

    def check_edge_endpoints(self, node_ids: Set[str]) -> List[Dict[str, Any]]:
        """Edge.from / Edge.to が実在する Node ID を参照しているか検証"""
        errors = []
        for edge in self.container.edges:
            if edge.from_ not in node_ids:
                errors.append({
                    "edge_id": edge.id,
                    "field": "from",
                    "missing_id": edge.from_,
                })
            if edge.to not in node_ids:
                errors.append({
                    "edge_id": edge.id,
                    "field": "to",
                    "missing_id": edge.to,
                })
        return errors

    def check_guard_invariants(self, node_ids: Set[str]) -> List[Dict[str, Any]]:
        """Edge.guard_invariant 内の ID が実在する Node ID を参照しているか検証 (Delta2)"""
        errors = []
        if not isinstance(self.container, Delta2MasterGraph):
            return errors

        for edge in self.container.edges:
            for inv_id in edge.guard_invariant:
                if inv_id not in node_ids:
                    errors.append({
                        "edge_id": edge.id,
                        "field": "guard_invariant",
                        "missing_id": inv_id,
                    })
        return errors

    def check_provenance_references(
        self, node_ids: Set[str], edge_ids: Set[str]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Traceability SSOT (delta2_nodes_provenance / delta2_edges_provenance) 参照検証"""
        node_errors = []
        edge_errors = []

        if not self.traceability_data:
            return node_errors, edge_errors

        # delta2_nodes_provenance 参照検証
        for mapping in self.traceability_data.get("delta2_nodes_provenance", []):
            target_id = mapping.get("delta2_node_id")
            if target_id and target_id not in node_ids:
                node_errors.append({
                    "mapping_type": "delta2_node_provenance",
                    "missing_target_id": target_id,
                })

        # delta2_edges_provenance 参照検証
        for mapping in self.traceability_data.get("delta2_edges_provenance", []):
            target_id = mapping.get("delta2_edge_id")
            if target_id and target_id not in edge_ids:
                edge_errors.append({
                    "mapping_type": "delta2_edge_provenance",
                    "missing_target_id": target_id,
                })

        return node_errors, edge_errors