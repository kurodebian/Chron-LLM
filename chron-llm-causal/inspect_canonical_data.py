# inspect_canonical_data.py
import json
import os

files = [
    'data/delta1_normalized/causal_extract_core_v1.json',
    'data/delta1_normalized/causal_extract_core_v2.json',
    'data/graphs/causal_master_graph_v2.json',
    'delta1_delta2_traceability.json'
]

for p in files:
    print(f"\n==================== {p} ====================")
    if not os.path.exists(p):
        print("FILE NOT FOUND")
        continue
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print('Type:', type(data).__name__)
    if isinstance(data, dict):
        print('Root Keys:', list(data.keys()))
        for k, v in data.items():
            if isinstance(v, list):
                print(f'  - Key "{k}": count={len(v)}')
                if len(v) > 0:
                    print(f'    Sample "{k}"[0]:')
                    print(json.dumps(v[0], indent=2, ensure_ascii=False)[:500])
            elif isinstance(v, dict):
                print(f'  - Key "{k}": dict keys={list(v.keys())[:5]}')
            else:
                print(f'  - Key "{k}": {v}')
    elif isinstance(data, list):
        print('Length:', len(data))
        if len(data) > 0:
            print('Sample [0]:')
            print(json.dumps(data[0], indent=2, ensure_ascii=False)[:500])