#!/usr/bin/env python3
"""
廃止されたアーティファクト名・旧キーワードの参照残存チェックツール
"""

from pathlib import Path
import re
import sys

ROOT_DIR = Path(__file__).parent.resolve()

# 検索対象ディレクトリ (archive は除外)
SEARCH_DIRS = ["docs", "llama-agent", "specs", "runtime", "src", "tests"]

# 検出したい廃止文字列パターン
FORBIDDEN_PATTERNS = [
    r"architecture-v1\.spec",
    r"architecture-v1\.md",
    r"chron-llm-causal",
]


def check_references():
    print("🔍 廃止されたアーティファクトへの残留参照を走査中...")
    found_issues = 0

    for dir_name in SEARCH_DIRS:
        target_dir = ROOT_DIR / dir_name
        if not target_dir.exists():
            continue

        for file_path in target_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in [
                ".spec",
                ".md",
                ".lisp",
                ".asd",
                ".json",
            ]:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    for pattern in FORBIDDEN_PATTERNS:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            # 行番号の計算
                            line_no = (
                                content[: match.start()].count("\n") + 1
                            )
                            print(
                                f"❌ 残留検出: {file_path.relative_to(ROOT_DIR)} (Line {line_no}): '{match.group(0)}'"
                            )
                            found_issues += 1
                except Exception:
                    pass

    if found_issues == 0:
        print("✨ クリーンです！廃止されたファイルへの参照は見つかりませんでした。")
    else:
        print(f"\n⚠️ 合計 {found_issues} 箇所の残留参照が検出されました。修正が必要です。")


if __name__ == "__main__":
    check_references()
