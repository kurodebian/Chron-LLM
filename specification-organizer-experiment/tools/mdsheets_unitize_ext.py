#!/usr/bin/env python3
# tools/mdsheets_unitize_ext.py
"""
P1-EXT — chapter unitization + freeze extension for the 4 unpinned md_sheets
files (125-149.md, 150-174.md, 175-199.md, 200-218.md; 99 chapters).

Boundaries are derived deterministically from the RATIFIED adopted index record
(md_sheets/chapters_index.md, regenerated 2026-10-29, adopted by ratified
ADR-007): its master chapter map lists every H1 chapter with file + anchor line,
and duplicate step numbers carry branch letters (STEP-154a/b …) from the index
branch-numbering convention. No LLM boundary decisions are used.

Guarantees computed as named checks (MISSING_EVIDENCE != PASS):
  - every recorded index anchor resolves to a '# ' H1 line at that exact line,
  - chapter spans (anchor .. next anchor-1, last chapter .. EOF) partition each
    extension file exactly (no gaps, no overlaps),
  - byte-exact concatenation reconstructs each extension file,
  - unit step ids are unique (branch letters), seqs contiguous 128..226
    (continuing the P1 1..127 numbering),
  - every '# ' H1 line is an anchor or flagged; range-style step refs are
    flagged, never attributed,
  - content outside anchors is preserved as UNRESOLVED segments (none expected:
    all extension files start on an anchor).

Artifacts written (RECORDS, not adoption):
  - ledger/mdsheets_chapter_ledger_ext.json   (extension chapter ledger)
  - ledger/units/mdsheets_units_ext.json      (unit pins with digests)
  - ledger/corpus_manifest_mdsheets_ext.json  (CORPUS-FREEZE-MDSHEETS-02)

Status discipline: ARTIFACT_EXISTENCE != NORMATIVE_ADOPTION /
MISSING_EVIDENCE != PASS / VERIFICATION_IS_NOT_AUTHORIZATION.
ADR-006 (ratified): the P2 pass stays scoped to the 127-unit freeze; these 99
units enter scope only via a recorded pass on them after this pin + freeze.
Namespace separation (roadmap §2, D-CCX-01 precedent): md_sheets chapters
STEP-187..218 are separate-domain assets from contracts/governance/step-187..218.

Usage:
  python tools/mdsheets_unitize_ext.py               # write artifacts
  python tools/mdsheets_unitize_ext.py --print-digest  # digest only, no write
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
if str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from tools.mdsheets_unitize import (
    ANCHOR_STEP_RE,
    RANGE_STEP_REF_RE,
    canonical_digest,
    ledger_n_chars,
    sha256_text,
)

EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_DIR.parent
INDEX_PATH = REPO_ROOT / "md_sheets" / "chapters_index.md"
LEDGER_EXT_PATH = EXPERIMENT_DIR / "ledger" / "mdsheets_chapter_ledger_ext.json"
UNITS_EXT_PATH = EXPERIMENT_DIR / "ledger" / "units" / "mdsheets_units_ext.json"
MANIFEST_EXT_PATH = EXPERIMENT_DIR / "ledger" / "corpus_manifest_mdsheets_ext.json"
CORPUS_DIR = REPO_ROOT / "md_sheets"
CORPUS_FILES = ("125-149.md", "150-174.md", "175-199.md", "200-218.md")

SCHEMA = "chron-llm/mdsheets-units-ext/1"
ARTIFACT_ID = "MDSHEETS-UNITS-EXT-01"
LEDGER_ID = "MDSHEETS-CHAPTER-LEDGER-EXT-01"
MANIFEST_ID = "CORPUS-FREEZE-MDSHEETS-02"
STATUS = (
    "RECORDED (deterministic H1 segmentation evidence from ratified index; "
    "not adoption, not freeze acceptance, not scope authorization)"
)
FREEZE_STATUS = "RECORDED (record of freeze; not adoption)"

SEQ_BASE = 128  # continues P1 seqs 1..127

# Master chapter map row: | seq | `STEP-x` | title | `file` | line |
MASTER_ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|\s*`(STEP-[0-9]+[a-z]?)\s*`\s*\|([^|]*)\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|"
)


def load_index_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    in_map = False
    for line in INDEX_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Master chapter map"):
            in_map = True
            continue
        if in_map and line.startswith("## "):
            in_map = False
            continue
        if not in_map:
            continue
        m = MASTER_ROW_RE.match(line)
        if m:
            seq, step, title, fname, anchor_line = m.groups()
            rows.append(
                {
                    "seq": int(seq),
                    "step": step,
                    "title": title.strip(),
                    "file": fname,
                    "line_start": int(anchor_line),
                }
            )
    return rows


def load_corpus() -> dict[str, list[str]]:
    return {
        name: (CORPUS_DIR / name).read_text(encoding="utf-8").splitlines(keepends=True)
        for name in CORPUS_FILES
    }


def build_ext_ledger() -> dict[str, Any]:
    rows = load_index_rows()
    corpus = load_corpus()
    chapters: list[dict[str, Any]] = []
    per_file_rows: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        if r["file"] in CORPUS_FILES:
            per_file_rows.setdefault(r["file"], []).append(r)
    for name in CORPUS_FILES:
        fr = sorted(per_file_rows.get(name, []), key=lambda r: r["line_start"])
        for i, r in enumerate(fr):
            end = fr[i + 1]["line_start"] - 1 if i + 1 < len(fr) else len(corpus[name])
            sl = corpus[name][r["line_start"] - 1 : end]
            chapters.append(
                {
                    "seq": r["seq"],
                    "step": r["step"],
                    "title": r["title"],
                    "file": name,
                    "line_start": r["line_start"],
                    "line_end": end,
                    "n_lines": end - r["line_start"] + 1,
                    "n_chars": ledger_n_chars("".join(sl)),
                    "clusters": [],
                    "status": "UNSCANNED (implementation scan not performed in this run)",
                    "candidate_lineage": [],
                }
            )
    chapters.sort(key=lambda c: c["seq"])
    return {
        "meta": {
            "ledger_id": LEDGER_ID,
            "status": STATUS,
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "derived_from": "md_sheets/chapters_index.md master chapter map "
            "(ratified index record, ADR-007 RATIFIED_HUMAN)",
            "boundary_method": "normative H1 anchors via adopted index "
            "(no LLM boundary decisions)",
            "seq_range": [SEQ_BASE, SEQ_BASE + len(chapters) - 1],
            "namespace_separation": (
                "md_sheets chapters STEP-187..218 are separate-domain assets from "
                "contracts/governance/step-187..218 (D-CCX-01 precedent; namespace "
                "separation deferred to a follow-on contract)"
            ),
        },
        "chapters": chapters,
    }


def build_units_ext_artifact(ledger_ext: dict[str, Any]) -> dict[str, Any]:
    corpus = load_corpus()
    units: list[dict[str, Any]] = []
    for c in ledger_ext["chapters"]:
        sl = corpus[c["file"]][c["line_start"] - 1 : c["line_end"]]
        units.append(
            {
                "unit_id": "mdsu%04d" % c["seq"],
                "seq": c["seq"],
                "step": c["step"],
                "title": c["title"],
                "file": c["file"],
                "line_start": c["line_start"],
                "line_end": c["line_end"],
                "n_lines": c["n_lines"],
                "n_chars": c["n_chars"],
                "text_sha256": sha256_text("".join(sl)),
                "anchor_line_sha256": sha256_text(
                    corpus[c["file"]][c["line_start"] - 1]
                ),
            }
        )

    unresolved_segments: list[dict[str, Any]] = []
    for name in CORPUS_FILES:
        covered: set[int] = set()
        for u in units:
            if u["file"] == name:
                covered.update(range(u["line_start"], u["line_end"] + 1))
        lines = corpus[name]
        gap: list[int] = []
        for i in range(1, len(lines) + 1):
            if i not in covered:
                gap.append(i)
            elif gap:
                unresolved_segments.append(_segment(name, gap, lines))
                gap = []
        if gap:
            unresolved_segments.append(_segment(name, gap, lines))

    anchor_pos = {(u["file"], u["line_start"]) for u in units}
    unresolved_h1_headers: list[dict[str, Any]] = []
    for name in CORPUS_FILES:
        for i, line in enumerate(corpus[name], start=1):
            if not line.startswith("# "):
                continue
            if (name, i) in anchor_pos:
                if RANGE_STEP_REF_RE.search(line):
                    unresolved_h1_headers.append(
                        {
                            "header_id": "mdshx%03d" % (len(unresolved_h1_headers) + 1),
                            "file": name,
                            "line_start": i,
                            "reason_code": "RANGE_STYLE_STEP_REFERENCE",
                            "text": line.rstrip("\n"),
                            "text_sha256": sha256_text(line),
                        }
                    )
            else:
                unresolved_h1_headers.append(
                    {
                        "header_id": "mdshx%03d" % (len(unresolved_h1_headers) + 1),
                        "file": name,
                        "line_start": i,
                        "reason_code": "H1_OUTSIDE_INDEX_ANCHOR",
                        "text": line.rstrip("\n"),
                        "text_sha256": sha256_text(line),
                    }
                )

    corpus_files = [
        {
            "file": name,
            "observed_sha256": sha256_text("".join(corpus[name])),
            "bytes_observed": len("".join(corpus[name]).encode("utf-8")),
        }
        for name in CORPUS_FILES
    ]

    checks = _compute_checks(
        ledger_ext, units, unresolved_segments, unresolved_h1_headers, corpus
    )

    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "units_artifact_id": ARTIFACT_ID,
        "status": STATUS,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {
            "index": "md_sheets/chapters_index.md",
            "index_sha256": sha256_text(INDEX_PATH.read_text(encoding="utf-8")),
            "ledger_ext": "ledger/mdsheets_chapter_ledger_ext.json",
            "boundary_method": "normative H1 anchors via ratified index record "
            "(ADR-007 RATIFIED_HUMAN; branch-letter step ids from index registry)",
            "anchor_digest_convention": "LF-only corpus lines; digest over the anchor "
            "line as read (ADR-008 RATIFIED_HUMAN)",
            "scope_note": "ADR-006 RATIFIED_HUMAN: P2 pass stays scoped to the 127-unit "
            "freeze until a recorded pass covers these extension units",
            "discipline": [
                "ARTIFACT_EXISTENCE != NORMATIVE_ADOPTION",
                "MISSING_EVIDENCE != PASS",
                "VERIFICATION_IS_NOT_AUTHORIZATION",
            ],
        },
        "corpus_files": corpus_files,
        "n_units": len(units),
        "units": units,
        "unresolved_segments": unresolved_segments,
        "unresolved_h1_headers": unresolved_h1_headers,
        "checks": checks,
    }
    core = {k: v for k, v in artifact.items() if k not in ("results_digest", "generated_utc")}
    artifact["results_digest"] = canonical_digest(core)
    return artifact


def _segment(name: str, gap: list[int], lines: list[str]) -> dict[str, Any]:
    text = "".join(lines[gap[0] - 1 : gap[-1]])
    return {
        "segment_id": "mdsusx%04d" % gap[0],
        "file": name,
        "line_start": gap[0],
        "line_end": gap[-1],
        "n_lines": len(gap),
        "n_chars": ledger_n_chars(text),
        "reason_code": "OUTSIDE_H1_BOUNDARY",
        "text": text,
        "text_sha256": sha256_text(text),
    }


def _compute_checks(
    ledger_ext: dict[str, Any],
    units: list[dict[str, Any]],
    unresolved_segments: list[dict[str, Any]],
    unresolved_h1_headers: list[dict[str, Any]],
    corpus: dict[str, list[str]],
) -> dict[str, bool]:
    checks: dict[str, bool] = {}

    checks["unit_count_matches_ext_ledger"] = len(units) == len(ledger_ext["chapters"]) == 99
    checks["unit_ids_unique"] = len({u["unit_id"] for u in units}) == len(units)
    checks["step_ids_unique"] = len({u["step"] for u in units}) == len(units)
    checks["seq_contiguous_after_p1"] = sorted(u["seq"] for u in units) == list(
        range(SEQ_BASE, SEQ_BASE + len(units))
    )
    checks["anchors_are_h1"] = all(
        corpus[u["file"]][u["line_start"] - 1].startswith("# ") for u in units
    )
    checks["anchor_step_number_matches_unit_step"] = all(
        (m := ANCHOR_STEP_RE.match(corpus[u["file"]][u["line_start"] - 1])) is not None
        and int(m.group(1)) == int(re.match(r"STEP-(\d+)", u["step"]).group(1))
        for u in units
    )
    checks["unit_text_sha256_matches_slice"] = all(
        u["text_sha256"] == sha256_text("".join(corpus[u["file"]][u["line_start"] - 1 : u["line_end"]]))
        for u in units
    )

    ok_partition = True
    ok_reconstruct = True
    for name in CORPUS_FILES:
        spans = sorted(
            (s["line_start"], s["line_end"])
            for s in (units + unresolved_segments)
            if s["file"] == name
        )
        pos = 1
        for start, end in spans:
            if start != pos or end < start:
                ok_partition = False
                break
            pos = end + 1
        if pos != len(corpus[name]) + 1:
            ok_partition = False
        rebuilt = "".join("".join(corpus[name][s - 1 : e]) for s, e in spans)
        if rebuilt != "".join(corpus[name]):
            ok_reconstruct = False
    checks["spans_partition_files_exactly"] = ok_partition
    checks["byte_exact_reconstruction"] = ok_reconstruct

    anchor_pos = {(u["file"], u["line_start"]) for u in units}
    flagged_pos = {(h["file"], h["line_start"]) for h in unresolved_h1_headers}
    checks["all_h1_lines_accounted"] = all(
        (name, i) in anchor_pos or (name, i) in flagged_pos
        for name in CORPUS_FILES
        for i, line in enumerate(corpus[name], start=1)
        if line.startswith("# ")
    )
    checks["h1_count_matches_units"] = (
        sum(1 for name in CORPUS_FILES for line in corpus[name] if line.startswith("# "))
        == len(units) + len(flagged_pos)
    )
    checks["no_range_style_step_refs_in_anchors"] = not any(
        RANGE_STEP_REF_RE.search(corpus[u["file"]][u["line_start"] - 1]) for u in units
    )
    checks["unresolved_segments_have_evidence"] = all(
        s.get("text") is not None and s.get("text_sha256") == sha256_text(s["text"])
        for s in unresolved_segments
    )
    return checks


def build_manifest_ext(units_artifact: dict[str, Any]) -> dict[str, Any]:
    files = []
    for name in CORPUS_FILES:
        text = (CORPUS_DIR / name).read_text(encoding="utf-8")
        files.append(
            {"path": f"md_sheets/{name}", "sha256": sha256_text(text), "bytes": len(text.encode("utf-8"))}
        )
    idx_text = INDEX_PATH.read_text(encoding="utf-8")
    files.append(
        {
            "path": "md_sheets/chapters_index.md",
            "sha256": sha256_text(idx_text),
            "bytes": len(idx_text.encode("utf-8")),
            "note": "re-recorded adopted index record (ADR-007 RATIFIED_HUMAN); "
            "supersedes CORPUS-FREEZE-MDSHEETS-01 index entry ea49cecc…",
        }
    )
    for p in (LEDGER_EXT_PATH, UNITS_EXT_PATH):
        data = p.read_bytes()
        files.append(
            {"path": str(p.relative_to(REPO_ROOT)), "sha256": sha256_text(data.decode("utf-8")), "bytes": len(data)}
        )
    return {
        "manifest_id": MANIFEST_ID,
        "status": FREEZE_STATUS,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "sha256 over file bytes; re-hash to verify",
        "scope": "extension freeze: 99 chapters in 125-149.md, 150-174.md, "
        "175-199.md, 200-218.md (ADR-006 RATIFIED_HUMAN prerequisite)",
        "files": files,
        "n_chapters": 99,
        "notes": [
            "freeze is a record, not adoption (ARTIFACT_EXISTENCE != NORMATIVE_ADOPTION)",
            "CORPUS-FREEZE-MDSHEETS-01 (127-unit freeze) untouched and byte-identical",
            "namespace separation: md_sheets STEP-187..218 vs contracts/governance step-187..218 "
            "are separate domains (D-CCX-01 precedent; deferred contract)",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument(
        "--print-digest",
        action="store_true",
        help="print results_digest and exit (determinism probe; no write)",
    )
    args = parser.parse_args(argv)

    ledger_ext = build_ext_ledger()
    units_artifact = build_units_ext_artifact(ledger_ext)
    if args.print_digest:
        print(units_artifact["results_digest"])
        return 0 if all(units_artifact["checks"].values()) else 1

    failed = sorted(k for k, v in units_artifact["checks"].items() if not v)
    if failed:
        # MISSING_EVIDENCE != PASS: never write a "passing-looking" artifact.
        print("CHECKS FAILED: " + ", ".join(failed), file=sys.stderr)
        return 1

    LEDGER_EXT_PATH.write_text(
        json.dumps(ledger_ext, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    UNITS_EXT_PATH.parent.mkdir(parents=True, exist_ok=True)
    UNITS_EXT_PATH.write_text(
        json.dumps(units_artifact, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = build_manifest_ext(units_artifact)
    MANIFEST_EXT_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {LEDGER_EXT_PATH}")
    print(f"wrote {UNITS_EXT_PATH}")
    print(f"wrote {MANIFEST_EXT_PATH}")
    print(f"results_digest {units_artifact['results_digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
