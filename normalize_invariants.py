#!/usr/bin/env python3
import json, glob

MAP = {"RUN-001": "REP-002", "INV-001": "APP-001"}
for fname in glob.glob("causal_extract_*_v1.json"):
    with open(fname, encoding="utf-8") as f:
        j = json.load(f)
    changed = False
    for p in j.get("proposals", []):
        orig = p.get("related_invariants", [])
        new = [MAP.get(x, x) for x in orig]
        if new != orig:
            p["related_invariants"] = new
            changed = True
    if j.get("key_invariants_detected"):
        j["key_invariants_detected"] = [
            MAP.get(x, x) for x in j["key_invariants_detected"]
        ]
        changed = True
    if changed:
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(j, f, indent=2, ensure_ascii=False)
        print("normalized", fname)
    else:
        print("no change", fname)
