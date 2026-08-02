#!/usr/bin/env python3
import glob
import json
import os
import networkx as nx


def is_spec(filename):
    """ファイルが純粋な .spec ファイルかどうかを判定"""
    return filename.lower().endswith(".spec")


def main():
    results_dir = "pair_results"
    output_file = "spec_relation_components.json"

    G = nx.Graph()
    observations_store = []

    print("🔍 Observation (pair_results) から関係構造を観測中...")

    # 1. グラフと観測履歴の分離抽出
    for filepath in glob.glob(os.path.join(results_dir, "pair_*.json")):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            for res in data.get("results", []):
                file_a = res.get("file_a", "")
                file_b = res.get("file_b", "")

                # .spec 同士のペアのみを対象とする
                if is_spec(file_a) and is_spec(file_b):
                    pair_id = os.path.basename(filepath)
                    sim = res.get("similarity_score", 0.0)

                    # グラフ構造には「純粋なトポロジーと類似度」のみを登録（判断を持ち込まない）
                    G.add_node(file_a)
                    G.add_node(file_b)
                    G.add_edge(
                        file_a,
                        file_b,
                        observed_similarity=sim,
                        observation=pair_id,
                    )

                    # AIの判断履歴は「Observations」として独立して別管理する
                    observations_store.append(
                        {
                            "pair_id": pair_id,
                            "source": file_a,
                            "target": file_b,
                            "similarity": sim,
                            "relationship": res.get("relationship"),
                            "recommended_action": res.get(
                                "recommended_action"
                            ),
                            "rationale": res.get("integration_rationale"),
                        }
                    )
        except Exception as e:
            print(f"⚠️ エラー [{filepath}]: {e}")

    # 2. 連結成分（Components）の抽出とデータ構造化
    components_output = {
        "metadata": {
            "total_spec_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "total_components": 0,
        },
        "components": [],
        "observations": observations_store,
    }

    for i, component in enumerate(nx.connected_components(G), 1):
        comp_id = f"component-{i:03d}"
        artifacts = sorted(list(component))

        relations = []
        sub_g = G.subgraph(component)
        for u, v, d in sub_g.edges(data=True):
            relations.append(
                {
                    "source": u,
                    "target": v,
                    "observed_similarity": d.get("observed_similarity"),
                    "observation": d.get("observation"),
                }
            )

        components_output["components"].append(
            {"id": comp_id, "artifacts": artifacts, "relations": relations}
        )

    # 構成要素（ファイル数）が多い順にソート
    components_output["components"].sort(
        key=lambda x: len(x["artifacts"]), reverse=True
    )
    components_output["metadata"]["total_components"] = len(
        components_output["components"]
    )

    # 3. JSONへの出力
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(components_output, f, ensure_ascii=False, indent=2)

    print("\n✅ Spec Relation Components の抽出が完了しました！")
    print(f" ┣ 対象SPECファイル数: {components_output['metadata']['total_spec_nodes']}")
    print(f" ┣ 抽出された独立コンポーネント数: {components_output['metadata']['total_components']}")
    print(f" ┗ 出力ファイル: '{output_file}'")


if __name__ == "__main__":
    main()
