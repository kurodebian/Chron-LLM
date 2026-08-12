"""
src/causal_kernel/extractor/extract_component.py
-------------------------------------------------
component-001〜013 の仕様書から Δ1 因果トポロジー (Node / Edge) を抽出するモジュール
(XML構造分離 + JSON Schema構造強制版 / 途切れデータの強力救出処理付き)
"""

import json
import os
import re
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


def build_component_prompt(spec_text: str, component_id: str) -> str:
    """抽象度（粒度）を「ドメイン内部の因果要素」に固定するプロンプト"""
    return f"""
<task_definition>
Extract the internal causal system graph (State, Operation, Invariant) from <spec_content>.
Target Component ID MUST be: "{component_id}"

[Node Types Definition]
- State: Internal data variables, buffer status, cache, flags, entity attributes (e.g., ST_BufferReady, ST_Unauthenticated).
- Operation: Functions, methods, event handlers, execution steps, transitions (e.g., OP_ParseHeader, OP_CommitTransaction).
- Invariant: System rules, validation guards, assertions, preconditions (e.g., INV_NonNegativeBalance, INV_MaxRetryCount).

[Target Output Schema Interface]
interface Node {{
  id: string; // Unique ID (e.g., ST_Ready, OP_Validate)
  label: string; // Meaningful short name
  type: "State" | "Operation" | "Invariant";
}}

interface Edge {{
  from: string; // Source Node ID
  to: string; // Target Node ID
  relation: "depends_on" | "mutates" | "enforces" | "triggers" | "produces";
}}

interface CausalGraph {{
  component_id: "{component_id}";
  nodes: Node[];
  edges: Edge[];
}}
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
"""


def repair_truncated_json(json_str: str) -> str:
    """
    途中で途切れた JSON を強力に復旧する関数。
    未完成な末尾要素（オブジェクトや文字列）をバッサリ切り落とし、
    完成済みのデータ構造まで巻き戻して括弧を補完する。
    """
    s = json_str.strip()

    # 1. 途中で切れている最後の不完全な要素を探して削る
    # 最後の完全な要素の区切り（カンマ ',' や 配列の開き '[' など）を探す
    last_valid_pos = max(s.rfind("}"), s.rfind("]"))

    if last_valid_pos != -1:
        # 完成している最後の要素以降のゴミ（ちぎれた要素）をバッサリ削除
        s = s[: last_valid_pos + 1].strip()

    # 末尾に残った余計なカンマを除去
    s = re.sub(r",\s*$", "", s)

    # 2. 不足している閉じ括弧を補完する
    open_curly = s.count("{") - s.count("}")
    open_square = s.count("[") - s.count("]")

    s += "]" * max(0, open_square)
    s += "}" * max(0, open_curly)

    return s


def parse_llm_json_response(raw_response: str) -> Dict[str, Any]:
    """LLMからのレスポンス文字列から安全にJSONをパースする（強力な自動修復機能付き）"""
    if not raw_response or not raw_response.strip():
        return {}

    # Markdown の ```json ... ``` ブロックを除去
    cleaned = re.sub(
        r"^```(?:json)?\s*", "", raw_response.strip(), flags=re.MULTILINE
    )
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

    # 最初に出現する '{' 以降を抽出
    match = re.search(r"\{.*", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    # まずそのままパースを試みる
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # パース失敗時：途切れ復旧を試みる
    repaired = repair_truncated_json(cleaned)
    try:
        parsed = json.loads(repaired)
        print("\n[Warning] JSONが途中で切れていたため、生成済みの要素（Node/Edge）まで救出してパースしました。")
        return parsed
    except json.JSONDecodeError as e:
        print(f"\n[Debug JSON Error] パース失敗 (修復不可): {e}")
        print(f"修復試行後の文字列:\n{repaired[:400]}\n---")
        return {}


def normalize_component_graph(
    raw_graph: Dict[str, Any], component_id: str
) -> Dict[str, Any]:
    """Δ1 グラフデータの正規化（表記揺れの網羅的吸収と安全なID付与）"""
    if not isinstance(raw_graph, dict):
        return {"component_id": component_id, "nodes": [], "edges": []}

    raw_nodes = (
        raw_graph.get("nodes")
        or raw_graph.get("Nodes")
        or raw_graph.get("node_list")
        or raw_graph.get("components")
        or []
    )
    raw_edges = (
        raw_graph.get("edges")
        or raw_graph.get("Edges")
        or raw_graph.get("edge_list")
        or raw_graph.get("relationships")
        or []
    )

    normalized_nodes = []
    seen_node_ids = set()

    for idx, node in enumerate(raw_nodes):
        if not isinstance(node, dict):
            continue

        raw_id = str(
            node.get("id") or node.get("node_id") or f"N_{idx}"
        ).strip()
        label = str(
            node.get("label") or node.get("name") or raw_id
        ).strip()
        node_type = str(
            node.get("type") or node.get("category") or "State"
        ).capitalize()

        safe_id = re.sub(r"[^a-zA-Z0-9_]", "_", raw_id)
        if safe_id in seen_node_ids:
            safe_id = f"{safe_id}_{idx}"
        seen_node_ids.add(safe_id)

        display_label = f"{label} [{node_type}]"

        normalized_nodes.append(
            {
                "id": safe_id,
                "label": display_label,
                "raw_label": label,
                "type": node_type,
                "component_id": component_id,
            }
        )

    normalized_edges = []
    for edge in raw_edges:
        if not isinstance(edge, dict):
            continue

        src = str(
            edge.get("from")
            or edge.get("source")
            or edge.get("src")
            or ""
        ).strip()
        dst = str(
            edge.get("to")
            or edge.get("target")
            or edge.get("dst")
            or ""
        ).strip()
        relation = str(
            edge.get("relation") or edge.get("type") or "depends_on"
        ).strip()

        safe_src = re.sub(r"[^a-zA-Z0-9_]", "_", src)
        safe_dst = re.sub(r"[^a-zA-Z0-9_]", "_", dst)

        if safe_src and safe_dst:
            normalized_edges.append(
                {
                    "from": safe_src,
                    "to": safe_dst,
                    "relation": relation,
                    "component_id": component_id,
                }
            )

    return {
        "component_id": component_id,
        "nodes": normalized_nodes,
        "edges": normalized_edges,
    }


def extract_component_delta1(
    spec_text: str,
    component_id: str,
    host: str = "http://127.0.0.1:8080",
    model: str = "Qwen3.6-35B-A3B-UD-Q4_K_M.gguf",
    backend: str = "llamacpp",
    timeout: int = 1200,
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
            "system": "You are a deterministic structural AST/graph extractor. Parse the input and output valid JSON matching the schema precisely.",
            "prompt": prompt,
            "format": CAUSAL_JSON_SCHEMA,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_ctx": 16384,
                "num_predict": 8192,
            },
        }
    else:  # default: llamacpp
        url = f"{host.rstrip('/')}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a deterministic structural AST/graph extractor. Parse the input and output valid JSON matching the schema precisely.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 8192,
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
                            raw_response_text = choice["message"].get("content", "")
                        elif "text" in choice:
                            raw_response_text = choice.get("text", "")
                elif "message" in res_body and isinstance(res_body["message"], dict):
                    raw_response_text = res_body["message"].get("content", "")
                elif "content" in res_body and isinstance(res_body["content"], str):
                    raw_response_text = res_body["content"]

            print(
                f"\n--- [{component_id} LLM 生レスポンス (先頭 300 文字)] ---"
            )
            print(raw_response_text[:300].strip())
            print("--------------------------------------------------")

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


def generate_component_mermaid(delta1_graph: Dict[str, Any]) -> str:
    """正規化された Δ1 グラフから Mermaid ダイアグラムコードを生成"""
    lines = ["graph TD"]

    lines.append("    classDef state fill:#f9f,stroke:#333,stroke-width:1px;")
    lines.append("    classDef op fill:#bbf,stroke:#333,stroke-width:1px;")
    lines.append("    classDef inv fill:#ff9,stroke:#333,stroke-width:1px;")

    nodes = delta1_graph.get("nodes", [])
    edges = delta1_graph.get("edges", [])

    for node in nodes:
        nid = node["id"]
        label = str(node.get("label", nid)).replace('"', '\\"')
        ntype = node.get("type", "State")

        lines.append(f'    {nid}["{label}"]')

        if ntype == "State":
            lines.append(f"    class {nid} state;")
        elif ntype == "Operation":
            lines.append(f"    class {nid} op;")
        elif ntype == "Invariant":
            lines.append(f"    class {nid} inv;")

    for edge in edges:
        src = edge.get("from", "")
        dst = edge.get("to", "")
        relation = str(edge.get("relation", "")).replace('"', '\\"')

        if src and dst:
            if relation:
                lines.append(f'    {src} -- "{relation}" --> {dst}')
            else:
                lines.append(f"    {src} --> {dst}")

    return "\n".join(lines)