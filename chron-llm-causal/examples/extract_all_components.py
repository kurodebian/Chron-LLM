"""
scripts/run_extract_all.py
--------------------------
component-001.json ～ component-013.json からの Δ1 因果抽出と Mermaid 出力
(llama.cpp / Ollama マルチバックエンド対応 & 自動サマリーレポート機能付き)
"""

import glob
import json
import os
import sys
from typing import Any, Dict

from causal_kernel.extractor.extract_component import (
    extract_component_delta1,
    generate_component_mermaid,
)


def load_component_context(json_path: str) -> str:
    """JSON ファイルからコンポーネントの仕様書テキスト/コンテキストを抽出"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            if "context" in data:
                return str(data["context"])
            elif "text" in data:
                return str(data["text"])
            elif "content" in data:
                return str(data["content"])
            else:
                return json.dumps(data, ensure_ascii=False, indent=2)
        elif isinstance(data, list):
            return json.dumps(data, ensure_ascii=False, indent=2)
        else:
            return str(data)
    except Exception as e:
        print(f"[Warning] {json_path} の読み込みに失敗しました: {e}")
        return ""


def main():
    # バックエンドの判定 (llamacpp / ollama)
    backend = os.environ.get("LLM_BACKEND", "llamacpp").lower()

    # バックエンドに応じた Host / Model のデフォルト設定
    if backend == "ollama":
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        model = os.environ.get("OLLAMA_MODEL", "qwen2.5:32b")
    else:  # default: llamacpp
        host = os.environ.get("LLAMA_HOST", "http://127.0.0.1:8080")
        model = os.environ.get("LLAMA_MODEL", "Qwen3.6-35B-A3B-UD-Q4_K_M.gguf")

    # ディレクトリパスの設定
    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    context_dir = os.path.join(base_dir, "component_contexts")

    output_json_dir = os.path.join(base_dir, "data", "delta1_normalized")
    output_mmd_dir = os.path.join(base_dir, "output_mermaid")

    os.makedirs(output_json_dir, exist_ok=True)
    os.makedirs(output_mmd_dir, exist_ok=True)

    json_files = sorted(
        glob.glob(os.path.join(context_dir, "component-*.json"))
    )

    if not json_files:
        print(
            f"[Error] [{context_dir}] に 'component-*.json' が見つかりませんでした。"
        )
        sys.exit(1)

    print(f"合計 {len(json_files)} 件の component JSON ファイルを検出しました。")
    print(
        f"=== 設定情報: Backend={backend} | Host={host} | Model={model} ==="
    )

    # 集計用カウンター
    summary_stats = []

    for json_path in json_files:
        filename = os.path.basename(json_path)
        component_id = filename.replace(".json", "")

        spec_text = load_component_context(json_path)
        if not spec_text:
            print(f"\n[{component_id}] スキップ: テキストが存在しません。")
            summary_stats.append(
                {"id": component_id, "status": "SKIP", "nodes": 0, "edges": 0}
            )
            continue

        print(
            f"\n=================================================="
            f"\n=== [{component_id}] Δ1 因果構造抽出中 ({backend} / {model}) ==="
        )

        # 1. Δ1 抽出 & 正規化 (マルチバックエンド対応引数)
        delta1_data = extract_component_delta1(
            spec_text,
            component_id=component_id,
            host=host,
            model=model,
            backend=backend,
        )

        node_count = len(delta1_data.get("nodes", []))
        edge_count = len(delta1_data.get("edges", []))
        is_error = "error" in delta1_data

        # 2. JSON 保存
        json_out_path = os.path.join(
            output_json_dir, f"causal_extract_{component_id}_v1.json"
        )
        with open(json_out_path, "w", encoding="utf-8") as f:
            json.dump(delta1_data, f, ensure_ascii=False, indent=2)
        print(f"  └─ JSON 保存完了: {json_out_path}")

        # 3. Mermaid 生成 & 保存
        mermaid_code = generate_component_mermaid(delta1_data)
        mmd_out_path = os.path.join(output_mmd_dir, f"{component_id}.mmd")
        with open(mmd_out_path, "w", encoding="utf-8") as f:
            f.write(mermaid_code)
        print(f"  └─ Mermaid 保存完了: {mmd_out_path}")

        status_str = "ERROR" if is_error else ("EMPTY" if node_count == 0 else "OK")
        summary_stats.append(
            {
                "id": component_id,
                "status": status_str,
                "nodes": node_count,
                "edges": edge_count,
            }
        )

    # ------------------------------------------------------------------
    # 最終実行結果の集計サマリー表示
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("      全 Component Δ1 因果構造抽出 - 実行結果サマリー")
    print("=" * 60)
    print(f"{'Component ID':<18} | {'Status':<8} | {'Nodes':<6} | {'Edges':<6}")
    print("-" * 60)

    total_nodes = 0
    total_edges = 0
    for stat in summary_stats:
        print(
            f"{stat['id']:<18} | {stat['status']:<8} | {stat['nodes']:<6} | {stat['edges']:<6}"
        )
        total_nodes += stat["nodes"]
        total_edges += stat["edges"]

    print("-" * 60)
    print(
        f"合計: {len(summary_stats)} 件 | Node総数: {total_nodes} | Edge総数: {total_edges}"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()