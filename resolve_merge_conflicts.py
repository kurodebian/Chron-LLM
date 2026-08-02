import json
import glob
import os
from pathlib import Path
from collections import defaultdict

# 退避済み・移動済みの旧版 .spec -> 現存する最新 .spec のリダイレクトのみを定義
CANONICAL_REDIRECTS = {
    "docs/ir/architecture-v1.spec": "docs/ir/architecture-v1.1.spec",
}

def resolve_target(filepath):
    """リダイレクト辞書を辿って最終的な .spec ファイルを取得"""
    curr = filepath
    visited = set()
    while curr in CANONICAL_REDIRECTS and curr not in visited:
        visited.add(curr)
        curr = CANONICAL_REDIRECTS[curr]
    return curr

ACTION_KEYS = ["suggested_action", "recommendation", "recommended_action", "action", "decision", "relationship"]

final_merge_map = defaultdict(set)
ignored_non_specs = set()
skipped_reasons = []

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

                rec_action = str(item.get("recommended_action") or item.get("suggested_action") or "")

                if rel == "PARTIAL_OVERLAP" or "MERGE" in rec_action:
                    file_a = item.get("file_a") or item.get("fileA") or item.get("file_1") or ""
                    file_b = item.get("file_b") or item.get("fileB") or item.get("file_2") or ""

                    if not file_a and "pair" in item and isinstance(item["pair"], dict):
                        file_a = item["pair"].get("file_a", "")
                        file_b = item["pair"].get("file_b", "")

                    if "MERGE_A_INTO_B" in rec_action:
                        src, tgt = file_a, file_b
                    else:
                        src, tgt = file_b, file_a  # 基本は B -> A

                    # リダイレクト解決
                    final_tgt = resolve_target(tgt)
                    final_src = resolve_target(src)

                    # 💡 .spec 以外は対象外とする
                    if not final_src.endswith(".spec") or not final_tgt.endswith(".spec"):
                        if not final_src.endswith(".spec"):
                            ignored_non_specs.add(final_src)
                        if not final_tgt.endswith(".spec"):
                            ignored_non_specs.add(final_tgt)
                        continue

                    # 同一ファイルチェック
                    if final_src == final_tgt:
                        continue

                    # 実在チェック
                    if os.path.exists(final_src) and os.path.exists(final_tgt):
                        final_merge_map[final_tgt].add(final_src)
                    else:
                        missing = []
                        if not os.path.exists(final_src): missing.append(f"統合元不在: {final_src}")
                        if not os.path.exists(final_tgt): missing.append(f"統合先不在: {final_tgt}")
                        skipped_reasons.append(f"{filepath}: {', '.join(missing)}")

    except Exception as e:
        print(f"⚠️ エラー [{filepath}]: {e}")

print("=== 🎯 【.spec 限定】最終マージ・統合計画一覧 ===")
if final_merge_map:
    for target, sources in sorted(final_merge_map.items()):
        print(f"\n📄 統合先正本 (.spec): 【 {target} 】")
        print(f"   └─ 集約・統合対象 (.spec) ({len(sources)} 件):")
        for src in sorted(sources):
            print(f"       • {src}")
else:
    print("\n⚠️ マージ対象となる .spec ペアが見つかりませんでした。")

if ignored_non_specs:
    print(f"\n🚫 対象外として除外された非.specファイル ({len(ignored_non_specs)}件):")
    for f in sorted(ignored_non_specs):
        print(f"   - {f}")

if skipped_reasons:
    print(f"\n👻 スキップされた理由（ファイル不在など） ({len(skipped_reasons)}件):")
    for r in sorted(skipped_reasons[:10]):
        print(f"   - {r}")
    if len(skipped_reasons) > 10:
        print(f"   ... 他 {len(skipped_reasons) - 10} 件")