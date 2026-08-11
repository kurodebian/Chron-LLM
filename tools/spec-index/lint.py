#!/usr/bin/env python3
"""
Chron-LLM Phase 1: Spec Linter (lint.py)
---------------------------------------
Validates structural and physical consistency of facts.jsonl without making
semantic judgments.
"""

import sys
import json
import argparse
from pathlib import Path


def lint_facts(facts_jsonl_path: Path) -> dict:
    records = []
    with open(facts_jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    path_seen = set()
    module_to_paths = {}
    known_modules = set()

    duplicate_paths, duplicate_modules = [], []
    empty_files, missing_versions, missing_modules = [], [], []
    unresolved_dependencies = []

    for r in records:
        if r.get("module"):
            known_modules.add(r["module"])

    for r in records:
        p = r["path"]
        if p in path_seen:
            duplicate_paths.append(p)
        path_seen.add(p)

        if r.get("content_state") == "EMPTY":
            empty_files.append(p)
            continue

        mod = r.get("module")
        if not mod:
            missing_modules.append(p)
        else:
            module_to_paths.setdefault(mod, []).append(p)

        if not r.get("version"):
            missing_versions.append(p)

        deps = (r.get("extends") or []) + (r.get("uses") or [])
        for d in deps:
            if d not in known_modules and d not in [
                "Constitution",
                "BaseTypes",
                "KernelWorld",
            ]:
                unresolved_dependencies.append({"spec": p, "unresolved": d})

    for mod, paths in module_to_paths.items():
        if len(paths) > 1:
            duplicate_modules.append({"module": mod, "paths": paths})

    return {
        "total_records_checked": len(records),
        "valid": len(duplicate_paths) == 0 and len(duplicate_modules) == 0,
        "findings": {
            "duplicate_paths": duplicate_paths,
            "duplicate_modules": duplicate_modules,
            "empty_files": empty_files,
            "missing_modules": missing_modules,
            "missing_versions": missing_versions,
            "unresolved_dependencies_count": len(unresolved_dependencies),
            "unresolved_dependencies_sample": unresolved_dependencies[:10],
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Chron-LLM Physical Spec Fact Linter")
    parser.add_argument(
        "--index",
        type=str,
        default="spec-index/facts.jsonl",
        help="Path to facts.jsonl",
    )
    args = parser.parse_args()

    index_path = Path(args.index).resolve()
    if not index_path.exists():
        print(f"Error: Index file {index_path} does not exist.")
        sys.exit(1)

    report = lint_facts(index_path)
    print("=== Chron-LLM Physical Fact Linter Report ===")
    print(f"Records Checked: {report['total_records_checked']}")
    print(f"Valid Structure: {report['valid']}")
    print(f"Empty Files: {len(report['findings']['empty_files'])}")
    print(f"Missing Module Declarations: {len(report['findings']['missing_modules'])}")
    print(
        f"Missing Version Declarations: {len(report['findings']['missing_versions'])}"
    )
    print(f"Duplicate Modules: {len(report['findings']['duplicate_modules'])}")


if __name__ == "__main__":
    main()
