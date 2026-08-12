"""
examples/query_rag.py
----------------------
因果マスターグラフからのコンテキスト抽出および表示スクリプト
"""

import sys
from pathlib import Path
from causal_kernel.kernel.rag_interface import CausalRAGInterface


def main():
    json_path = Path("data/graphs/causal_master_graph_v2.json")
    if not json_path.exists():
        print(f"[Error] Graph JSON not found at: {json_path}")
        sys.exit(1)

    rag = CausalRAGInterface(json_path)

    keyword = "Commit"
    print(f"=== Search Nodes for '{keyword}' ===")

    # 1. 該当ノードの検索と表示
    matched_nodes = rag.search_nodes(keyword)
    if not matched_nodes:
        print("  (該当するノードが見つかりませんでした)")
    else:
        for node_id, data in matched_nodes.items():
            category = data.get("category", "State")
            label = data.get("label", "")
            desc = data.get("description", "")
            print(f"  - [{node_id}] [{category}] {label}")
            if desc:
                short_desc = desc[:70] + "..." if len(desc) > 70 else desc
                print(f"      概要: {short_desc}")

    print("\n=== LLM Prompt Injection Context ===")
    # 2. LLM プロンプトへ注入するための因果コンテキスト構築
    context_prompt = rag.generate_context_prompt(keyword)
    print(context_prompt)


if __name__ == "__main__":
    main()