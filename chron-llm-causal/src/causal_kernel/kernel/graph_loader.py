"""
src/causal_kernel/kernel/graph_loader.py
-----------------------------------------
Canonical Delta2 MasterGraph JSON を読み込み、
Delta2MasterGraph モデル経由で NetworkX 有向グラフへ変換する。
"""

import json
from pathlib import Path
from typing import Tuple

import networkx as nx

from .models import Delta2MasterGraph
from .validator.graph_validator import CausalGraphValidator


class CausalGraphLoader:
    def __init__(self, json_path: str | Path):
        self.json_path = Path(json_path)
        self.container: Delta2MasterGraph | None = None
        self.graph: nx.DiGraph = nx.DiGraph()

    def load(self) -> nx.DiGraph:
        if not self.json_path.exists():
            raise FileNotFoundError(
                f"Master graph file not found: {self.json_path}"
            )

        with open(self.json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        self.container = Delta2MasterGraph.model_validate(raw_data)
        self.graph.clear()

        for node in self.container.nodes:
            self.graph.add_node(
                node.id,
                global_id=node.global_id,
                local_id=node.local_id,
                type=node.type,
                name=node.name,
                description=node.description,
                **node.properties,
            )

        for edge in self.container.edges:
            self.graph.add_edge(
                edge.from_,
                edge.to,
                id=edge.id,
                pipeline=edge.pipeline,
                morphism_type=edge.morphism_type,
                guard_invariant=edge.guard_invariant,
                delta_level=edge.delta_level,
            )

        return self.graph

    def validate(self):
        if self.graph.number_of_nodes() == 0:
            self.load()

        return CausalGraphValidator(self.graph).validate_all()


def load_causal_graph(
    json_path: str | Path,
) -> Tuple[nx.DiGraph, Delta2MasterGraph]:

    loader = CausalGraphLoader(json_path)
    graph = loader.load()

    return graph, loader.container