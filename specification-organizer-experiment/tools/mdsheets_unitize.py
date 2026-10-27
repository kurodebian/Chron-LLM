#!/usr/bin/env python3
# tools/mdsheets_unitize.py
"""
P1 — 章レベル単位画定 (md_sheets deterministic chapter unitization).

Slices the frozen md_sheets corpus (127 chapters) into units at H1
boundaries, driven solely by ledger/mdsheets_chapter_ledger.json
(P0-era H1-slice ledger). No LLM boundary decisions are used: md_sheets
has normative H1 structure, so boundaries are normative-derived.

Guarantees computed as named checks (MISSING_EVIDENCE != PASS):
  - spans partition every corpus file exactly (no gaps, no overlaps),
  - byte-exact concatenation reconstructs each frozen source file
    (digests equal the P0 freeze manifest),
  - every unit starts on an H1 anchor whose step number matches the
    ledger step id,
  - content outside H1 boundaries is preserved as UNRESOLVED segments
    (recorded with line range + full text + digest, never guessed),
  - range-style step references in H1 anchors (e.g. "STEP-31-96") are
    flagged as unresolved headers, never silently attributed.

Status discipline: this artifact is RECORD of deterministic
segmentation evidence only. ARTIFACT_EXISTENCE != NORMATIVE_ADOPTION /
VERIFICATION_IS_NOT_AUTHORIZATION.

Usage:
  python tools/mdsheets_unitize.py               # write artifact
  python tools/mdsheets_unitize.py --print-digest # digest only (determinism probe)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_DIR.parent
LEDGER_PATH = EXPERIMENT_DIR / "ledger" / "mdsheets_chapter_ledger.json"
P0_MANIFEST_PATH = EXPERIMENT_DIR / "ledger" / "corpus_manifest_mdsheets.json"
ARTIFACT_PATH = EXPERIMENT_DIR / "ledger" / "units" / "mdsheets_units.json"
CORPUS_DIR = REPO_ROOT / "md_sheets"
CORPUS_FILES = ("1-74.md", "75-99.md", "100-124.md")

SCHEMA = "chron-llm/mdsheets-units/1"
ARTIFACT_ID = "MDSHEETS-UNITS-P1-01"
STATUS = (
    "RECORDED (deterministic H1 segmentation evidence; "
    "not adoption, not freeze, not acceptance)"
)

# H1 anchor step token: "# **Step 44 ..." or "# **STEP-60 ..." (both styles
# occur in the corpus; anchors were verified to cover all 127 chapters).
ANCHOR_STEP_RE = re.compile(r"^#\s+\*\*(?:STEP|Step)[\s\u3000-]*(\d+)")

# Range-style step reference inside heading text, e.g. "STEP-31-96" with
# hyphen / en-dash / em-dash. The section-dash style "Step 44 \u2014 Title" is safe: its right side
# is not a digit.
RANGE_STEP_REF_RE = re.compile(
    r"(?:STEP|Step)[\s\u3000-]*\d+\s*[-\u2013\u2014]\s*(?:STEP[\s\u3000-]*)?\d+"
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ledger_n_chars(slice_with_endings: str) -> int:
    """Ledger n_chars convention (build_chapters_index.py): the slice read
    via splitlines() (line terminators stripped, CRLF-safe) joined by '\\n'."""
    return len("\n".join(slice_with_endings.splitlines()))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_corpus() -> dict[str, list[str]]:
    """{filename: lines with keepends} preserving exact line endings."""
    return {
        name: (CORPUS_DIR / name).read_text(encoding="utf-8").splitlines(keepends=True)
        for name in CORPUS_FILES
    }


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_digest(obj: Any) -> str:
    """sha256 over the canonical JSON form used for results_digest."""
    return hashlib.sha256(_canonical_json(obj).encode("utf-8")).hexdigest()


def build_units_artifact() -> dict[str, Any]:
    ledger = load_json(LEDGER_PATH)
    p0 = load_json(P0_MANIFEST_PATH)
    corpus = load_corpus()

    units: list[dict[str, Any]] = []
    for c in sorted(ledger["chapters"], key=lambda c: c["seq"]):
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
                "n_lines": c["line_end"] - c["line_start"] + 1,
                "n_chars": ledger_n_chars("".join(sl)),
                "text_sha256": sha256_text("".join(sl)),
                "anchor_line_sha256": sha256_text(
                    corpus[c["file"]][c["line_start"] - 1]
                ),
            }
        )

    # UNRESOLVED segments: any line not covered by a unit span. These are
    # preserved with full evidence; attribution is left to adjudication.
    anchored = {c["seq"]: c for c in ledger["chapters"]}
    unresolved_segments: list[dict[str, Any]] = []
    for name in CORPUS_FILES:
        covered: set[int] = set()
        for c in ledger["chapters"]:
            if c["file"] == name:
                covered.update(range(c["line_start"], c["line_end"] + 1))
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

    # Range-style H1 headers: every H1 line must be a unit anchor or be
    # flagged here. Flagged headers are never attributed to a chapter.
    anchor_pos = {(c["file"], c["line_start"]) for c in ledger["chapters"]}
    unresolved_h1_headers: list[dict[str, Any]] = []
    for name in CORPUS_FILES:
        for i, line in enumerate(corpus[name], start=1):
            if not line.startswith("# "):
                continue
            if (name, i) in anchor_pos:
                if RANGE_STEP_REF_RE.search(line):
                    unresolved_h1_headers.append(
                        {
                            "header_id": "mdsh%03d" % (len(unresolved_h1_headers) + 1),
                            "file": name,
                            "line_start": i,
                            "reason_code": "RANGE_STYLE_STEP_REFERENCE",
                            "text": line.rstrip("\n"),
                            "text_sha256": sha256_text(line),
                        }
                    )
            else:
                # H1 outside ledger anchors: preserve, never guess.
                unresolved_h1_headers.append(
                    {
                        "header_id": "mdsh%03d" % (len(unresolved_h1_headers) + 1),
                        "file": name,
                        "line_start": i,
                        "reason_code": "H1_OUTSIDE_LEDGER_ANCHOR",
                        "text": line.rstrip("\n"),
                        "text_sha256": sha256_text(line),
                    }
                )

    corpus_files = []
    for f in p0["files"]:
        name = f["path"].split("/")[-1]
        if name in CORPUS_FILES:
            corpus_files.append(
                {
                    "file": name,
                    "expected_sha256": f["sha256"],
                    "observed_sha256": sha256_text("".join(corpus[name])),
                    "bytes_observed": len("".join(corpus[name]).encode("utf-8")),
                }
            )

    checks = _compute_checks(
        ledger, units, unresolved_segments, unresolved_h1_headers, corpus, corpus_files
    )

    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "units_artifact_id": ARTIFACT_ID,
        "status": STATUS,
        "generated_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {
            "ledger": "ledger/mdsheets_chapter_ledger.json",
            "ledger_sha256": sha256_text(LEDGER_PATH.read_text(encoding="utf-8")),
            "p0_manifest_id": p0.get("manifest_id"),
            "p0_manifest_sha256": sha256_text(
                P0_MANIFEST_PATH.read_text(encoding="utf-8")
            ),
            "boundary_method": "normative H1 anchors via P0 chapter ledger "
            "(no LLM boundary decisions)",
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
    artifact["results_digest"] = hashlib.sha256(
        _canonical_json(core).encode("utf-8")
    ).hexdigest()
    return artifact


def _segment(name: str, gap: list[int], lines: list[str]) -> dict[str, Any]:
    text = "".join(lines[gap[0] - 1 : gap[-1]])
    return {
        "segment_id": "mdsus%03d" % (gap[0]),
        "file": name,
        "line_start": gap[0],
        "line_end": gap[-1],
        "n_lines": len(gap),
        "n_chars": ledger_n_chars("".join(lines[gap[0] - 1 : gap[-1]])),
        "reason_code": "OUTSIDE_H1_BOUNDARY",
        "text": text,
        "text_sha256": sha256_text(text),
    }


def _compute_checks(
    ledger: dict[str, Any],
    units: list[dict[str, Any]],
    unresolved_segments: list[dict[str, Any]],
    unresolved_h1_headers: list[dict[str, Any]],
    corpus: dict[str, list[str]],
    corpus_files: list[dict[str, Any]],
) -> dict[str, bool]:
    checks: dict[str, bool] = {}

    checks["unit_count_matches_ledger"] = len(units) == len(ledger["chapters"])
    checks["unit_ids_unique"] = len({u["unit_id"] for u in units}) == len(units)
    checks["step_ids_unique"] = len({u["step"] for u in units}) == len(units)
    checks["seq_unique_and_contiguous"] = sorted(u["seq"] for u in units) == list(
        range(1, len(units) + 1)
    )

    checks["anchors_are_h1"] = all(
        corpus[u["file"]][u["line_start"] - 1].startswith("# ") for u in units
    )
    checks["anchor_step_number_matches_unit_step"] = all(
        (m := ANCHOR_STEP_RE.match(corpus[u["file"]][u["line_start"] - 1])) is not None
        and int(m.group(1)) == int(re.match(r"STEP-(\d+)", u["step"]).group(1))
        for u in units
    )
    checks["ledger_spans_consistent"] = all(
        u["n_lines"]
        == next(c for c in ledger["chapters"] if c["seq"] == u["seq"])["line_end"]
        - next(c for c in ledger["chapters"] if c["seq"] == u["seq"])["line_start"]
        + 1
        for u in units
    )

    ok_partition = True
    ok_reconstruct = True
    for name in CORPUS_FILES:
        spans = sorted(
            (
                (s["line_start"], s["line_end"])
                for s in (units + unresolved_segments)
                if s["file"] == name
            )
        )
        pos = 1
        for start, end in spans:
            if start != pos or end < start:
                ok_partition = False
                break
            pos = end + 1
        if pos != len(corpus[name]) + 1:
            ok_partition = False
        rebuilt = "".join(
            "".join(corpus[name][s - 1 : e]) for s, e in spans
        )
        if rebuilt != "".join(corpus[name]):
            ok_reconstruct = False
    checks["spans_partition_files_exactly"] = ok_partition
    checks["byte_exact_reconstruction"] = ok_reconstruct
    checks["corpus_digests_match_p0_freeze"] = all(
        f["observed_sha256"] == f["expected_sha256"] for f in corpus_files
    )

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

    # UNRESOLVED segments must carry evidence, not just ranges.
    checks["unresolved_segments_have_evidence"] = all(
        s.get("text") is not None and s.get("text_sha256") == sha256_text(s["text"])
        for s in unresolved_segments
    )
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument(
        "--print-digest",
        action="store_true",
        help="print results_digest and exit (determinism probe; no write)",
    )
    args = parser.parse_args(argv)

    artifact = build_units_artifact()
    if args.print_digest:
        print(artifact["results_digest"])
        return 0 if all(artifact["checks"].values()) else 1

    failed = sorted(k for k, v in artifact["checks"].items() if not v)
    if failed:
        # MISSING_EVIDENCE != PASS: never write a "passing-looking" artifact.
        print("CHECKS FAILED: " + ", ".join(failed), file=sys.stderr)
        return 1

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {ARTIFACT_PATH}")
    print(f"results_digest {artifact['results_digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
