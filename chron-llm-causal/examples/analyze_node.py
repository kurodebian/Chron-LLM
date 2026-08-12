"""
examples/analyze_node.py
------------------------
因果グラフのロード・検証・トラバース動作チェック
"""

import sys
from pathlib import Path

# src ディレクトリを Python パスに追加
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from causal_kernel.kernel.graph_loader import load_causal_graph


def main():
    graph_path = Path("data/graphs/causal_master_graph_v2.json")
    
    if not graph_path.exists():
        print(f"[ERROR] {graph_path} が存在しません。セットアップスクリプトでファイルを配置してください。")
        return

    print(f"=== Loading Master Graph from {graph_path} ===")
    graph, report = load_causal_graph(graph_path)

    print(f"\n[Graph Summary]")
    print(f"- Total Nodes: {graph.number_of_nodes()}")
    print(f"- Total Edges: {graph.number_of_edges()}")

    print(f"\n[Validation Report]")
    print(f"- Is Valid: {report['is_valid']}")
    if not report['is_valid']:
        print(f"- Violations: {report['violations']}")

    # ノード一覧の確認（先頭5件）
    print("\n[Sample Nodes]")
    for node_id, data in list(graph.nodes(data=True))[:5]:
        print(f"  * [{node_id}] {data.get('label')} ({data.get('category')})")


if __name__ == "__main__":
    main()