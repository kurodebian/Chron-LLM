"""Causal Extract (CAE) モジュール - Ollama 統合"""

import json
import urllib.error
import urllib.request
from builders.mermaid_builder import build_mermaid_from_json


def extract_causal_json(
    text: str,
    ollama_host: str = "http://localhost:11434",
    model: str = "qwen2.5:32b",
    timeout: int = 300,
) -> dict:
    """Ollama API (format='json') を呼び出し、因果グラフの JSON オブジェクトを取得する"""

    prompt = f"""
以下のテキストから因果関係（原因、操作、状態、不変条件とそれらの依存関係）を抽出し、指定のJSONスキーマに従って出力してください。
余計な解説は一切含めず、純粋なJSONオブジェクトのみを返してください。

【JSONスキーマ】
{{
  "nodes": [
    {{"id": "識別子(例: N1)", "label": "ノード名/状態/不変条件"}},
    {{"id": "識別子(例: N2)", "label": "ノード名/操作"}}
  ],
  "edges": [
    {{"from": "N1", "to": "N2", "relation": "因果関係/依存関係の説明"}}
  ]
}}

【対象テキスト】
{text}
"""

    url = f"{ollama_host.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.1},
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            raw_json_str = res_body.get("response", "{}")
            return json.loads(raw_json_str)
    except Exception as e:
        print(f"[Error] 因果グラフJSON抽出に失敗しました: {e}")
        return {"nodes": [], "edges": []}


def generate_causal_mermaid(
    text: str,
    ollama_host: str = "http://localhost:11434",
    model: str = "qwen2.5:32b",
) -> str:
    """テキストから因果関係を抽出して Mermaid 構文文字列を返す高レベル関数"""
    data = extract_causal_json(text, ollama_host=ollama_host, model=model)
    return build_mermaid_from_json(data)