#!/usr/bin/env python3
"""
Chron-LLM Phase 1: Spec Preprocessor (preprocess.py)
---------------------------------------------------
Physical, lexical, and structural fact extractor for .spec files.

STRICT SAFETY CONSTRAINTS:
- FACT-ONLY: NO semantic normalization, NO canonical judgments, NO supersession claims,
  NO rename or move suggestions.
- Preserves empty files (recorded as content_state="EMPTY").
- Computes SHA256 for physical file verification and auditability.
"""

import os
import sys
import argparse
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime, timezone

DEFAULT_EXCLUDE_DIRS = {"archive", "archival", "backup", ".git", "node_modules", "venv", "__pycache__"}

def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def parse_header_and_body(content: str):
    lines = content.splitlines()

    module = None
    version = None
    raw_status = "not_declared"
    extends, uses, defines, declares = [], [], [], []
    operations, invariants, theorems, policies = [], [], [], []
    contracts, excludes, boundary_claims = [], [], []
    sections = []

    comment_lines = 0
    non_comment_lines = 0

    # Key extraction regexes
    module_re = re.compile(r"^(?:#|//|;|\*)*\s*(?:MODULE|Module|SPEC|Spec|NAME|Name)\s*[:=]\s*(.+)$", re.IGNORECASE)
    version_re = re.compile(r"^(?:#|//|;|\*)*\s*(?:VERSION|Version|REV|Revision)\s*[:=]\s*(.+)$", re.IGNORECASE)
    status_re = re.compile(r"^(?:#|//|;|\*)*\s*(?:STATUS|Status)\s*[:=]\s*(.+)$", re.IGNORECASE)
    extends_re = re.compile(r"^(?:#|//|;|\*)*\s*(?:EXTENDS|Extends|INHERITS|Inherits)\s*[:=]\s*(.+)$", re.IGNORECASE)
    uses_re = re.compile(r"^(?:#|//|;|\*)*\s*(?:USES|Uses|DEPENDENCIES|Dependencies|DEPENDS|Depends)\s*[:=]\s*(.+)$", re.IGNORECASE)
    defines_re = re.compile(r"^(?:#|//|;|\*)*\s*(?:DEFINES|Defines|TYPES|Types|ENTITIES|Entities)\s*[:=]\s*(.+)$", re.IGNORECASE)
    declares_re = re.compile(r"^(?:#|//|;|\*)*\s*(?:DECLARES|Declares)\s*[:=]\s*(.+)$", re.IGNORECASE)
    ops_re = re.compile(r"^(?:#|//|;|\*)*\s*(?:OPERATIONS|Operations|OPS|Ops)\s*[:=]\s*(.+)$", re.IGNORECASE)
    inv_re = re.compile(r"^(?:#|//|;|\*)*\s*(?:INVARIANTS|Invariants|INV|Inv)\s*[:=]\s*(.+)$", re.IGNORECASE)
    thm_re = re.compile(r"^(?:#|//|;|\*)*\s*(?:THEOREMS|Theorems)\s*[:=]\s*(.+)$", re.IGNORECASE)
    pol_re = re.compile(r"^(?:#|//|;|\*)*\s*(?:POLICIES|Policies)\s*[:=]\s*(.+)$", re.IGNORECASE)
    cnt_re = re.compile(r"^(?:#|//|;|\*)*\s*(?:CONTRACTS|Contracts)\s*[:=]\s*(.+)$", re.IGNORECASE)
    excl_re = re.compile(r"^(?:#|//|;|\*)*\s*(?:EXCLUDES|Excludes|NON-GOALS|Non-Goals)\s*[:=]\s*(.+)$", re.IGNORECASE)
    bound_re = re.compile(r"^(?:#|//|;|\*)*\s*(?:BOUNDARY|Boundary|SCOPE|Scope)\s*[:=]\s*(.+)$", re.IGNORECASE)
    section_re = re.compile(r"^\s*(?:#+|\d+\.|\b[A-Z][A-Za-z0-9 _-]{2,}:)\s*(.+)$")

    def split_csv(text):
        return [item.strip() for item in re.split(r"[,;|\s]+", text) if item.strip()]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith(("#", "//", ";", "/*", "*")):
            comment_lines += 1
        else:
            non_comment_lines += 1

        # Check section headers
        if line.startswith(("#", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")) or (line.isupper() and len(line) < 40):
            m_sec = section_re.match(stripped)
            if m_sec:
                sec_title = m_sec.group(1).strip("#* ")
                if sec_title and sec_title not in sections:
                    sections.append(sec_title)

        # Header tag extractions
        if m := module_re.match(stripped):
            if not module: module = m.group(1).strip()
        if m := version_re.match(stripped):
            if not version: version = m.group(1).strip()
        if m := status_re.match(stripped): raw_status = m.group(1).strip()
        if m := extends_re.match(stripped): extends.extend(split_csv(m.group(1)))
        if m := uses_re.match(stripped): uses.extend(split_csv(m.group(1)))
        if m := defines_re.match(stripped): defines.extend(split_csv(m.group(1)))
        if m := declares_re.match(stripped): declares.extend(split_csv(m.group(1)))
        if m := ops_re.match(stripped): operations.extend(split_csv(m.group(1)))
        if m := inv_re.match(stripped): invariants.extend(split_csv(m.group(1)))
        if m := thm_re.match(stripped): theorems.extend(split_csv(m.group(1)))
        if m := pol_re.match(stripped): policies.extend(split_csv(m.group(1)))
        if m := cnt_re.match(stripped): contracts.extend(split_csv(m.group(1)))
        if m := excl_re.match(stripped): excludes.extend(split_csv(m.group(1)))
        if m := bound_re.match(stripped): boundary_claims.extend(split_csv(m.group(1)))

        if "does_not_" in stripped or "authority_scope" in stripped:
            if stripped not in boundary_claims:
                boundary_claims.append(stripped)

    if not module:
        for sec in sections:
            if sec and not sec.startswith("1") and len(sec) < 50:
                module = sec
                break

    return {
        "module": module,
        "version": version,
        "raw_status": raw_status,
        "extends": sorted(list(set(extends))),
        "uses": sorted(list(set(uses))),
        "defines": sorted(list(set(defines))),
        "declares": sorted(list(set(declares))),
        "operations": sorted(list(set(operations))),
        "invariants": sorted(list(set(invariants))),
        "theorems": sorted(list(set(theorems))),
        "policies": sorted(list(set(policies))),
        "contracts": sorted(list(set(contracts))),
        "excludes": sorted(list(set(excludes))),
        "boundary_claims": sorted(list(set(boundary_claims))),
        "structure": {
            "sections": sections,
            "comment_lines": comment_lines,
            "non_comment_lines": non_comment_lines
        }
    }

def process_spec_file(filepath: Path, root_dir: Path) -> dict:
    rel_path = filepath.relative_to(root_dir).as_posix()
    size = filepath.stat().st_size
    sha256 = compute_sha256(filepath)

    if size == 0:
        return {
            "path": rel_path,
            "sha256": sha256,
            "size": 0,
            "lines": 0,
            "content_state": "EMPTY",
            "module": None,
            "version": None,
            "raw_status": "not_declared",
            "extends": [], "uses": [], "defines": [], "declares": [],
            "operations": [], "invariants": [], "theorems": [], "policies": [],
            "contracts": [], "excludes": [], "boundary_claims": [],
            "structure": { "sections": [], "comment_lines": 0, "non_comment_lines": 0 },
            "fact_only": True
        }

    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        content = ""

    lines_count = len(content.splitlines()) if content else 0
    parsed = parse_header_and_body(content)

    return {
        "path": rel_path,
        "sha256": sha256,
        "size": size,
        "lines": lines_count,
        "content_state": "NON_EMPTY",
        "module": parsed["module"],
        "version": parsed["version"],
        "raw_status": parsed["raw_status"],
        "extends": parsed["extends"],
        "uses": parsed["uses"],
        "defines": parsed["defines"],
        "declares": parsed["declares"],
        "operations": parsed["operations"],
        "invariants": parsed["invariants"],
        "theorems": parsed["theorems"],
        "policies": parsed["policies"],
        "contracts": parsed["contracts"],
        "excludes": parsed["excludes"],
        "boundary_claims": parsed["boundary_claims"],
        "structure": parsed["structure"],
        "fact_only": True
    }

def main():
    parser = argparse.ArgumentParser(description="Chron-LLM Phase 1 Physical Spec Fact Extractor")
    parser.add_argument("--root", type=str, default=".", help="Root repository directory to scan")
    parser.add_argument("--output-dir", type=str, default="spec-index", help="Output directory for index artifacts")
    parser.add_argument("--exclude-dirs", nargs="*", default=list(DEFAULT_EXCLUDE_DIRS), help="Directory names to exclude")
    args = parser.parse_args()

    root_dir = Path(args.root).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    exclude_set = set(args.exclude_dirs)
    spec_files = [p for p in root_dir.rglob("*.spec") if not any(part in exclude_set for part in p.relative_to(root_dir).parts[:-1])]
    spec_files.sort(key=lambda p: p.as_posix())

    records, empty_count, non_empty_count = [], 0, 0
    for s_file in spec_files:
        rec = process_spec_file(s_file, root_dir)
        records.append(rec)
        if rec["content_state"] == "EMPTY": empty_count += 1
        else: non_empty_count += 1

    facts_jsonl_path = out_dir / "facts.jsonl"
    jsonl_hasher = hashlib.sha256()

    with open(facts_jsonl_path, "w", encoding="utf-8") as f:
        for rec in records:
            line = json.dumps(rec, ensure_ascii=False) + "\n"
            f.write(line)
            jsonl_hasher.update(line.encode("utf-8"))

    manifest_meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root_directory": str(root_dir),
        "total_spec_files": len(records),
        "non_empty_files": non_empty_count,
        "empty_files": empty_count,
        "facts_jsonl_path": facts_jsonl_path.name,
        "facts_jsonl_sha256": jsonl_hasher.hexdigest(),
        "schema_version": "1.0.0",
        "phase": "PHASE_1_PREPROCESSOR_PHYSICAL_FACTS_ONLY"
    }

    with open(out_dir / "manifest-meta.json", "w", encoding="utf-8") as f:
        json.dump(manifest_meta, f, indent=2, ensure_ascii=False)

    print(f"Preprocess complete. Total: {len(records)} (Non-empty: {non_empty_count}, Empty: {empty_count})")

if __name__ == "__main__":
    main()