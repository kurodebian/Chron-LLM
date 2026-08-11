import glob
import re
import sys

DEPRECATED_PATTERNS = [
    (
        re.compile(r"Phase\s*=\s*\{0:prefill"),
        "Deprecated lowercase Phase definition found. Use {{0:PREFILL | 1:GENERATION | 2:FINALIZE}}.",
    ),
    (
        re.compile(r"STATE\s*\*ir-stream\*"),
        "Deprecated global array STATE *ir-stream* found. Use ir.IR_Buffer.",
    ),
]

REQUIRED_INVARIANTS = ["INV-IMMUTABLE", "INV-OBS-ONLY"]


def lint_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    errors = []

    # 1. Deprecated pattern check
    for pattern, msg in DEPRECATED_PATTERNS:
        if pattern.search(content):
            errors.append(f"[DEPRECATED ERROR] {msg}")

    # 2. Syntax / Structure checks (Allow PKG, MODULE, or MOD)
    if "PKG " not in content and "MODULE " not in content and "MOD " not in content:
        errors.append(
            "[SYNTAX ERROR] Spec file missing PKG, MODULE, or MOD declaration."
        )

    return errors


def main():
    spec_files = glob.glob("runtime/ir/**/*.spec", recursive=True)
    total_errors = 0

    for filepath in spec_files:
        print(f"Linting {filepath}...")
        errs = lint_file(filepath)
        for e in errs:
            print(f"  ❌ {e}")
            total_errors += 1

    if total_errors > 0:
        print(f"\nSpec lint failed with {total_errors} errors.")
        sys.exit(1)
    else:
        print("\nAll spec files passed validation successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
