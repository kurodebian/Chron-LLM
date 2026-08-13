"""
Causal Extract (CAE) モジュール
(llama.cpp / Ollama 完全対応 & 後方互換維持 & 思考プロセス・途切れ除去堅牢化版)
"""

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, Optional
from builders.mermaid_builder import build_mermaid_from_json

# ----------------------------------------------------------------------
# LLM 指示用システムプロンプト
# ----------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a deterministic structural causal graph extractor. "
    "Output valid JSON matching the schema precisely. "
    "CRITICAL: Do NOT output any preamble, thinking process, introduction, or explanatory text. "
    "Output ONLY the JSON object starting with '{' and ending with '}'."
)


def repair_truncated_json(json_str: str) -> str:
    """
    途中で途切れた JSON を強力に復旧する関数。
    未完成な末尾要素（オブジェクトや文字列）を切り落とし、
    完成済みのデータ構造まで巻き戻して括弧を補完する。
    """
    s = json_str.strip()

    # 1. 開いたまま閉じられていない文字列リテラル（ダブルクォート）の自動クローズ
    quote_count = len(re.findall(r'(?<!\\)"', s))
    if quote_count % 2 != 0:
        s += '"'

    # 2. 途中で切れている最後の完成済みオブジェクト/配列を探して切り詰める
    last_valid_pos = max(s.rfind("}"), s.rfind("]"))
    if last_valid_pos != -1:
        s = s[: last_valid_pos + 1].strip()

    # 末尾に残った余計なカンマを除去
    s = re.sub(r",\s*$", "", s)

    # 3. 不足している閉じ括弧を補完する
    open_curly = s.count("{") - s.count("}")
    open_square = s.count("[") - s.count("]")

    s += "]" * max(0, open_square)
    s += "}" * max(0, open_curly)

    return s


def parse_llm_json_response(raw_response: str) -> Dict[str, Any]:
    """LLMからのレスポンス文字列から安全にJSONをパースする（思考テキスト除去・自動修復機能付き）"""
    if not raw_response or not raw_response.strip():
        return {"nodes": [], "edges": []}

    cleaned = raw_response.strip()

    # <think>...</think> タグ（思考プロセス）の強固な除去
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()

    # Markdown の ```json ... ``` ブロックを除去
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

    # 最初に出現する '{' から最後に出現する '}' までを抽出（前後の思考テキスト・解説を削ぎ落とす）
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    else:
        # 途切れ等の理由で閉じ括弧がない場合は '{' 以降を取得
        match_start = re.search(r"\{.*", cleaned, re.DOTALL)
        if match_start:
            cleaned = match_start.group(0)

    # まずそのままパースを試みる
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # パース失敗時：途切れ復旧を試みる
    repaired = repair_truncated_json(cleaned)
    try:
        parsed = json.loads(repaired)
        print(
            "\n[Warning] JSONが途中で切れていたため、生成済みの要素まで救出してパースしました。"
        )
        return parsed
    except json.JSONDecodeError as e:
        print(f"\n[Debug JSON Error] パース失敗 (修復不可): {e}")
        print(f"修復試行後の文字列:\n{repaired[:400]}\n---")
        return {"nodes": [], "edges": []}


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
            host = os.environ.get("LLAMA_HOST", "[http://127.0.0.1:8080](http://127.0.0.1:8080)")
        if not model:
            model = os.environ.get("LLAMA_MODEL", "qwen2.5-32b")

    prompt = f"""
以下のテキストから因果関係（原因、操作、状態、不変条件とそれらの依存関係）を抽出し、指定のJSONスキーマに従って出力してください。

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

<output_instructions>
CRITICAL OUTPUT RULES:
1. Output STRICTLY a valid raw JSON object starting with '{{' and ending with '}}'.
2. Do NOT output any preamble, thinking process, analysis, explanation, or markdown wrapper.
3. Absolutely NO conversational text before or after the JSON.
</output_instructions>
"""

    if backend == "ollama":
        url = f"{host.rstrip('/')}/api/generate"
        payload = {
            "model": model,
            "system": SYSTEM_PROMPT,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.0},
        }
    else:  # llamacpp (OpenAI Chat Completions 互換)
        url = f"{host.rstrip('/')}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
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

            raw_response_text = ""
            if isinstance(res_body, dict):
                if "response" in res_body and isinstance(res_body["response"], str):
                    raw_response_text = res_body["response"]
                elif "choices" in res_body and len(res_body["choices"]) > 0:
                    choice = res_body["choices"][0]
                    if isinstance(choice, dict):
                        if "message" in choice and isinstance(choice["message"], dict):
                            msg = choice["message"]
                            content = msg.get("content")
                            if content is not None and str(content).strip():
                                raw_response_text = str(content)
                            else:
                                raw_response_text = str(
                                    msg.get("reasoning_content") or content or ""
                                )
                        elif "text" in choice:
                            raw_response_text = choice.get("text", "")
                elif "message" in res_body and isinstance(res_body["message"], dict):
                    raw_response_text = res_body["message"].get("content", "")
                elif "content" in res_body and isinstance(res_body["content"], str):
                    raw_response_text = res_body["content"]

            return parse_llm_json_response(raw_response_text)

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