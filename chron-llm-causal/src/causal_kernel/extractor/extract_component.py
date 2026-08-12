"""
src/causal_kernel/extractor/extract_component.py
-------------------------------------------------
component-001〜013 の仕様書から Δ1 因果トポロジー (Node / Edge) を抽出するモジュール
(XML構造分離 + JSON Schema構造強制版)
"""

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List

# ----------------------------------------------------------------------
# Ollama サンプリングエンジンに直接渡す JSON Schema
# これにより nodes と edges 以外の不要なキー (integration_plan 等) の生成を物理的に遮断する
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
    """
    抽象度（粒度）を「ドメイン内部の因果要素」に固定するプロンプト。
    ファイルパスや仕様書メタデータへの脱線を厳格に禁止する。
    """
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


def parse_llm_json_response(raw_response: str) -> Dict[str, Any]:
    """LLMからのレスポンス文字列から安全にJSONをパースする"""
    if not raw_response or not raw_response.strip():
        return {}

    # Markdown の ```json ... ``` ブロックを除去
    cleaned = re.sub(
        r"^```(?:json)?\s*", "", raw_response.strip(), flags=re.MULTILINE
    )
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

    # 最初に出現する '{' から最後に出現する '}' までを抽出
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"\n[Debug JSON Error] パース失敗:\n{cleaned[:400]}\n---")
        return {}


def normalize_component_graph(
    raw_graph: Dict[str, Any], component_id: str
) -> Dict[str, Any]:
    """Δ1 グラフデータの正規化（表記揺れの網羅的吸収と安全なID付与）"""
    if not isinstance(raw_graph, dict):
        return {"component_id": component_id, "nodes": [], "edges": []}

    # 表記揺れの網羅的吸収
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
    ollama_host: str = "http://localhost:11434",
    model: str = "qwen2.5:32b",
    timeout: int = 600,
) -> Dict[str, Any]:
    """Ollama API を呼び出してコンポーネントの Δ1 因果構造を取得"""

    if not spec_text or not spec_text.strip():
        print(f"[Error] {component_id}: 入力仕様書テキスト(spec_text) が空です！")
        return {"component_id": component_id, "nodes": [], "edges": []}

    prompt = build_component_prompt(spec_text, component_id)

    url = f"{ollama_host.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "system": "You are a deterministic structural AST/graph extractor. Parse the input and output valid JSON matching the schema precisely.",
        "prompt": prompt,
        "format": CAUSAL_JSON_SCHEMA,  # JSON Schemaを指定し、Ollama側で構造を強制
        "stream": False,
        "options": {
            "temperature": 0.0,  # 0.0で挙動を完全固定
            "num_ctx": 4096,
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
            raw_response_text = res_body.get("response", "")

            # 生レスポンスのデバッグ表示
            print(f"\n--- [{component_id} LLM 生レスポンス (先頭 300 文字)] ---")
            print(raw_response_text[:300].strip())
            print("--------------------------------------------------")

            extracted_data = parse_llm_json_response(raw_response_text)
            result = normalize_component_graph(extracted_data, component_id)

            print(
                f"[Info] {component_id}: 抽出結果 -> Nodes: {len(result['nodes'])}, Edges: {len(result['edges'])}"
            )
            return result
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