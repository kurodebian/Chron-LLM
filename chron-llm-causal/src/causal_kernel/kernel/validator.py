"""
src/causal_kernel/kernel/validator.py
-------------------------------------
因果グラフ不変条件・整合性検証エンジン
"""

from typing import Any, Dict, List
import networkx as nx
from .models import NodeCategory


class CausalGraphValidator:
    """因果マスターグラフの不変条件検証"""

    def __init__(self, graph: nx.DiGraph):
        self.graph = graph

    def validate_all(self) -> Dict[str, Any]:
        violations = {
            "dangling_edges": self.check_dangling_edges(),
            "isolated_nodes": self.check_isolated_nodes(),
            "invariant_cycles": self.check_invariant_cycles(),
            "unconstrained_operations": self.check_unconstrained_operations()
        }
        return {
            "is_valid": sum(len(v) for v in violations.values()) == 0,
            "violations": violations
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
        return [node for node in self.graph.nodes() if self.graph.degree(node) == 0]

    def check_invariant_cycles(self) -> List[List[str]]:
        try:
            return list(nx.simple_cycles(self.graph))
        except Exception:
            return []

    def check_unconstrained_operations(self) -> List[str]:
        unconstrained = []
        for node, attr in self.graph.nodes(data=True):
            category = str(attr.get("category", "")).lower()
            if category in ("operation", "op"):
                predecessors = self.graph.predecessors(node)
                has_invariant = any(
                    str(self.graph.nodes[p].get("category", "")).lower() in ("invariant", "inv")
                    for p in predecessors
                )
                if not has_invariant:
                    unconstrained.append(node)
        return unconstrained