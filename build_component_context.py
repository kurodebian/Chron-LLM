#!/usr/bin/env python3
import json
import os


def load_file_content(filepath):
    """.spec ファイルの生テキストを読み込む"""
    if not os.path.exists(filepath):
        return f"[ERROR: File not found - {filepath}]"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"[ERROR reading {filepath}: {e}]"


def main():
    components_file = "spec_relation_components.json"
    output_dir = "component_contexts"
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(components_file):
        print(
            f"❌ '{components_file}' が見つかりません。先に build_spec_graph.py を実行してください。"
        )
        return

    with open(components_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    components = data.get("components", [])
    observations = {
        f"{o['source']}<->{o['target']}": o for o in data.get("observations", [])
    }
    # 逆方向検索用のインデックスも作成
    for o in data.get("observations", []):
        observations[f"{o['target']}<->{o['source']}"] = o

    print(f"📦 コンポーネントのパッキングを開始します（全 {len(components)} 件）...")

    for comp in components:
        comp_id = comp["id"]
        artifacts = comp["artifacts"]

        # 該当コンポーネント内の全 SPEC ファイルの生テキストを収集
        spec_payloads = []
        for path in artifacts:
            content = load_file_content(path)
            spec_payloads.append(
                {
                    "file_path": path,
                    "line_count": len(content.splitlines()),
                    "content": content,
                }
            )

        # 該当コンポーネントに関連する pair observation の収集
        related_observations = []
        for rel in comp.get("relations", []):
            src, tgt = rel["source"], rel["target"]
            key = f"{src}<->{tgt}"
            if key in observations:
                related_observations.append(observations[key])

        # パックされた文脈コンテキスト
        context_data = {
            "component_id": comp_id,
            "artifact_count": len(artifacts),
            "artifacts": spec_payloads,
            "observed_relationships": related_observations,
        }

        output_path = os.path.join(output_dir, f"{comp_id}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(context_data, f, ensure_ascii=False, indent=2)

    print(f"✅ パッキング完了！ '{output_dir}/' にコンテキストを出力しました。")


if __name__ == "__main__":
    main()
