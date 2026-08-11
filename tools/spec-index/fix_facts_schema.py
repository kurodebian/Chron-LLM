import json
import shutil
from pathlib import Path

# プロジェクトルートディレクトリの自動解決 (tools/spec-index/ から2階層上)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]

FACTS_PATH = PROJECT_ROOT / "spec-index" / "facts.jsonl"
BACKUP_PATH = PROJECT_ROOT / "spec-index" / "facts.jsonl.bak"
TMP_PATH = PROJECT_ROOT / "spec-index" / "facts.jsonl.tmp"


def count_lines(filepath: Path) -> int:
    """指定されたパスの行数をカウント"""
    if not filepath.exists():
        return 0
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def main():
    # バックアップが存在する場合は元データから読み込む
    source_path = BACKUP_PATH if BACKUP_PATH.exists() else FACTS_PATH

    if not source_path.exists():
        print(f"Error: 変換元ファイルが見つかりません。({source_path})")
        return

    # バックアップが存在しない場合のみ作成
    if not BACKUP_PATH.exists():
        shutil.copyfile(FACTS_PATH, BACKUP_PATH)
        print(f"Backed up {FACTS_PATH} -> {BACKUP_PATH}")

    cleaned_entries = []
    with open(source_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            file_bytes = data.get("bytes", data.get("size", 0))
            spec_path = data.get("spec_path", data.get("path", ""))

            # lines の取得（存在しない場合は実ファイルから行数を取得）
            lines = data.get("lines")
            if lines is None:
                if "line_count" in data:
                    lines = data["line_count"]
                elif spec_path:
                    lines = count_lines(PROJECT_ROOT / spec_path)
                else:
                    lines = 0

            # GATE-1 スキーマの許可フィールドのみでクリーンな辞書を作成
            cleaned_entry = {
                "spec_path": spec_path,
                "lines": lines,
                "bytes": file_bytes,
                "is_empty": (file_bytes == 0),
                "sha256": data.get("sha256", ""),
            }
            cleaned_entries.append(cleaned_entry)

    # アトミック書き込み
    with open(TMP_PATH, "w", encoding="utf-8") as f:
        for entry in cleaned_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    TMP_PATH.replace(FACTS_PATH)
    print(
        f"Successfully converted and updated {len(cleaned_entries)} entries in GATE-1 schema."
    )


if __name__ == "__main__":
    main()
