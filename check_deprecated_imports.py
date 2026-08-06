# check_deprecated_imports.py
from pathlib import Path

deprecated = [p.name for p in Path("specs/archive").rglob("*.spec")]

for path in Path("specs/active").rglob("*.spec"):
    text = path.read_text()
    for dep in deprecated:
        if dep in text:
            print(f"ERROR: {path} imports deprecated file {dep}")
            exit(1)

print("OK: No deprecated imports.")

