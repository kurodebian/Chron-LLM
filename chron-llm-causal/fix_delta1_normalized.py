import json
from pathlib import Path

target_dir = Path("data/delta1_normalized")

for json_path in target_dir.glob("*.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. ルート階層に proposals を設定
    if "proposals" not in data or data["proposals"] is None:
        data["proposals"] = []

    # 2. Node に origin を補完（明示的ノードとして設定）
    for node in data.get("nodes", []):
        if "origin" not in node or not node["origin"]:
            node["origin"] = "EXPLICIT_NODE"

    # 3. Edge にユニーク id を補完
    for idx, edge in enumerate(data.get("edges", [])):
        if "id" not in edge or not edge["id"]:
            edge["id"] = f"edge_{edge.get('from')}_{edge.get('to')}_{idx}"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

print("All normalized JSON files updated successfully.")