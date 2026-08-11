import os
import re

# 走査対象のSPECディレクトリ
SPEC_DIRS = ["docs/ir", "llama-agent/ir"]

# 廃止・存在しないはずのシンボル/ファイルキーワード
OBSOLETE_KEYWORDS = [
    "chron-llm-causal",
    "architecture-v1.spec",
    "node-id",
    "timestamp",
    "clock",
]

# 偽陽性（誤検知）を防止するための禁止規定文脈
# （これらの否定表現が含まれる行は仕様上正しい文脈としてスキップします）
EXCLUDE_PROHIBITION_PATTERNS = [
    "NO_TIMESTAMPS",
    "no external",
    "excludes wall-clock",
    "no timestamps",
    "no clock",
    "without timestamps",
]


def check_integrity():
    print("🔍 SPECファイル群の整合性検証を開始します...\n")
    errors = 0
    spec_files = []

    for s_dir in SPEC_DIRS:
        if not os.path.exists(s_dir):
            continue
        for root, _, files in os.walk(s_dir):
            for f in files:
                if f.endswith(".spec"):
                    spec_files.append(os.path.join(root, f))

    print(f"📄 対象SPECファイル ({len(spec_files)} 件):")
    for sf in spec_files:
        print(f"  - {sf}")
    print("-" * 50)

    for sf in spec_files:
        with open(sf, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # コメント行（//, #, ;）はスキップ
            if (
                stripped.startswith("//")
                or stripped.startswith("#")
                or stripped.startswith(";")
            ):
                continue

            # 1. 廃止キーワードのチェック
            for kw in OBSOLETE_KEYWORDS:
                if kw in line:
                    # 禁止規定の文脈であれば偽陽性としてスキップ
                    if any(
                        pattern.lower() in line.lower()
                        for pattern in EXCLUDE_PROHIBITION_PATTERNS
                    ):
                        continue

                    print(
                        f"❌ 廃止表現検出: {sf} (Line {line_num}): '{kw}' が残っています"
                    )
                    print(f"   > {stripped}")
                    errors += 1

            # 2. 未定義/型レベル不整合チェック (Int型/node-id等の残存など)
            if re.search(r"\bnode[-_]id\s*:\s*(Int|ID)\b", line, re.IGNORECASE):
                print(
                    f"❌ 型不整合検出: {sf} (Line {line_num}): 整数/ID型 node-id が検出されました (CausalID/Hashへの統一が必要です)"
                )
                errors += 1

    print("-" * 50)
    if errors == 0:
        print("✨ SPECの整合性チェックに合格しました！不整合・廃止参照はありません。")
    else:
        print(f"⚠️ 合計 {errors} 箇所の問題が検出されました。修正を行ってください。")


if __name__ == "__main__":
    check_integrity()
