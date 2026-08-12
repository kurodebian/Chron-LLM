"""
src/causal_kernel/kernel/graph_loader.py
-----------------------------------------
JSON マスターグラフロードおよび NetworkX 有向グラフ変換
"""

import json
from pathlib import Path
from typing import Tuple, Dict, Any
import networkx as nx

from .models import MasterGraphContainer
from .validator import CausalGraphValidator


class CausalGraphLoader:
    def __init__(self, json_path: str | Path):
        self.json_path = Path(json_path)
        self.container: MasterGraphContainer | None = None
        self.graph: nx.DiGraph = nx.DiGraph()

    def load(self) -> nx.DiGraph:
        if not self.json_path.exists():
            raise FileNotFoundError(f"Master graph file not found: {self.json_path}")

        with open(self.json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        self.container = MasterGraphContainer(**raw_data)
        self.graph.clear()

        for node_id, node in self.container.nodes.items():
            category_val = node.category.value if hasattr(node.category, "value") else str(node.category)
            self.graph.add_node(
                node_id,
                label=node.label,
                category=category_val,
                description=node.description,
                **node.metadata
            )

        for edge in self.container.edges:
            relation_val = edge.relation.value if hasattr(edge.relation, "value") else str(edge.relation)
            self.graph.add_edge(
                edge.from_node,
                edge.to_node,
                id=edge.id,
                relation=relation_val,
                evidence=edge.evidence,
                source_proposals=edge.source_proposals,
                confidence=edge.confidence
            )

        return self.graph

    def validate(self) -> Dict[str, Any]:
        if self.graph.number_of_nodes() == 0:
            self.load()
        return CausalGraphValidator(self.graph).validate_all()


def load_causal_graph(json_path: str | Path) -> Tuple[nx.DiGraph, Dict[str, Any]]:
    loader = CausalGraphLoader(json_path)
    graph = loader.load()
    report = loader.validate()
    return graph, report