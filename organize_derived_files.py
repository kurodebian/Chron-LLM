import os
from pathlib import Path

ir_dir = Path("runtime/ir")

if not ir_dir.exists():
    print(f"⚠️ ディレクトリ {ir_dir} が見つかりません。")
    exit(1)

# .spec ファイルの幹名（stem）を取得
spec_stems = {f.stem for f in ir_dir.glob("*.spec")}

md_candidates = []
lisp_candidates = []

# .spec と同名の .md を抽出
for md_file in ir_dir.glob("*.md"):
    if md_file.stem in spec_stems:
        md_candidates.append(md_file)

# .spec と同名の .lisp を抽出
for lisp_file in ir_dir.glob("*.lisp"):
    if lisp_file.stem in spec_stems:
        lisp_candidates.append(lisp_file)

print("=== .spec を正本とした場合の削除対象（重複・派生ファイル） ===")

print(f"\n🗑️ 削除対象の .md ファイル ({len(md_candidates)}件):")
for f in md_candidates:
    print(f"  - {f}")

print(f"\n🗑️ 削除対象の .lisp ファイル ({len(lisp_candidates)}件):")
for f in lisp_candidates:
    print(f"  - {f}")

if not md_candidates and not lisp_candidates:
    print("\n✨ .spec と重複する .md / .lisp ファイルはありません。")
