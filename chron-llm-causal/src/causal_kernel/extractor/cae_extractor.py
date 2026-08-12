"""
Causal Extract (CAE) モジュール
(llama.cpp / Ollama 完全対応 & 後方互換維持版)
"""

import json
import os
import urllib.error
import urllib.request
from typing import Optional
from builders.mermaid_builder import build_mermaid_from_json


def extract_causal_json(
    text: str,
    host: Optional[str] = None,
    model: Optional[str] = None,
    backend: Optional[str] = None,
    ollama_host: Optional[str] = None,  # 旧コードとの互換用
    timeout: int = 300,
) -> dict:
    """LLM (llama.cpp / Ollama) API を呼び出し、因果グラフの JSON オブジェクトを取得する"""

    # 1. バックエンドの自動判定 (指定なしなら環境変数、それもなければ llamacpp)
    if backend is None:
        backend = os.environ.get("LLM_BACKEND", "llamacpp").lower()
    else:
        backend = backend.lower()

    # 2. 旧引数 ollama_host が渡された場合の互換吸収
    if ollama_host and not host:
        host = ollama_host
        backend = "ollama"

    # 3. バックエンドに応じたデフォルト Host / Model の自動補完
    if backend == "ollama":
        if not host:
            host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        if not model:
            model = os.environ.get("OLLAMA_MODEL", "qwen2.5:32b")
    else:  # llamacpp
        if not host:
            host = os.environ.get("LLAMA_HOST", "http://127.0.0.1:8080")
        if not model:
            model = os.environ.get("LLAMA_MODEL", "qwen2.5-32b")

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

    if backend == "ollama":
        url = f"{host.rstrip('/')}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.1},
        }
    else:  # llamacpp (OpenAI Chat Completions 互換)
        url = f"{host.rstrip('/')}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a deterministic structural causal graph extractor. Output valid JSON matching the schema precisely.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_body = json.loads(response.read().decode("utf-8"))

            if backend == "ollama":
                raw_json_str = res_body.get("response", "{}")
            else:  # llamacpp
                choices = res_body.get("choices", [])
                if choices:
                    raw_json_str = (
                        choices[0].get("message", {}).get("content", "{}")
                    )
                else:
                    raw_json_str = res_body.get("content", "{}")

            return json.loads(raw_json_str)
    except Exception as e:
        print(f"[Error] 因果グラフJSON抽出に失敗しました ({backend} / {host}): {e}")
        return {"nodes": [], "edges": []}


def generate_causal_mermaid(
    text: str,
    host: Optional[str] = None,
    model: Optional[str] = None,
    backend: Optional[str] = None,
    ollama_host: Optional[str] = None,
) -> str:
    """テキストから因果関係を抽出して Mermaid 構文文字列を返す高レベル関数"""
    data = extract_causal_json(
        text,
        host=host,
        model=model,
        backend=backend,
        ollama_host=ollama_host,
    )
    return build_mermaid_from_json(data)