import json
from pathlib import Path

def audit_delta2():
    mg_path = Path("data/graphs/causal_master_graph_v2.json")
    if not mg_path.exists():
        print(f"Error: {mg_path} not found.")
        return

    with open(mg_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    print("=" * 60)
    print("=== DELTA-2 MASTER GRAPH AUDIT ===")
    print("=" * 60)
    print(f"Total Nodes: {len(nodes)}")
    print(f"Total Edges: {len(edges)}")
    
    # ノードタイプの集計
    print("\n--- Node Types ---")
    node_types = {}
    for n in nodes:
        nt = n.get("type", "unknown")
        node_types[nt] = node_types.get(nt, 0) + 1
    for nt, count in node_types.items():
        print(f"  - {nt}: {count}")

    # エッジの morphism_type 集計
    print("\n--- Edge Morphism Types ---")
    morphism_types = {}
    for e in edges:
        mt = e.get("morphism_type", "unknown")
        morphism_types[mt] = morphism_types.get(mt, 0) + 1
    for mt, count in morphism_types.items():
        print(f"  - {mt}: {count}")

    # プロヴァナンス（起原・紐付け情報）の有無をチェック
    print("\n--- Provenance & Properties Check ---")
    nodes_with_provenance = 0
    for n in nodes:
        props = n.get("properties", {})
        # プロパティやメタデータにDelta-1への言及があるか
        if any(k in props for k in ["source", "provenance", "delta1_ref", "origin", "guard_token"]):
            nodes_with_provenance += 1

    print(f"Nodes with auxiliary properties (e.g., guard_token, provenance): {nodes_with_provenance} / {len(nodes)}")

    print("\n--- Sample Node Structure ---")
    if nodes:
        print(json.dumps(nodes[0], ensure_ascii=False, indent=2))

    print("\n--- Sample Edge Structure ---")
    if edges:
        print(json.dumps(edges[0], ensure_ascii=False, indent=2))
    print("=" * 60)

if __name__ == "__main__":
    audit_delta2()