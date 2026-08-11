import json
import glob
import os
from pathlib import Path
from collections import defaultdict

ACTION_KEYS = [
    "suggested_action",
    "recommendation",
    "recommended_action",
    "action",
    "decision",
    "relationship",
]

# 記録用データ構造
to_keep_targets = defaultdict(
    list
)  # 統合先（残す側）として挙げられたファイル -> 根拠ペア
to_delete_targets = defaultdict(
    list
)  # 削除/退避対象（SUPERSEDED / EXACT_DUPLICATE / マージ元） -> 根拠ペア

for filepath in sorted(
    glob.glob("pair_results/pair_*.json"),
    key=lambda x: int(x.split("_")[-1].split(".")[0]),
):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
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

                file_a = (
                    item.get("file_a") or item.get("fileA") or item.get("file_1") or ""
                )
                file_b = (
                    item.get("file_b") or item.get("fileB") or item.get("file_2") or ""
                )
                rec_action = str(
                    item.get("recommended_action") or item.get("suggested_action") or ""
                )

                # 1. 削除/退避対象の記録
                if rel in ["SUPERSEDED", "EXACT_DUPLICATE"]:
                    deprecated_target = (
                        item.get("deprecated_file")
                        or item.get("superseded_file")
                        or file_b
                    )
                    if deprecated_target:
                        to_delete_targets[deprecated_target].append((filepath, rel))

                # 2. マージ関係の記録 (MERGE_B_INTO_A など)
                if "MERGE_B_INTO_A" in rec_action or (
                    rel == "PARTIAL_OVERLAP" and file_a
                ):
                    # file_a が統合先（残す側）、file_b が統合元（マージされる側）
                    if file_a:
                        to_keep_targets[file_a].append(
                            (filepath, f"Target of {file_b}")
                        )
                    if file_b:
                        to_delete_targets[file_b].append(
                            (filepath, f"Merged into {file_a}")
                        )

                elif "MERGE_A_INTO_B" in rec_action:
                    if file_b:
                        to_keep_targets[file_b].append(
                            (filepath, f"Target of {file_a}")
                        )
                    if file_a:
                        to_delete_targets[file_a].append(
                            (filepath, f"Merged into {file_b}")
                        )

    except Exception as e:
        print(f"⚠️ エラー [{filepath}]: {e}")

print("=== 🛠️ 統合先（マージ先）の整合性チェック結果 ===\n")

# チェック 1: 統合先に指定されているが、実ファイルが存在しない（既に削除・退避済み）
missing_targets = []
for keep_file, pairs in to_keep_targets.items():
    if not os.path.exists(keep_file):
        missing_targets.append((keep_file, pairs))

print(
    f"🚨 [衝突1] 退避・削除済みだが「統合先」に指定されているファイル ({len(missing_targets)} 件):"
)
if missing_targets:
    for target, pairs in missing_targets:
        print(f"  ❌ {target}")
        for fp, reason in pairs:
            print(f"     └─ 参照元: {fp} ({reason})")
else:
    print("  ✅ 該当なし（全ての統合先ファイルは現存しています）")

print("\n" + "=" * 60 + "\n")

# チェック 2: 「統合先」に指定されているが、別ペアで「削除/マージ元」に指定されている（相互矛盾）
conflicted_targets = []
for keep_file in to_keep_targets.keys():
    if keep_file in to_delete_targets:
        conflicted_targets.append(
            (keep_file, to_keep_targets[keep_file], to_delete_targets[keep_file])
        )

print(
    f"🚨 [衝突2] 「統合先」と「削除/統合元」の両方に指定されている矛盾ファイル ({len(conflicted_targets)} 件):"
)
if conflicted_targets:
    for target, keep_reasons, delete_reasons in conflicted_targets:
        print(f"  ⚠️ {target}")
        for fp, reason in keep_reasons:
            print(f"     ├─ [保持/統合先]: {fp} ({reason})")
        for fp, reason in delete_reasons:
            print(f"     └─ [削除/統合元]: {fp} ({reason})")
else:
    print("  ✅ 該当なし（マージ先と削除対象の不一致はありません）")
