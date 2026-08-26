import json

path = "data/delta1_normalized/causal_extract_commit_kernel_v1.json"
with open(path) as f:
    data = json.load(f)

print("Top-level keys:", list(data.keys()) if isinstance(data, dict) else type(data))

# トップレベルが dict の場合、主要なキーの型とサンプルを表示
if isinstance(data, dict):
    for k, v in data.items():
        if isinstance(v, list):
            print(f"  Key '{k}': List with {len(v)} elements")
            if v and isinstance(v[0], dict):
                print(f"    First item keys: {list(v[0].keys())}")
        else:
            print(f"  Key '{k}': Type {type(v).__name__}")
