# normalize_fields.py
from pathlib import Path
import re

for path in Path("specs").rglob("*.spec"):
    text = path.read_text()
    new = (
        text.replace("strength", "str")
        .replace("relation", "rel")
        .replace("Symbol", "ID")
    )
    if new != text:
        path.write_text(new)
        print(f"Normalized: {path}")
