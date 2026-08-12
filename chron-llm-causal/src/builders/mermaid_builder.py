"""JSON 構造から Mermaid 構文を生成するビルダー"""


def build_mermaid_from_json(data: dict) -> str:
    """JSON データ構造から Mermaid (flowchart TD) 構文テキストを生成する"""
    lines = ["flowchart TD"]

    # ノード定義 (ID と表示ラベル)
    nodes = data.get("nodes", [])
    for node in nodes:
        node_id = node.get("id", "").strip()
        label = str(node.get("label", "")).replace('"', "'")
        if node_id:
            lines.append(f'    {node_id}["{label}"]')

    # エッジ定義 (依存・因果関係)
    edges = data.get("edges", [])
    for edge in edges:
        source = edge.get("from", "").strip()
        target = edge.get("to", "").strip()
        relation = edge.get("relation", "").strip()

        if source and target:
            if relation:
                rel_label = relation.replace('"', "'")
                lines.append(f'    {source} -- "{rel_label}" --> {target}')
            else:
                lines.append(f'    {source} --> {target}')

    return "\n".join(lines)