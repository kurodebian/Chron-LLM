"""
Causal Extract (CAE) モジュール
(MasterGraph v2.0 / C6 Canonical スキーマ完全準拠版)
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
    "Output valid JSON matching the MasterGraph v2.0 Causal Core schema precisely. "
    "CRITICAL: Do NOT output any preamble, thinking process, introduction, or explanatory text. "
    "Output ONLY the JSON object starting with '{' and ending with '}'."
)


def repair_truncated_json(json_str: str) -> str:
    """途中で途切れた JSON を復旧する関数"""
    s = json_str.strip()

    quote_count = len(re.findall(r'(?<!\\)"', s))
    if quote_count % 2 != 0:
        s += '"'

    last_valid_pos = max(s.rfind("}"), s.rfind("]"))
    if last_valid_pos != -1:
        s = s[: last_valid_pos + 1].strip()

    s = re.sub(r",\s*$", "", s)

    open_curly = s.count("{") - s.count("}")
    open_square = s.count("[") - s.count("]")

    s += "]" * max(0, open_square)
    s += "}" * max(0, open_curly)

    return s


def normalize_canonical_graph(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    LLMから抽出したデータ、または旧形式データを
    MasterGraph v2.0 / C6 Canonical 検証仕様に適合する形へ正規化・補完する。
    """
    normalized_nodes = []
    normalized_edges = []

    # 1. ノードの正規化
    raw_nodes = raw_data.get("nodes", [])
    if isinstance(raw_nodes, dict):
        # 辞書形式 {"P001": {...}} の吸収
        node_items = list(raw_nodes.values())
    elif isinstance(raw_nodes, list):
        node_items = raw_nodes
    else:
        node_items = []

    for idx, n in enumerate(node_items):
        if not isinstance(n, dict):
            continue

        node_id = n.get("id") or f"N{idx+1:03d}"
        node_type = n.get("type", "component")
        name = n.get("name") or n.get("label") or node_id
        properties = n.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}

        # 権限インバリアント・境界ノードに対する guard_token の自動定義
        if ("AUTH" in node_id.upper() or "AUTHORITY" in name.upper() or node_type == "authority_boundary") and "guard_token" not in properties:
            properties["guard_token"] = f"AUTH-{idx+1:03d}"

        normalized_nodes.append({
            "id": node_id,
            "global_id": n.get("global_id", node_id),
            "local_id": n.get("local_id", node_id),
            "type": node_type,
            "name": name,
            "description": n.get("description") or n.get("notes") or "",
            "properties": properties
        })

    # 2. エッジの正規化
    raw_edges = raw_data.get("edges", [])
    if not isinstance(raw_edges, list):
        raw_edges = []

    for idx, e in enumerate(raw_edges):
        if not isinstance(e, dict):
            continue

        edge_id = e.get("id") or f"E{idx+1:03d}"
        from_node = e.get("from") or e.get("source") or ""
        to_node = e.get("to") or e.get("target") or ""
        morphism_type = e.get("morphism_type") or e.get("relation") or "invariant"

        # C6 Morphism Type の推論・変換
        if morphism_type not in ["authority_boundary", "invariant", "dependency", "constraint", "defines"]:
            if "AUTH" in from_node.upper() or "AUTH" in to_node.upper():
                morphism_type = "authority_boundary"
            elif "FUNC" in from_node.upper() or "depends" in str(e.get("relation", "")).lower():
                morphism_type = "dependency"
            elif "TYPE" in from_node.upper():
                morphism_type = "defines"
            else:
                morphism_type = "invariant"

        # guard_invariant 配列の調整
        guard_inv = e.get("guard_invariant", [])
        if not guard_inv and morphism_type == "authority_boundary":
            # from_node がインバリアント指定であれば自動バインド
            guard_inv = [from_node] if from_node else []

        normalized_edges.append({
            "id": edge_id,
            "from": from_node,
            "to": to_node,
            "pipeline": e.get("pipeline", "CommitPipeline"),
            "morphism_type": morphism_type,
            "guard_invariant": guard_inv,
            "delta_level": e.get("delta_level", "DELTA_1")
        })

    return {
        "nodes": normalized_nodes,
        "edges": normalized_edges
    }


def parse_llm_json_response(raw_response: str) -> Dict[str, Any]:
    """LLMからのレスポンス文字列から安全にJSONをパースし正規化する"""
    if not raw_response or not raw_response.strip():
        return {"nodes": [], "edges": []}

    cleaned = raw_response.strip()

    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    else:
        match_start = re.search(r"\{.*", cleaned, re.DOTALL)
        if match_start:
            cleaned = match_start.group(0)

    try:
        parsed = json.loads(cleaned)
        return normalize_canonical_graph(parsed)
    except json.JSONDecodeError:
        pass

    repaired = repair_truncated_json(cleaned)
    try:
        parsed = json.loads(repaired)
        print("\n[Warning] JSONが途中で切れていたため、生成済みの要素まで救出してパースしました。")
        return normalize_canonical_graph(parsed)
    except json.JSONDecodeError as e:
        print(f"\n[Debug JSON Error] パース失敗 (修復不可): {e}")
        return {"nodes": [], "edges": []}


def extract_causal_json(
    text: str,
    host: Optional[str] = None,
    model: Optional[str] = None,
    backend: Optional[str] = None,
    ollama_host: Optional[str] = None,
    timeout: int = 300,
) -> dict:
    """LLM API を呼び出し、MasterGraph v2.0 スキーマに準拠した JSON を取得する"""

    if backend is None:
        backend = os.environ.get("LLM_BACKEND", "llamacpp").lower()
    else:
        backend = backend.lower()

    if ollama_host and not host:
        host = ollama_host
        backend = "ollama"

    if backend == "ollama":
        if not host:
            host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        if not model:
            model = os.environ.get("OLLAMA_MODEL", "qwen2.5:32b")
    else:
        if not host:
            host = os.environ.get("LLAMA_HOST", "http://127.0.0.1:8080")
        if not model:
            model = os.environ.get("LLAMA_MODEL", "qwen2.5-32b")

    prompt = f"""
以下のテキストから因果関係（原因、操作、状態、不変条件とそれらの依存関係）を抽出し、MasterGraph v2.0 スキーマに従って出力してください。

【MasterGraph v2.0 JSONスキーマ】
{{
  "nodes": [
    {{
      "id": "INV_AUTH_001",
      "type": "invariant",
      "name": "権限チェックインバリアント",
      "description": "説明",
      "properties": {{ "guard_token": "AUTH-001" }}
    }},
    {{
      "id": "OP_COMMIT",
      "type": "operation",
      "name": "コミット操作",
      "description": "説明",
      "properties": {{}}
    }}
  ],
  "edges": [
    {{
      "id": "E001",
      "from": "INV_AUTH_001",
      "to": "OP_COMMIT",
      "pipeline": "CommitPipeline",
      "morphism_type": "authority_boundary",
      "guard_invariant": ["INV_AUTH_001"],
      "delta_level": "DELTA_0"
    }}
  ]
}}

【対象テキスト】
{text}

<output_instructions>
CRITICAL OUTPUT RULES:
1. Output STRICTLY a valid raw JSON object starting with '{{' and ending with '}}'.
2. Do NOT output any preamble, thinking process, analysis, explanation, or markdown wrapper.
3. 'morphism_type' must be one of: ['authority_boundary', 'invariant', 'dependency', 'constraint', 'defines'].
4. Authority nodes/invariants MUST have a 'guard_token' property starting with 'AUTH-'.
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
    else:
        url = f"{host.rstrip('/')}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
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
                            raw_response_text = str(content) if content else str(msg.get("reasoning_content") or "")
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
    """テキストから因果関係を抽出して Mermaid 構文文字列を返す"""
    data = extract_causal_json(
        text,
        host=host,
        model=model,
        backend=backend,
        ollama_host=ollama_host,
    )
    return build_mermaid_from_json(data)