# check_basin_ratio.py
from pathlib import Path

for path in Path("specs").rglob("*.spec"):
    text = path.read_text()
    if "Basin.ratio" in text and "len(nodes)" in text:
        print(f"ERROR: Basin.ratio uses len(nodes) in {path}")
        exit(1)

print("OK: Basin.ratio normalization is correct.")

