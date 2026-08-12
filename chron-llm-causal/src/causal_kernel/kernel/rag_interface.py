"""
src/causal_kernel/kernel/rag_interface.py
-----------------------------------------
因果マスターグラフからのコンテキスト抽出および LLM プロンプト整形インターフェース
"""

from pathlib import Path
from typing import Dict, Any, List, Set
import networkx as nx

from .graph_loader import load_causal_graph


class CausalRAGInterface:
    def __init__(self, json_path: str | Path):
        self.graph, self.validation_report = load_causal_graph(json_path)

    def search_nodes(self, keyword: str) -> Dict[str, Dict[str, Any]]:
        """
        キーワードによるノード検索
        ID, label, description, category のいずれかに部分一致（大文字小文字無視）でヒットしたものを返します。
        """
        kw_lower = keyword.lower()
        matched = {}
        for node_id, data in self.graph.nodes(data=True):
            label = str(data.get("label", ""))
            desc = str(data.get("description", ""))
            cat = str(data.get("category", ""))

            if (
                kw_lower in node_id.lower()
                or kw_lower in label.lower()
                or kw_lower in desc.lower()
                or kw_lower in cat.lower()
            ):
                matched[node_id] = data
        return matched

    def extract_subgraph(self, target_node_ids: List[str], depth: int = 1) -> nx.DiGraph:
        """指定したノード群とその周辺（1ホップ）の依存ノードを含めたサブグラフを抽出"""
        sub_nodes: Set[str] = set()
        for nid in target_node_ids:
            if nid in self.graph:
                sub_nodes.add(nid)
                # 依存元（前向）および依存先（後向）ノードを収集
                preds = nx.single_source_shortest_path_length(
                    self.graph.reverse(copy=False), nid, cutoff=depth
                )
                succs = nx.single_source_shortest_path_length(self.graph, nid, cutoff=depth)
                sub_nodes.update(preds.keys())
                sub_nodes.update(succs.keys())

        return self.graph.subgraph(sub_nodes).copy()

    def generate_context_prompt(self, keyword: str) -> str:
        """検索キーワードに関連するサブグラフ抽出し、LLMプロンプト注入用の文字列に整形"""
        matched = self.search_nodes(keyword)
        if not matched:
            return f"[Causal Context: No nodes matched keyword '{keyword}']"

        subgraph = self.extract_subgraph(list(matched.keys()))

        lines = [f"=== 因果グラフコンテキスト (検索語: '{keyword}') ==="]
        lines.append("\n【関連ノード】")
        for nid, attrs in subgraph.nodes(data=True):
            category = attrs.get("category", "State")
            label = attrs.get("label", nid)
            desc = attrs.get("description", "")
            desc_str = f" - {desc}" if desc else ""
            lines.append(f"  * [{nid}] ({category}) {label}{desc_str}")

        lines.append("\n【因果依存関係 (エッジ)】")
        if subgraph.number_of_edges() == 0:
            lines.append("  (関連するエッジはありません)")
        else:
            for u, v, attrs in subgraph.edges(data=True):
                rel = attrs.get("relation", "depends_on")
                evidence = attrs.get("evidence", "")
                ev_str = f" [根拠: {evidence}]" if evidence else ""
                lines.append(f"  * [{u}] --({rel})--> [{v}]{ev_str}")

        return "\n".join(lines)