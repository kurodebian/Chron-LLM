import json

path = "data/delta1_normalized/causal_extract_commit_kernel_v1.json"
with open(path) as f:
    data = json.load(f)

for key in ["authority_boundaries", "key_invariants_detected", "open_questions", "proposals"]:
    items = data.get(key, [])
    print(f"\n=== {key} ({len(items)} items) ===")
    if items:
        print("First item structure:")
        print(json.dumps(items[0], indent=2, ensure_ascii=False))
