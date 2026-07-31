import json
import glob
from collections import defaultdict

overlap_groups = defaultdict(list)
ACTION_KEYS = ["suggested_action", "recommendation", "action", "decision", "relationship"]

for filepath in sorted(glob.glob("pair_results/pair_*.json"), key=lambda x: int(x.split('_')[-1].split('.')[0])):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            items = data.get("results") or data.get("processed_pairs") or [data]
            if isinstance(items, dict):
                items = [items]

            for item in items:
                rel = None
                for k in ACTION_KEYS:
                    if k in item and item[k]:
                        rel = str(item[k])
                        break
                
                if rel == "PARTIAL_OVERLAP":
                    file_a = item.get("file_a") or item.get("fileA") or item.get("file_1") or ""
                    file_b = item.get("file_b") or item.get("fileB") or item.get("file_2") or ""
                    
                    if not file_a and "pair" in item and isinstance(item["pair"], dict):
                        file_a = item["pair"].get("file_a", "")
                        file_b = item["pair"].get("file_b", "")

                    # モジュールやディレクトリ単位で分類
                    mod = "other"
                    for m in ["runtime", "graph-runtime", "llama-agent", "world", "memory", "observability", "registry", "tests", "experiments"]:
                        if m in file_a or m in file_b:
                            mod = m
                            break
                    if "docs" in file_a or "docs" in file_b:
                        mod = "docs/specs"

                    overlap_groups[mod].append((file_a, file_b, filepath))
    except Exception as e:
        print(f"⚠️ エラー [{filepath}]: {e}")

print("=== PARTIAL_OVERLAP（部分重複）のモジュール別内訳 ===")
for mod, pairs in sorted(overlap_groups.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n📁 [{mod.upper()}] ({len(pairs)}件)")
    for a, b, fp in pairs:
        print(f"  - {a}  <==>  {b}")
