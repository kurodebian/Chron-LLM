import json
from pathlib import Path

def audit_traceability():
    trace_path = Path("delta1_delta2_traceability.json")
    if not trace_path.exists():
        print(f"Error: {trace_path} not found in root directory.")
        return

    with open(trace_path, 'r', encoding='utf-8') as f:
        trace_data = json.load(f)

    print("=" * 60)
    print("=== TRACEABILITY CLAIMS VS ACTUAL AUDIT ===")
    print("=" * 60)
    print(f"Traceability Top-level Keys: {list(trace_data.keys())}")

    # レポートが保持している自己申告・チェック値の抽出
    checks = trace_data.get("machine_checks", {})
    if not checks:
        # 代替キーの探索
        for k, v in trace_data.items():
            if isinstance(v, dict) and any(subk in v for subk in ["NODE_COUNT", "node_count", "nodes"]):
                checks = v
                break

    print("\n[Reported Values in Traceability JSON]")
    print(json.dumps(checks, ensure_ascii=False, indent=2))

    # --- 1. Delta-1 の実測 ---
    delta1_dir = Path("data/delta1_normalized")
    actual_d1_nodes = 0
    actual_d1_edges = 0
    file_counts = 0
    
    if delta1_dir.exists():
        for file_path in delta1_dir.glob("causal_extract_*.json"):
            file_counts += 1
            try:
                with open(file_path, 'r', encoding='utf-8') as df:
                    d = json.load(df)
                    if "nodes" in d:
                        actual_d1_nodes += len(d["nodes"])
                    if "edges" in d:
                        actual_d1_edges += len(d["edges"])
                    if "proposals" in d:
                        actual_d1_nodes += len(d["proposals"]) # Proposalの数も計上
            except Exception as e:
                print(f"Warning: Failed to parse {file_path.name}: {e}")

    # --- 2. Delta-2 (MasterGraph) の実測 ---
    mg_path = Path("data/graphs/causal_master_graph_v2.json")
    actual_d2_nodes = 0
    actual_d2_edges = 0
    if mg_path.exists():
        with open(mg_path, 'r', encoding='utf-8') as mf:
            md = json.load(mf)
            actual_d2_nodes = len(md.get("nodes", []))
            actual_d2_edges = len(md.get("edges", []))

    print("\n[Independent Actual Measurements]")
    print(f"  - Delta-1 Processed Files: {file_counts}")
    print(f"  - Delta-1 Actual Nodes/Proposals: {actual_d1_nodes}")
    print(f"  - Delta-1 Actual Edges: {actual_d1_edges}")
    print(f"  - Delta-2 (MasterGraph) Actual Nodes: {actual_d2_nodes}")
    print(f"  - Delta-2 (MasterGraph) Actual Edges: {actual_d2_edges}")

    print("=" * 60)

if __name__ == "__main__":
    audit_traceability()