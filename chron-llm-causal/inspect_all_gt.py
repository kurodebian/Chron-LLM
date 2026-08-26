import glob, json

gt_nodes = set()
key_counts = {}

for path in glob.glob("data/delta1_normalized/*.json"):
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict):
        for key, items in data.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and "id" in item:
                        gt_nodes.add(str(item["id"]))
                        key_counts[key] = key_counts.get(key, 0) + 1

print(f"Total Ground Truth Unique Node IDs: {len(gt_nodes)}")
print("ID sources by key:", key_counts)

# P001 〜 P012 の存在確認
p_nodes = [f"P{i:03d}" for i in range(1, 13)]
found_p = [p for p in p_nodes if p in gt_nodes]
print(f"\nP001-P012 found in GT: {len(found_p)} / 12")
print("Found IDs:", found_p)
