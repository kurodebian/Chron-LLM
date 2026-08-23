#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def extract_component_nodes(start_id: int = 1, end_id: int = 5):
    base_dir = Path("./data/delta1_normalized")
    extracted_data = {}

    for i in range(start_id, end_id + 1):
        comp_id = f"component-{i:03d}"
        file_path = base_dir / f"causal_extract_{comp_id}_v1.json"

        if not file_path.exists():
            print(f"[Warning] File not found: {file_path}", file=sys.stderr)
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                extracted_data[comp_id] = {
                    "component_id": data.get("component_id", comp_id),
                    "nodes": data.get("nodes", []),
                }
        except Exception as e:
            print(f"[Error] Failed to parse {file_path}: {e}", file=sys.stderr)

    print(json.dumps(extracted_data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # デフォルトで 001 〜 005 を抽出（引数指定で範囲変更可能）
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    extract_component_nodes(start, end)