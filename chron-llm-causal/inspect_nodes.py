import glob, json

# 1. Delta-1 Ground Truth の ID 収集
gt_nodes = set()
for path in glob.glob("data/delta1_normalized/*.json"):
    with open(path) as f:
        data = json.load(f)
        for n in data.get("nodes", []):
            if isinstance(n, dict) and "id" in n:
                gt_nodes.add(str(n["id"]))

print(f"Ground Truth Unique Nodes: {len(gt_nodes)}")
print(f"GT Sample IDs: {sorted(list(gt_nodes))[:5]}")

# 2. Traceability ファイルのノード照合確認
with open("data/audit/delta1_delta2_traceability_v1.json") as f:
    audit_data = json.load(f)

mappings = audit_data.get("node_mappings", [])
print(f"Total Mappings: {len(mappings)}")

match_orig = sum(1 for m in mappings if str(m.get("source_original_id")) in gt_nodes)
match_d1 = sum(1 for m in mappings if str(m.get("source_delta1_id")) in gt_nodes)

print(f"Matches using source_original_id: {match_orig}")
print(f"Matches using source_delta1_id  : {match_d1}")
