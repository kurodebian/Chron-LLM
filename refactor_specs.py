#!/usr/bin/env python3
"""
refactor_specs.py - Spec Refactoring Helper for Chron-LLM
フェーズ1〜3の自動化処理（バックアップ、ファイル統合、型名置換、IMPORTヘッダー挿入）を実行します。
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

# ルートディレクトリ
BASE_DIR = Path(__file__).parent.resolve()
BACKUP_DIR = (
    BASE_DIR
    / "archive"
    / f"backup_before_merge_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
)

# 1. 統合対象ペア
MERGE_PAIRS = [
    {
        "src": BASE_DIR / "runtime/r1/ir/package.spec",
        "dst": BASE_DIR / "runtime/r1/ir/core.spec",
        "label": "Phase 1: package.spec -> core.spec",
    },
    {
        "src": BASE_DIR / "docs/ir/04-runtime-pipeline.spec",
        "dst": BASE_DIR / "docs/ir/02-operational-semantics.spec",
        "label": "Phase 2: 04-runtime-pipeline.spec -> 02-operational-semantics.spec",
    },
]

# 2. 一括置換ルール (Phase 3: 型・フィールド名の統一)
TEXT_REPLACEMENTS = {
    # Event の content -> payload 置換 (構造文脈に応じた置換)
    r"(\bEvent\s*:\s*\{[^}]*)\bcontent\b": r"\1payload",
    # 明示的な型置換
    r"\bRuntimeRequest\b": "KernelAction",
}

# 3. 各層ごとの IMPORT ヘッダー挿入ルール
IMPORT_HEADERS = {
    BASE_DIR
    / "docs/ir/02-operational-semantics.spec": "IMPORT ir::01-domain-model AS Schema\n\n",
    BASE_DIR / "runtime/r1/ir/core.spec": "IMPORT ir::01-domain-model AS Schema\n\n",
    BASE_DIR
    / "docs/ir/07-chron-mapping.spec": "IMPORT ir::01-domain-model AS Schema\nIMPORT runtime::r1::core AS Core\n\n",
}


def create_backup():
    """現在の spec ファイル群を archive にバックアップ"""
    print(f"📦 バックアップを作成中: {BACKUP_DIR}")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    spec_files = list(BASE_DIR.glob("**/*.spec"))
    for file in spec_files:
        rel_path = file.relative_to(BASE_DIR)
        dest_path = BACKUP_DIR / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, dest_path)
    print(f"✅ {len(spec_files)} 件の .spec ファイルをバックアップしました。\n")


def execute_merges(dry_run=False):
    """Phase 1 & Phase 2: ファイルの結合と旧ファイルの退避"""
    print("🔄 Phase 1 & 2: 仕様書ファイルの統合処理を開始...")
    superseded_dir = BASE_DIR / "archive" / "superseded_specs"
    superseded_dir.mkdir(parents=True, exist_ok=True)

    for pair in MERGE_PAIRS:
        src, dst, label = pair["src"], pair["dst"], pair["label"]
        print(f"  ▶ {label}")
        if not src.exists() or not dst.exists():
            print(f"    ⚠️ スキップ: {src.name} または {dst.name} が存在しません。")
            continue

        if not dry_run:
            # src の内容を dst の末尾に結合（手作業推敲用ブロックとして追加）
            with open(src, "r", encoding="utf-8") as f_src:
                src_content = f_src.read()

            with open(dst, "a", encoding="utf-8") as f_dst:
                f_dst.write(f"\n\n# ==========================================\n")
                f_dst.write(f"# MERGED FROM: {src.name}\n")
                f_dst.write(f"# (Please refactor and remove duplicate logic)\n")
                f_dst.write(f"# ==========================================\n\n")
                f_dst.write(src_content)

            # 統合元ファイルを superseded フォルダへ移動
            shutil.move(src, superseded_dir / src.name)
            print(
                f"    ✅ {src.name} を {dst.name} に結合し、archive/superseded_specs/ に移動しました。"
            )
        else:
            print(
                f"    [Dry-run] {src.name} -> {dst.name} への結合シミュレーション完了。"
            )
    print()


def apply_type_replacements(dry_run=False):
    """Phase 3: 全 spec ファイルにおける表記揺れの一括置換と IMPORT 挿入"""
    print("📝 Phase 3: 型名統一および IMPORT ヘッダーの自動挿入...")
    spec_files = list(BASE_DIR.glob("**/*.spec"))

    for file_path in spec_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        new_content = content
        # 表記揺れの置換
        for pattern, repl in TEXT_REPLACEMENTS.items():
            new_content = re.sub(pattern, repl, new_content)

        # IMPORT ヘッダーの挿入（未挿入の場合のみ）
        if file_path in IMPORT_HEADERS:
            import_stmt = IMPORT_HEADERS[file_path]
            if "IMPORT " not in new_content:
                new_content = import_stmt + new_content
                print(
                    f"  ➕ {file_path.relative_to(BASE_DIR)} に IMPORT ヘッダーを追加しました。"
                )

        if new_content != content:
            if not dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"  ✏️ {file_path.relative_to(BASE_DIR)} を更新しました。")
            else:
                print(
                    f"  [Dry-run] {file_path.relative_to(BASE_DIR)} の更新対象を検出。"
                )

    print("\n✅ 置換・ヘッダー挿入完了。\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Chron-LLM Spec Refactoring Tool")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際の変更を行わずにシミュレーションを実行します",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("🔍 --- DRY RUN MODE --- 🔍\n")

    if not args.dry_run:
        create_backup()

    execute_merges(dry_run=args.dry_run)
    apply_type_replacements(dry_run=args.dry_run)

    print("🎉 自動処理フェーズが完了しました。")
    print(
        "👉 次の手順: 結合された `02-operational-semantics.spec` および `core.spec` を開き、"
    )
    print(
        "   手作業（またはLLM）で末尾に追記されたブロックの整理・重複削除を行ってください。"
    )


if __name__ == "__main__":
    main()
