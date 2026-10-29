"""
src/causal_kernel/extractor/extract_component.py
-------------------------------------------------
component-001〜013 の仕様書から Δ1 因果トポロジー (Node / Edge) を抽出するモジュール
(XML構造分離 + JSON Schema構造強制版 / 途切れデータの強力救出処理付き)
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List

# ----------------------------------------------------------------------
# LLM に渡す JSON Schema
# ----------------------------------------------------------------------
CAUSAL_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "component_id": {"type": "string"},
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["State", "Operation", "Invariant"],
                    },
                },
                "required": ["id", "label", "type"],
                "additionalProperties": False,
            },
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "from": {"type": "string"},
                    "to": {"type": "string"},
                    "relation": {
                        "type": "string",
                        "enum": [
                            "depends_on",
                            "mutates",
                            "enforces",
                            "triggers",
                            "produces",
                        ],
                    },
                },
                "required": ["from", "to", "relation"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["component_id", "nodes", "edges"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "You are a deterministic structural causal graph extractor. "
    "Output valid JSON matching the schema precisely. "
    "CRITICAL: Do NOT output any preamble, thinking process, introduction, or explanatory text. "
    "Output ONLY the JSON object starting with '{' and ending with '}'."
)

# ----------------------------------------------------------------------
# 1. プロンプト構築
# ----------------------------------------------------------------------
def build_component_prompt(spec_text: str, component_id: str) -> str:
    """抽象度（粒度）を「ドメイン内部の因果要素」に固定するプロンプト"""
    template = """
<task_definition>
Extract the internal causal system graph (State, Operation, Invariant) from <spec_content>.
Target Component ID MUST be: "{component_id}"

[Node Types Definition]
- State: Internal data variables, buffer status, cache, flags, entity attributes (e.g., ST_BufferReady, ST_Unauthenticated).
- Operation: Functions, methods, event handlers, execution steps, transitions (e.g., OP_ParseHeader, OP_CommitTransaction).
- Invariant: System rules, validation guards, assertions, preconditions (e.g., INV_NonNegativeBalance, INV_MaxRetryCount).

[Target Output Schema Interface]
interface Node {
  id: string; // Unique ID (e.g., ST_Ready, OP_Validate)
  label: string; // Meaningful short name
  type: "State" | "Operation" | "Invariant";
}

interface Edge {
  from: string; // Source Node ID
  to: string; // Target Node ID
  relation: "depends_on" | "mutates" | "enforces" | "triggers" | "produces";
}

interface CausalGraph {
  component_id: "{component_id}";
  nodes: Node[];
  edges: Edge[];
}
</task_definition>

<strict_negative_constraints>
CRITICAL RULES TO PREVENT META-DATA LEAKAGE:
1. NEVER extract file paths (e.g., "docs/ir/...", "*.spec", "*.md"), directory names, or document titles as Nodes.
2. NEVER extract human team plans, refactoring tasks, or integration steps as Nodes.
3. If <spec_content> references external spec files, IGNORE the file names and extract ONLY the technical logic, variables, and processes described within them.
</strict_negative_constraints>

<spec_content>
{spec_text}
</spec_content>

<output_instructions>
CRITICAL OUTPUT RULES:
1. Output STRICTLY a valid raw JSON object starting with '{' and ending with '}'.
2. Do NOT output any preamble, thinking process, analysis, explanation, or markdown wrapper.
3. Absolutely NO conversational text before or after the JSON.
</output_instructions>
"""
    return (
        template.replace("{component_id}", component_id)
                .replace("{spec_text}", spec_text)
    )

# ----------------------------------------------------------------------
# 2. JSON パース & 途切れ修復
# ----------------------------------------------------------------------
def repair_truncated_json(json_str: str) -> str:
    """途中で途切れた JSON の未完成な末尾を削除し、スタック構造で安全に括弧を補完"""
    s = json_str.strip()

    s = re.sub(r"<think>.*?</think>", "", s, flags=re.DOTALL)
    s = re.sub(r"```(?:json)?", "", s)
    s = s.strip()

    s = re.sub(r',?\s*"[^"]*$', '', s)
    s = re.sub(r',?\s*"[^"]*"\s*:\s*$', '', s)
    s = re.sub(r',?\s*"[^"]*"\s*:\s*"[^"]*$', '', s)
    s = re.sub(r',?\s*"[^"]*"\s*:\s*(?:true|false|null|[0-9.eE+-]+)?$', '', s)
    s = re.sub(r',?\s*[\{\[]\s*$', '', s)

    last_valid_pos = max(s.rfind("}"), s.rfind("]"))
    if last_valid_pos != -1:
        after_last = s[last_valid_pos + 1:].strip()
        if not (after_last.startswith("}") or after_last.startswith("]")):
            s = s[: last_valid_pos + 1].strip()

    s = re.sub(r"[:,]\s*$", "", s)

    stack = []
    in_string = False
    escape = False

    for char in s:
        if escape:
            escape = False
            continue
        if char == '\\':
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string:
            if char in ('{', '['):
                stack.append(char)
            elif char == '}':
                if stack and stack[-1] == '{':
                    stack.pop()
            elif char == ']':
                if stack and stack[-1] == '[':
                    stack.pop()

    closing_map = {'{': '}', '[': ']'}
    while stack:
        s += closing_map[stack.pop()]

    return s

def parse_llm_json_response(raw_response: str) -> Dict[str, Any]:
    """LLMからのレスポンス文字列から安全にJSONをパースする"""
    if not raw_response or not raw_response.strip():
        return {}

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
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    repaired = repair_truncated_json(cleaned)
    try:
        parsed = json.loads(repaired)
        print(
            "\n[Warning] JSONが途中で切れていたため、生成済みの要素（Node/Edge）まで救出してパースしました。"
        )
        return parsed
    except json.JSONDecodeError as e:
        print(f"\n[Debug JSON Error] パース失敗 (修復不可): {e}")
        print(f"修復試行後の文字列:\n{repaired[:400]}\n---")
        return {}

# ----------------------------------------------------------------------
# 3. ID サニタイズ & グラフ正規化
# ----------------------------------------------------------------------
def sanitize_id(raw_id: str) -> str:
    """Mermaid で構文エラーを起こさない安全な ID に変換"""
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', str(raw_id))
    return clean if clean else "NODE_UNKNOWN"

def normalize_component_graph(raw_graph: dict, component_id: str) -> dict:
    """IDの統一・サニタイズと、Dangling Node の自動補完"""
    normalized_nodes = []
    normalized_edges = []
    id_mapping = {}

    for node in raw_graph.get("nodes", []):
        raw_id = str(node.get("id", ""))
        clean_id = sanitize_id(raw_id)
        id_mapping[raw_id] = clean_id

        normalized_nodes.append({
            "id": clean_id,
            "label": node.get("label", clean_id),
            "raw_label": node.get("label", clean_id),
            "type": node.get("type", "State"),
            "component_id": component_id,
        })

    for edge in raw_graph.get("edges", []):
        from_id = id_mapping.get(edge.get("from"), sanitize_id(edge.get("from", "")))
        to_id = id_mapping.get(edge.get("to"), sanitize_id(edge.get("to", "")))

        normalized_edges.append({
            "from": from_id,
            "to": to_id,
            # A3: NO_IMPLICIT_DEFAULT — missing relation => UNCLASSIFIED sentinel.
            "relation": edge.get("relation", "UNCLASSIFIED"),
        })

    existing_node_ids = {n["id"] for n in normalized_nodes}

    for edge in normalized_edges:
        for ref_id in (edge["from"], edge["to"]):
            if ref_id and ref_id not in existing_node_ids:
                node_type = "State"
                if ref_id.startswith("OP_"):
                    node_type = "Operation"
                elif ref_id.startswith("INV_"):
                    node_type = "Invariant"

                normalized_nodes.append({
                    "id": ref_id,
                    "label": f"{ref_id}",
                    "raw_label": ref_id,
                    "type": node_type,
                    "component_id": component_id,
                })
                existing_node_ids.add(ref_id)

    return {
        "component_id": component_id,
        "nodes": normalized_nodes,
        "edges": normalized_edges,
    }

# ----------------------------------------------------------------------
# 4. Mermaid 生成 & 特殊文字エスケープ処理
# ----------------------------------------------------------------------
def clean_mermaid_label(label: str) -> str:
    """Mermaid の構文と衝突する文字を HTML エンティティに置換"""
    if not isinstance(label, str):
        label = str(label)
    return (
        label.replace('"', "#quot;")
        .replace("[", "&#91;")
        .replace("]", "&#93;")
        .replace("(", "&#40;")
        .replace(")", "&#41;")
        .replace("{", "&#123;")
        .replace("}", "&#125;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", " ")
    )

def generate_mermaid(graph: dict) -> str:
    """正規化済みグラフ辞書から Mermaid ダイアグラム文字列表現を出力"""
    lines = ["flowchart TD"]
    
    for node in graph.get("nodes", []):
        node_id = node["id"]
        safe_label = clean_mermaid_label(node.get("label", node_id))
        node_type = node.get("type", "State")

        if node_type == "Operation":
            lines.append(f'    {node_id}(["{safe_label}"])')
        elif node_type == "Invariant":
            lines.append(f'    {node_id}{{"{safe_label}"}}')
        else:
            lines.append(f'    {node_id}["{safe_label}"]')

    relation_style = {
        "depends_on": "-->|depends_on|",
        "mutates": "==>|mutates|",
        "enforces": "-.->|enforces|",
        "triggers": "-->|triggers|",
        "produces": "-->|produces|",
    }

    for edge in graph.get("edges", []):
        f = edge["from"]
        t = edge["to"]
        rel = edge.get("relation", "UNCLASSIFIED")
        arrow = relation_style.get(rel, "-->")
        lines.append(f"    {f} {arrow} {t}")

    lines.append("")
    lines.append("    classDef stateStyle fill:#e1f5fe,stroke:#0288d1,stroke-width:1px;")
    lines.append("    classDef opStyle fill:#e8f5e9,stroke:#388e3c,stroke-width:1px;")
    lines.append("    classDef invStyle fill:#fff3e0,stroke:#f57c00,stroke-width:1px;")

    state_ids = [n["id"] for n in graph.get("nodes", []) if n.get("type") == "State"]
    op_ids = [n["id"] for n in graph.get("nodes", []) if n.get("type") == "Operation"]
    inv_ids = [n["id"] for n in graph.get("nodes", []) if n.get("type") == "Invariant"]

    if state_ids:
        lines.append(f"    class {','.join(state_ids)} stateStyle;")
    if op_ids:
        lines.append(f"    class {','.join(op_ids)} opStyle;")
    if inv_ids:
        lines.append(f"    class {','.join(inv_ids)} invStyle;")

    return "\n".join(lines)

# 互換性維持のためのエイリアス
generate_component_mermaid = generate_mermaid

# ----------------------------------------------------------------------
# 5. LLM API 呼び出しメイン関数
# ----------------------------------------------------------------------
def extract_component_delta1(
    spec_text: str,
    component_id: str,
    host: str = "[http://127.0.0.1:8080](http://127.0.0.1:8080)",
    model: str = "Qwen3.6-35B-A3B-UD-Q4_K_M.gguf",
    backend: str = "llamacpp",
    timeout: int = 1200,
    max_tokens: int = 8192,
    **kwargs,
) -> Dict[str, Any]:
    """llama.cpp または Ollama API を呼び出してコンポーネントの Δ1 因果構造を取得"""

    if not spec_text or not spec_text.strip():
        print(f"[Error] {component_id}: 入力仕様書テキスト(spec_text) が空です！")
        return {"component_id": component_id, "nodes": [], "edges": []}

    prompt = build_component_prompt(spec_text, component_id)
    backend_type = backend.lower()

    if backend_type == "ollama":
        url = f"{host.rstrip('/')}/api/generate"
        payload = {
            "model": model,
            "system": SYSTEM_PROMPT,
            "prompt": prompt,
            "format": CAUSAL_JSON_SCHEMA,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_ctx": 32768,
                "num_predict": max_tokens,
            },
        }
    else:  # default: llamacpp
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
            "max_tokens": max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "causal_graph",
                    "schema": CAUSAL_JSON_SCHEMA,
                },
            },
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
                            # content を第一優先で取得 (思考ログ reasoning_content は除外)
                            content = msg.get("content")
                            if content is not None and str(content).strip():
                                raw_response_text = str(content)
                            else:
                                raw_response_text = str(msg.get("reasoning_content") or "")
                        elif "text" in choice:
                            raw_response_text = choice.get("text", "")
                elif "message" in res_body and isinstance(res_body["message"], dict):
                    raw_response_text = res_body["message"].get("content", "")
                elif "content" in res_body and isinstance(res_body["content"], str):
                    raw_response_text = res_body["content"]

            print(f"\n--- [{component_id} LLM 生レスポンス (先頭 300 文字)] ---")
            print(raw_response_text[:300].strip())
            print("--------------------------------------------------")

            if not raw_response_text.strip():
                print(f"[Warning] {component_id}: レスポンスコンテンツが空です。")

            extracted_data = parse_llm_json_response(raw_response_text)
            result = normalize_component_graph(extracted_data, component_id)

            print(
                f"[Info] {component_id}: 抽出結果 -> Nodes: {len(result['nodes'])}, Edges: {len(result['edges'])}"
            )
            return result

    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        print(f"[Error] Component {component_id} HTTP Error {e.code}: {e.reason}")
        print(f"  └─ 詳細: {err_body}")
        return {
            "component_id": component_id,
            "nodes": [],
            "edges": [],
            "error": f"HTTP {e.code}: {err_body}",
        }
    except Exception as e:
        print(f"[Error] Component {component_id} の抽出失敗: {e}")
        return {
            "component_id": component_id,
            "nodes": [],
            "edges": [],
            "error": str(e),
        }

# ----------------------------------------------------------------------
# CLI エントリポイント
# ----------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract Causal Component Graph from Spec Text")
    parser.add_argument("--spec", required=True, help="Path to spec file (.md / .txt)")
    parser.add_argument("--id", required=True, help="Component ID (e.g., component-001)")
    parser.add_argument("--host", default="[http://127.0.0.1:8080](http://127.0.0.1:8080)", help="LLM Host URL")
    parser.add_argument("--model", default="Qwen3.6-35B-A3B-UD-Q4_K_M.gguf", help="LLM Model Name")
    parser.add_argument("--backend", default="llamacpp", choices=["llamacpp", "ollama"], help="Backend type")
    parser.add_argument("--out", default=None, help="Output JSON path")

    args = parser.parse_args()

    if not os.path.exists(args.spec):
        print(f"[Error] Spec file not found: {args.spec}")
        sys.exit(1)

    with open(args.spec, "r", encoding="utf-8") as f:
        spec_content = f.read()

    res = extract_component_delta1(
        spec_text=spec_content,
        component_id=args.id,
        host=args.host,
        model=args.model,
        backend=args.backend,
    )

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print(f"[Success] Saved result to {args.out}")
    else:
        print(json.dumps(res, ensure_ascii=False, indent=2))