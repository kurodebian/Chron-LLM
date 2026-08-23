# test_quick.py として実行
from causal_kernel.extractor.extract_component import (
    parse_llm_json_response,
    normalize_component_graph,
    generate_mermaid,
)

# 1. 途切れJSONの修復パーステスト
dummy_raw_llm_output = """
```json
{
  "component_id": "component-001",
  "nodes": [
    {"id": "ST_Buffer", "label": "Buffer Ready", "type": "State"},
    {"id": "OP_Flush", "label": "Flush Buffer", "type": "Operation"}
  ],
  "edges": [
    {"from": "OP_Flush", "to": "ST_Buffer", "relation": "mutates
""" # あえて途中で切れたレスポンス

parsed = parse_llm_json_response(dummy_raw_llm_output)
graph = normalize_component_graph(parsed, "component-001")
mermaid = generate_mermaid(graph)

print("--- グラフ抽出結果 ---")
print(graph)
print("\n--- Mermaid 生成結果 ---")
print(mermaid)