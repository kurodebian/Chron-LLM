import json
from collections import Counter

# JSONファイルの読み込み
with open("data/audit/delta1_delta2_traceability_v1.json", encoding="utf-8") as f:
    data = json.load(f)

mappings = data.get("edge_mappings", [])

tuples_no_comp = []
tuples_with_comp = []

for m in mappings:
    f_node = m.get("from_node_id") or m.get("source_from")
    t_node = m.get("to_node_id") or m.get("source_to")
    rel = m.get("relation") or m.get("relation_type")
    comp = m.get("component_id")

    tuples_no_comp.append((f_node, t_node, rel))
    tuples_with_comp.append((comp, f_node, t_node, rel))

counts_no_comp = Counter(tuples_no_comp)
counts_with_comp = Counter(tuples_with_comp)

print("=== 重複検出結果 ===")
print(f"component_id 無視での重複グループ数: {sum(1 for v in counts_no_comp.values() if v > 1)}")
print(f"component_id 含めでの重複グループ数: {sum(1 for v in counts_with_comp.values() if v > 1)}")

for k, v in counts_no_comp.items():
    if v > 1:
        print(f"\n重複キー ({v}回出現): {k}")
