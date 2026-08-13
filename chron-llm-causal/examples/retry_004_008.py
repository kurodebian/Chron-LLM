"""
examples/retry_004_008.py
-------------------------
思考テキスト混入対策 & 生成トークン上限拡張 & JSON強固パース処理を施した
component-004 / component-008 専用リカバリ実行スクリプト
"""

import json
import os
import re
from pathlib import Path

from causal_kernel.extractor.extract_component import (
    extract_component_delta1,
    generate_component_mermaid,
)

TARGET_IDS = ["component-004", "component-008"]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent

COMPONENTS_DIR = REPO_ROOT / "component_contexts"
OUTPUT_JSON_DIR = PROJECT_ROOT / "data" / "delta1_normalized"
OUTPUT_MMD_DIR = PROJECT_ROOT / "output_mermaid"


def sanitize_and_parse_json(raw_input) -> dict:
    """思考テキストや説明文が混入したレスポンスから純粋なJSONオブジェクトのみを強力に抽出・パースする"""
    if isinstance(raw_input, dict):
        # 既に辞書でノードかエッジが存在すればそのまま返す
        if raw_input.get("nodes") or raw_input.get("edges"):
            return raw_input
        # 内包された生レスポンス文字列があるか確認
        raw_text = raw_input.get("raw_response") or raw_input.get("text") or str(raw_input)
    else:
        raw_text = str(raw_input)

    # 1. ```json ... ``` コードブロックの優先抽出
    json_block = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw_text)
    if json_block:
        try:
            return json.loads(json_block.group(1))
        except json.JSONDecodeError:
            pass

    # 2. 思考テキスト等を切り捨て、最初に出現する '{' から 最後に出現する '}' までを切り出す
    start_idx = raw_text.find("{")
    end_idx = raw_text.rfind("}")

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        candidate = raw_text[start_idx : end_idx + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # 末尾のカンマ（, } や , ]）の修復試行
            fixed_candidate = re.sub(r",\s*([\}\]])", r"\1", candidate)
            try:
                return json.loads(fixed_candidate)
            except json.JSONDecodeError:
                pass

    return {}


def load_component_context(json_path: Path) -> str:
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for key in ["context", "text", "content"]:
                if key in data:
                    return str(data[key])
            return json.dumps(data, ensure_ascii=False, indent=2)
        return str(data)
    except Exception as e:
        print(f"[Warning] {json_path} 読み込み失敗: {e}")
        return ""


def main():
    backend = os.environ.get("LLM_BACKEND", "llamacpp").lower()
    
    # URL 取得とサニタイズ（Markdownリンク記法や角括弧を自動除去）
    raw_host = os.environ.get("LLAMA_HOST", "http://127.0.0.1:8080")
    host = re.sub(r"\[.*?\]\((.*?)\)", r"\1", raw_host).replace("[", "").replace("]", "").strip()

    model = os.environ.get("LLAMA_MODEL", "Qwen3.6-35B-A3B-UD-Q4_K_M.gguf")

    # 出力先ディレクトリの自動作成
    OUTPUT_JSON_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_MMD_DIR.mkdir(parents=True, exist_ok=True)

    print(f"=== ピンポイント・リカバリ抽出 (004 / 008) ===")
    print(f"接続先 Host: {host} (Backend: {backend})")

    for comp_id in TARGET_IDS:
        spec_path = COMPONENTS_DIR / f"{comp_id}.json"
        if not spec_path.exists():
            print(f"[Skip] {spec_path} が存在しません。")
            continue

        spec_text = load_component_context(spec_path)
        print(f"\n==================================================")
        print(f"=== リカバリ抽出中: {comp_id} (文字数: {len(spec_text):,} bytes) ===")

        # max_tokens 拡張 & 長時間タイムアウト確保
        raw_result = extract_component_delta1(
            spec_text=spec_text,
            component_id=comp_id,
            host=host,
            model=model,
            backend=backend,
            timeout=1800,
            max_tokens=8192,  # 生成上限を拡大
        )

        # レスポンスサニタイズ（思考テキストの分離・JSON抽出）
        result = sanitize_and_parse_json(raw_result)

        # component_id の補正
        if isinstance(result, dict):
            result["component_id"] = comp_id

        # JSON 保存
        json_out = OUTPUT_JSON_DIR / f"causal_extract_{comp_id}_v1.json"
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # Mermaid 保存
        mmd_text = generate_component_mermaid(result)
        mmd_out = OUTPUT_MMD_DIR / f"{comp_id}.mmd"
        with open(mmd_out, "w", encoding="utf-8") as f:
            f.write(mmd_text)

        nodes_cnt = len(result.get("nodes", [])) if isinstance(result, dict) else 0
        edges_cnt = len(result.get("edges", [])) if isinstance(result, dict) else 0
        print(f"[完了] {comp_id} -> Nodes: {nodes_cnt}, Edges: {edges_cnt}")


if __name__ == "__main__":
    main()