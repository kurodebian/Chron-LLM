# check_types.py
from pathlib import Path
import re

SOT = "chron-llm-spec-v0.2.spec"
TYPES = ["Node", "Edge", "Graph", "Basin"]

for path in Path("specs").rglob("*.spec"):
    if path.name == SOT:
        continue

    text = path.read_text()
    for t in TYPES:
        if re.search(rf"type\s+{t}\b", text):
            print(f"ERROR: {t} defined in {path}")
            exit(1)

print("OK: No duplicate type definitions.")

