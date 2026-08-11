#!/usr/bin/env python3
"""
Component-004 廃止アーティファクトの自動退避およびバックアップスクリプト
"""

from pathlib import Path
import datetime
import shutil
import sys

# プロジェクトルート
ROOT_DIR = Path(__file__).parent.resolve()

# 1. 退避対象の定義 (相対パス)
DEPRECATED_TARGETS = [
    # architecture-v1 (Superseded by v1.1)
    "docs/ir/architecture-v1.spec",
    "docs/architecture-v1.md",
    # chron-llm-causal (Superseded by mature Phase D/E kernel)
    "llama-agent/ir/chron-llm-causal.spec",
    "llama-agent/chron-llm-causal.md",
    "llama-agent/chron-llm-causal.lisp",
]


def create_backup():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = ROOT_DIR / "archive" / f"backup_before_component004_merge_{timestamp}"
    print(f"📦 事前バックアップを作成中: {backup_dir}")

    # docs と llama-agent をバックアップ
    for src_dir in ["docs", "llama-agent"]:
        src_path = ROOT_DIR / src_dir
        if src_path.exists():
            dst_path = backup_dir / src_dir
            shutil.copytree(src_path, dst_path)

    print("✅ バックアップ完了\n")
    return backup_dir


def archive_files():
    deprecated_dir = ROOT_DIR / "archive" / "deprecated"
    superseded_dir = ROOT_DIR / "archive" / "superseded_specs"

    deprecated_dir.mkdir(parents=True, exist_ok=True)
    superseded_dir.mkdir(parents=True, exist_ok=True)

    print("🚀 廃止ファイルの移動処理を開始します...")

    for rel_path_str in DEPRECATED_TARGETS:
        src_file = ROOT_DIR / rel_path_str
        if not src_file.exists():
            print(f"⚠️  スキップ (ファイルが存在しません): {rel_path_str}")
            continue

        # architecture-v1 は superseded_specs、その他は deprecated へ
        if "architecture-v1." in src_file.name:
            dest_folder = superseded_dir
        else:
            dest_folder = deprecated_dir

        dest_file = dest_folder / src_file.name

        # 同名ファイルが存在する場合は上書き回避のため名前変更
        if dest_file.exists():
            dest_file = (
                dest_folder
                / f"{src_file.stem}_{datetime.datetime.now().strftime('%H%M%S')}{src_file.suffix}"
            )

        shutil.move(str(src_file), str(dest_file))
        print(f"  └─ 📁 移動: {rel_path_str} -> {dest_file.relative_to(ROOT_DIR)}")

    print("\n✅ 移動処理が完了しました。")


if __name__ == "__main__":
    try:
        create_backup()
        archive_files()
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)
