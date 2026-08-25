"""
src/causal_kernel/kernel/validator.py
-------------------------------------
Delta2 Canonical MasterGraph の不変条件・整合性検証
"""

from typing import Any, Dict, List
import networkx as nx


class CausalGraphValidator:
    """Delta2 Canonical MasterGraph の不変条件検証"""

    def __init__(self, graph: nx.DiGraph):
        self.graph = graph

    def validate_all(self) -> Dict[str, Any]:
        violations = {
            "dangling_edges": self.check_dangling_edges(),
            "isolated_nodes": self.check_isolated_nodes(),
            "invariant_cycles": self.check_invariant_cycles(),
            "unconstrained_operations": self.check_unconstrained_operations(),
        }

        return {
            "is_valid": all(len(v) == 0 for v in violations.values()),
            "violations": violations,
        }

    def check_dangling_edges(self) -> List[str]:
        errors = []

        node_ids = set(self.graph.nodes())

        for u, v in self.graph.edges():
            if u not in node_ids:
                errors.append(f"Missing source node: {u}")

            if v not in node_ids:
                errors.append(f"Missing target node: {v}")

        return errors

    def check_isolated_nodes(self) -> List[str]:
        return [
            node
            for node in self.graph.nodes()
            if self.graph.degree(node) == 0
        ]

    def check_invariant_cycles(self) -> List[List[str]]:
        """
        現段階では、全グラフのcycleを検出する。
        
        注意:
        「全cycle = invariant cycle」とは意味論的に同値ではない。
        Phase 2-Aでは検出器として保持し、後段で
        invariant-only cycle の意味論を確定する。
        """
        try:
            return list(nx.simple_cycles(self.graph))
        except Exception:
            return []

    def check_unconstrained_operations(self) -> List[str]:
        """
        Delta2 node.type == operation/op のノードについて、
        invariant predecessor が存在するかを検証する。
        """

        unconstrained = []

        for node, attr in self.graph.nodes(data=True):
            node_type = str(attr.get("type", "")).lower()

            if node_type not in ("operation", "op"):
                continue

            predecessors = self.graph.predecessors(node)

            has_invariant = any(
                str(
                    self.graph.nodes[p].get("type", "")
                ).lower()
                in ("invariant", "inv")
                for p in predecessors
            )

            if not has_invariant:
                unconstrained.append(node)

        return unconstrained