"""
src/causal_kernel/kernel/validator/graph_validator.py
----------------------------------------------------
Delta2 Canonical MasterGraph の構造・グラフ不変条件検証
"""

from typing import Any, Dict, List
import networkx as nx


class CausalGraphValidator:
    """Canonical Delta2 MasterGraph のグラフ不変条件検証"""

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
            "is_valid": all(not values for values in violations.values()),
            "violations": violations,
        }

    def check_dangling_edges(self) -> List[str]:
        errors = []

        for u, v in self.graph.edges():
            if u not in self.graph:
                errors.append(f"Missing source node: {u}")

            if v not in self.graph:
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
        現段階では構造的な全有向サイクルを返す。
        ※ P1 にて意味論的な invariant-cycle 検出へ再定義予定。
        """
        try:
            return list(nx.simple_cycles(self.graph))
        except Exception:
            return []

    def check_unconstrained_operations(self) -> List[str]:
        unconstrained = []

        for node, attr in self.graph.nodes(data=True):
            node_type = str(attr.get("type", "")).lower()

            if node_type not in ("operation", "op"):
                continue

            predecessors = self.graph.predecessors(node)

            has_invariant = any(
                str(
                    self.graph.nodes[p].get("type", "")
                ).lower() in ("invariant", "inv")
                for p in predecessors
            )

            if not has_invariant:
                unconstrained.append(node)

        return unconstrained

# Backward-compatible public API alias.
GraphValidator = CausalGraphValidator
# Backward-compatible public API alias.
GraphValidator = CausalGraphValidator
