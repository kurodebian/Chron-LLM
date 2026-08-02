import json
import glob
from pathlib import Path
from collections import defaultdict

ACTION_KEYS = ["suggested_action", "recommendation", "action", "decision", "relationship"]

same_stem_pairs = []
constitution_pairs = []
other_overlaps = []

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

                    stem_a = Path(file_a).stem
                    stem_b = Path(file_b).stem
                    
                    # パターン1: ファイル幹（stem）が同じ、または極めて類似（.md / .spec / .lisp）
                    if stem_a == stem_b:
                        same_stem_pairs.append((file_a, file_b))
                    # パターン2: 憲法（Constitution/Specification）と個別仕様の重複
                    elif "Chron-" in file_a or "Constitution" in file_a or "Chron-" in file_b or "Constitution" in file_b:
                        constitution_pairs.append((file_a, file_b))
                    else:
                        other_overlaps.append((file_a, file_b))

    except Exception as e:
        print(f"⚠️ エラー [{filepath}]: {e}")

print("=== PARTIAL_OVERLAP サブパターン分析 ===")

print(f"\n🔹 【パターン1】同名・拡張子違い/フォーマット重複 ({len(same_stem_pairs)}件)")
for a, b in same_stem_pairs:
    print(f"  - {a}  <==>  {b}")

print(f"\n🔹 【パターン2】上位憲法 vs サブシステム仕様 ({len(constitution_pairs)}件)")
for a, b in constitution_pairs[:10]:  # 先頭10件を表示
    print(f"  - {a}  <==>  {b}")
if len(constitution_pairs) > 10:
    print(f"  ... 他 {len(constitution_pairs) - 10} 件")

print(f"\n🔹 【パターン3】仕様間の相互記述重複 ({len(other_overlaps)}件)")
for a, b in other_overlaps[:10]:
    print(f"  - {a}  <==>  {b}")
if len(other_overlaps) > 10:
    print(f"  ... 他 {len(other_overlaps) - 10} 件")
