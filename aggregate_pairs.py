import json
import glob
from collections import defaultdict

results = defaultdict(list)
files = sorted(
    glob.glob("pair_results/pair_*.json"),
    key=lambda x: int(x.split("_")[-1].split(".")[0]),
)

# 判定/アクションを示す可能性のあるキー一覧
ACTION_KEYS = [
    "suggested_action",
    "recommendation",
    "action",
    "decision",
    "relationship",
    "verdict",
    "result",
    "status",
    "comparison",
]

for filepath in files:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

            items = data.get("results") or data.get("processed_pairs") or [data]
            if isinstance(items, dict):
                items = [items]

            for item in items:
                rec = None
                # アクション/判定キーを自動探索
                for k in ACTION_KEYS:
                    if k in item and item[k]:
                        rec = str(item[k])
                        break

                if not rec:
                    rec = "UNKNOWN"

                file_a = (
                    item.get("file_a") or item.get("fileA") or item.get("file_1") or ""
                )
                file_b = (
                    item.get("file_b") or item.get("fileB") or item.get("file_2") or ""
                )

                if not file_a and "pair" in item and isinstance(item["pair"], dict):
                    file_a = item["pair"].get("file_a", "")
                    file_b = item["pair"].get("file_b", "")

                results[rec].append((file_a, file_b, filepath, item))
    except Exception as e:
        print(f"⚠️ Error parsing {filepath}: {e}")

print("=== 整理アクション集計 ===")
for rec, pairs in results.items():
    print(f"\n■ {rec} ({len(pairs)}件)")
    for a, b, fp, item in pairs:
        print(f"  - [{fp}] {a} <---> {b}")
        if rec == "UNKNOWN":
            print(f"    └ 保持されているキー一覧: {list(item.keys())}")
