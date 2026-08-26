import json, os

path = "data/delta1_normalized/causal_extract_commit_kernel_v1.json"
if os.path.exists(path):
    with open(path) as f:
        data = json.load(f)
    nodes = data.get("nodes", [])
    print(f"File: {path}")
    print(f"Total Nodes: {len(nodes)}")
    if nodes:
        print("\n--- Index 0 Node (First Node) ---")
        print(json.dumps(nodes[0], indent=2, ensure_ascii=False))
        print("\n--- First 5 Node IDs ---")
        print([n.get("id") for n in nodes[:5] if isinstance(n, dict)])
else:
    print(f"File not found: {path}")
