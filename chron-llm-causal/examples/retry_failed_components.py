"""
examples/retry_failed_components.py
----------------------------------
未完了の component-004, component-007 〜 component-013 を一括再抽出するスクリプト
(パス階層の厳密化 & 巨大コンテキスト対応)
"""

import json
import os
from pathlib import Path

from causal_kernel.extractor.extract_component import (
    extract_component_delta1,
    generate_component_mermaid,
)

# 未完了の 004 および 007 〜 013 を指定
TARGET_IDS = [
    "component-004",
    "component-007",
    "component-008",
    "component-009",
    "component-010",
    "component-011",
    "component-012",
    "component-013",
]

# 階層パスの設定
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # ~/Chron-LLM/chron-llm-causal
REPO_ROOT = PROJECT_ROOT.parent                       # ~/Chron-LLM

COMPONENTS_DIR = REPO_ROOT / "component_contexts"
OUTPUT_JSON_DIR = PROJECT_ROOT / "data" / "delta1_normalized"
OUTPUT_MMD_DIR = PROJECT_ROOT / "output_mermaid"


def load_component_context(json_path: Path) -> str:
    """コンテキストJSONからテキストフィールドを柔軟に抽出"""
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
    backend = os.environ.get("LLM_BACKEND", "llamacpp").lower()
    if backend == "ollama":
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        model = os.environ.get("OLLAMA_MODEL", "qwen2.5:32b")
    else:
        host = os.environ.get("LLAMA_HOST", "http://127.0.0.1:8080")
        model = os.environ.get("LLAMA_MODEL", "Qwen3.6-35B-A3B-UD-Q4_K_M.gguf")

    OUTPUT_JSON_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_MMD_DIR.mkdir(parents=True, exist_ok=True)

    print(f"=== 未完了コンポーネントの一括リカバリ抽出 ===")
    print(f"対象件数: {len(TARGET_IDS)} 件")
    print(f"対象ID  : {TARGET_IDS}")
    print(f"設定情報: Backend={backend} | Host={host} | Model={model}\n")

    for comp_id in TARGET_IDS:
        spec_path = COMPONENTS_DIR / f"{comp_id}.json"
        if not spec_path.exists():
            print(f"\n[Skip] {spec_path} が見つかりません。")
            continue

        spec_text = load_component_context(spec_path)
        if not spec_text:
            print(f"\n[{comp_id}] スキップ: テキストが存在しません。")
            continue

        print("\n==================================================")
        print(f"=== リカバリ抽出中: {comp_id} (文字数: {len(spec_text):,} bytes) ===")

        # 巨大ファイル向けに timeout 1800 秒（30分）を確保
        result = extract_component_delta1(
            spec_text=spec_text,
            component_id=comp_id,
            host=host,
            model=model,
            backend=backend,
            timeout=1800,
        )

        # JSON 保存
        json_out = OUTPUT_JSON_DIR / f"causal_extract_{comp_id}_v1.json"
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"  └─ JSON 保存完了: {json_out}")

        # Mermaid 保存
        mmd_text = generate_component_mermaid(result)
        mmd_out = OUTPUT_MMD_DIR / f"{comp_id}.mmd"
        with open(mmd_out, "w", encoding="utf-8") as f:
            f.write(mmd_text)
        print(f"  └─ Mermaid 保存完了: {mmd_out}")

        nodes_cnt = len(result.get("nodes", []))
        edges_cnt = len(result.get("edges", []))
        print(f"[完了] {comp_id} -> Nodes: {nodes_cnt}, Edges: {edges_cnt}")


if __name__ == "__main__":
    main()