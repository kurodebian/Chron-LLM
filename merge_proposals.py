#!/usr/bin/env python3
import json, glob

master = {"nodes": {}, "edges": []}
for fname in glob.glob("causal_extract_*_v1.json"):
    with open(fname, encoding="utf-8") as f:
        j = json.load(f)
    for p in j.get("proposals", []):
        pid = p.get("id")
        if pid not in master["nodes"]:
            master["nodes"][pid] = {
                "id": pid,
                "type": p.get("type"),
                "source": p.get("source"),
                "target": p.get("target"),
                "notes": p.get("notes", ""),
                "confidence": p.get("confidence", 0.0),
            }
        master["edges"].append(
            {
                "from": p.get("source"),
                "to": p.get("target"),
                "dir": p.get("direction"),
                "proposal_id": pid,
                "confidence": p.get("confidence", 0.0),
            }
        )
with open("causal_master_graph.json", "w", encoding="utf-8") as f:
    json.dump(master, f, indent=2, ensure_ascii=False)
print("wrote causal_master_graph.json")
