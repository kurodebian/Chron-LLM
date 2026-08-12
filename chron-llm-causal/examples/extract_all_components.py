"""
component-001.json ～ component-013.json からの Δ1 因果抽出と Mermaid 出力
"""

import glob
import json
import os
from causal_kernel.extractor.extract_component import (
    extract_component_delta1,
    generate_component_mermaid,
)


def load_component_context(json_path: str) -> str:
    """JSON ファイルからコンポーネントの仕様書テキスト/コンテキストを抽出"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # JSON 内のテキストプロパティを探索 (構造に応じて調整)
        if isinstance(data, dict):
            if "context" in data:
                return str(data["context"])
            elif "text" in data:
                return str(data["text"])
            elif "content" in data:
                return str(data["content"])
            else:
                # 辞書全体をフォーマットテキスト化
                return json.dumps(data, ensure_ascii=False, indent=2)
        elif isinstance(data, list):
            return json.dumps(data, ensure_ascii=False, indent=2)
        else:
            return str(data)
    except Exception as e:
        print(f"[Warning] {json_path} の読み込みに失敗しました: {e}")
        return ""


def main():
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "qwen2.5:32b")

    # 相対パスで ../component_contexts を指定（Chron-LLM/component_contexts）
    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    context_dir = os.path.join(base_dir, "component_contexts")

    output_json_dir = "data/delta1_normalized"
    output_mmd_dir = "output_mermaid"

    os.makedirs(output_json_dir, exist_ok=True)
    os.makedirs(output_mmd_dir, exist_ok=True)

    # component-*.json ファイルを取得
    json_files = sorted(
        glob.glob(os.path.join(context_dir, "component-*.json"))
    )

    if not json_files:
        print(
            f"[Error] [{context_dir}] に 'component-*.json' が見つかりませんでした。"
        )
        return

    print(
        f"合計 {len(json_files)} 件の component JSON ファイルを検出しました。"
    )

    for json_path in json_files:
        filename = os.path.basename(json_path)
        component_id = filename.replace(".json", "")

        spec_text = load_component_context(json_path)
        if not spec_text:
            print(f"[{component_id}] スキップ: テキストが存在しません。")
            continue

        print(
            f"\n=== [{component_id}] Δ1 因果構造抽出中 (Model: {model}) ==="
        )

        # 1. Δ1 抽出 & 正規化
        delta1_data = extract_component_delta1(
            spec_text,
            component_id=component_id,
            ollama_host=ollama_host,
            model=model,
        )

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

    print(
        "\n全 component-001 ～ 013 の Δ1 抽出 & Mermaid 出力が完了しました。"
    )


if __name__ == "__main__":
    main()