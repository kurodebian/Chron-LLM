import json
from pathlib import Path

DELTA1_DIR = Path("data/delta1_normalized")

def inspect_and_verify():
    files = sorted(DELTA1_DIR.glob("causal_extract_*.json"))
    if not files:
        print("❌ No normalized JSON files found in data/delta1_normalized")
        return

    # 先頭ファイルでキー構造をアタリ付け
    sample_data = json.loads(files[0].read_text(encoding="utf-8"))
    sample_edges = sample_data.get("edges", [])
    
    if sample_edges:
        sample_edge = sample_edges[0]
        print(f"ℹ️ Sample edge structure in {files[0].name}:")
        print(f"   Keys: {list(sample_edge.keys())}")
        print(f"   Content: {sample_edge}")
        print("-" * 60)

    print(f"=== Delta-1 Normalized Data Validation ({len(files)} files) ===")
    
    total_nodes = 0
    total_edges = 0
    errors_found = 0

    for json_path in files:
        comp_name = json_path.stem.replace("causal_extract_", "").replace("_v1", "")
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[ERROR] {comp_name}: Failed to parse JSON ({e})")
            errors_found += 1
            continue

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        node_ids = {n["id"] for n in nodes if isinstance(n, dict) and "id" in n}

        # 柔軟なキー取得 (source / from / src / cause / from_node 対応)
        dangling_edges = []
        for idx, e in enumerate(edges):
            src = e.get("source") or e.get("from") or e.get("src") or e.get("cause") or e.get("from_node")
            tgt = e.get("target") or e.get("to") or e.get("dst") or e.get("effect") or e.get("to_node")

            if src is None or tgt is None:
                dangling_edges.append(f"Edge[{idx}] missing key structure: {e}")
                continue

            if src not in node_ids:
                dangling_edges.append(f"Missing source node: '{src}'")
            if tgt not in node_ids:
                dangling_edges.append(f"Missing target node: '{tgt}'")

        status = "OK" if not dangling_edges else "ERROR"
        if status == "ERROR":
            errors_found += 1

        total_nodes += len(nodes)
        total_edges += len(edges)

        print(f"[{status}] {comp_name:<25} | Nodes: {len(nodes):>2} | Edges: {len(edges):>2}")
        if dangling_edges:
            for err in dangling_edges[:3]:
                print(f"  └── {err}")

    print("-" * 60)
    print(f"Summary: {len(files) - errors_found}/{len(files)} Passed | Total Nodes: {total_nodes} | Total Edges: {total_edges}")

if __name__ == "__main__":
    inspect_and_verify()
