import json
import glob
import os
import shutil
from pathlib import Path

# 退避先ディレクトリ
ARCHIVE_DIR = Path("archive/superseded_specs")
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

ACTION_KEYS = [
    "suggested_action",
    "recommendation",
    "action",
    "decision",
    "relationship",
]
archived_files = set()

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

                if rel in ["SUPERSEDED", "EXACT_DUPLICATE"]:
                    file_b = (
                        item.get("file_b") or item.get("fileB") or item.get("file_2")
                    )
                    deprecated_target = (
                        item.get("deprecated_file")
                        or item.get("superseded_file")
                        or file_b
                    )

                    if deprecated_target and os.path.exists(deprecated_target):
                        archived_files.add(deprecated_target)

    except Exception as e:
        print(f"⚠️ エラー [{filepath}]: {e}")

print(f"📦 退避処理を実行します ({len(archived_files)} 件)\n")

for target in sorted(archived_files):
    src = Path(target)
    dest = ARCHIVE_DIR / src.name
    print(f"🚚 移動中: {src}  ===>  {dest}")
    shutil.move(str(src), str(dest))

print("\n✅ 退避処理が完了しました！")
