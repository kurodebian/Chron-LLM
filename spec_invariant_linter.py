#!/usr/bin/env python3
"""
Chron-LLM Specification Invariant & Integrity Linter (spec_invariant_linter.py)

Checks:
1. Reference Integrity: Active specs must not reference deprecated/archived files.
2. Package Declaration Alignment: Verifies PKG statements in active test specifications.
3. Invariant Syntax & Naming: Validates [INVARIANT: ...] constructs in active specs.
"""

import os
import re
import sys
from pathlib import Path

DEPRECATED_FILES = ["prefill.spec", "projection.spec", "world.spec", "registry.spec"]

def lint_spec_files(root_dir="."):
    root = Path(root_dir)
    spec_files = list(root.glob("**/*.spec"))
    
    errors = []
    warnings = []
    checked_count = 0

    print("=" * 70)
    print(f"🔍 Chron-LLM Spec Invariant Linter")
    print(f"   Scanning {len(spec_files)} .spec file(s) across repository...")
    print("=" * 70)

    for spec_path in spec_files:
        rel_path = spec_path.relative_to(root)
        
        # archive/ 配下（退避ファイルおよびバックアップフォルダ）はアクティブチェック対象外とする
        is_archived = str(rel_path).startswith("archive/") or "archive" in rel_path.parts
        
        try:
            content = spec_path.read_text(encoding="utf-8")
        except Exception as e:
            errors.append(f"[{rel_path}] Unable to read file: {e}")
            continue

        checked_count += 1
        lines = content.splitlines()

        # ---------------------------------------------------------------------
        # Check 1: Deprecated file reference in active specs
        # ---------------------------------------------------------------------
        if not is_archived:
            for dep in DEPRECATED_FILES:
                for line_no, line in enumerate(lines, 1):
                    if "DEPRECATED" in line or "SUPERSEDED" in line:
                        continue
                    if dep in line and not line.strip().startswith("//"):
                        warnings.append(
                            f"[{rel_path}:{line_no}] Refers to deprecated file '{dep}': {line.strip()}"
                        )

        # ---------------------------------------------------------------------
        # Check 2: PKG declaration check for active r2-0-b-tests.spec
        # ---------------------------------------------------------------------
        if not is_archived and "r2-0-b-tests.spec" in str(rel_path):
            match = re.search(r"^PKG\s+([^\s]+)", content, re.MULTILINE)
            if match:
                pkg_name = match.group(1)
                if pkg_name != "chron-r2-0-b":
                    errors.append(
                        f"[{rel_path}] Invalid PKG declaration '{pkg_name}'. Expected 'chron-r2-0-b'."
                    )
            else:
                errors.append(f"[{rel_path}] Missing 'PKG' declaration.")

        # ---------------------------------------------------------------------
        # Check 3: Invariant definition syntax checking (active specs only)
        # ---------------------------------------------------------------------
        if not is_archived:
            for line_no, line in enumerate(lines, 1):
                line_str = line.strip()
                if line_str.startswith("[INVARIANT:"):
                    if not line_str.endswith("]"):
                        errors.append(
                            f"[{rel_path}:{line_no}] Malformed [INVARIANT:] header: '{line_str}'"
                        )

    print(f"\n📊 Summary Report:")
    print(f"  ・ Files Scanned: {checked_count}")
    print(f"  ・ Errors:        {len(errors)}")
    print(f"  ・ Warnings:      {len(warnings)}")
    print("-" * 70)

    if warnings:
        print("\n⚠️  WARNINGS:")
        for w in warnings:
            print(f"  • {w}")

    if errors:
        print("\n❌ ERRORS:")
        for e in errors:
            print(f"  • {e}")
        print("\n💥 Spec Invariant Linting FAILED.")
        sys.exit(1)
    else:
        print("\n✅ All Active Spec Invariants and Reference Rules Passed Successfully!")
        sys.exit(0)

if __name__ == "__main__":
    lint_spec_files()
