"""
P2 independent verifier (read-only; writes nothing).

Re-derives the full P2 gate from first principles, WITHOUT trusting
report.json:
  1. every ledger unit (all 127) reconstructs sha-exactly from the corpus
  2. every unit has exactly one OK extraction_log entry whose record_sha256
     equals the sha256 of the bytes on disk (1unit=1request pairing)
  3. every on-disk record passes the validator authority (validate_dm2 +
     mechanically-derived md_sheets schema profile) against the freshly
     reconstructed canonical unit — schema AND semantic enforced atomically
  4. evidence phrases are exact substrings of the canonical source and
     evidence lines lie inside the unit line span
  5. unresolved preservation: ledger unresolved_segments still match the
     corpus byte-for-byte (preamble 1-74.md L1-33, OUTSIDE_H1_BOUNDARY)
  6. corpus layer untouched: observed_sha256 in ledger == live file digests

Exit 0 iff every check passes for every unit; MISSING_EVIDENCE != PASS:
a unit without an OK entry or without a record file is a FAIL, never a skip.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from tools import validate_dm2  # noqa: E402
from tools.mdsheets_dm2_runner import (  # noqa: E402
    DEFAULT_CORPUS_DIR,
    DEFAULT_UNITS_PATH,
    PROFILE_SCHEMA_PATH,
    UnitReconstructionError,
    canonical_from_unit,
    load_corpus,
    load_units,
    reconstruct_unit,
    record_filename,
    validator_schema_profile,
)

ROOT = HERE.parent


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(ROOT / "results/mdsheets-dm2"))
    ap.add_argument("--units", default=str(DEFAULT_UNITS_PATH))
    ap.add_argument("--corpus", default=str(DEFAULT_CORPUS_DIR))
    args = ap.parse_args()

    results = Path(args.results)
    units = load_units(Path(args.units))
    corpus = load_corpus(Path(args.corpus))

    log_entries = [
        json.loads(l)
        for l in (results / "extraction_log.jsonl").read_text().splitlines()
        if l.strip()
    ]

    failures: list[dict] = []
    checked = 0
    per_unit_digests: list[str] = []

    def fail(unit_id: str, step: str, check: str, detail: str = "") -> None:
        failures.append(
            {"unit_id": unit_id, "step": step, "check": check, "detail": detail}
        )

    with validator_schema_profile(PROFILE_SCHEMA_PATH):
        for u in units["units"]:
            checked += 1
            uid, step = u["unit_id"], u["step"]
            # 1. reconstruct (sha-pinned against ledger)
            try:
                source = reconstruct_unit(u, corpus)
            except UnitReconstructionError as exc:
                fail(uid, step, "reconstruction", str(exc))
                continue
            # 2. exactly one OK entry, disk bytes == logged sha
            ok_entries = [
                e for e in log_entries
                if e["unit_id"] == uid and e["status"] == "OK"
            ]
            if len(ok_entries) != 1:
                fail(uid, step, "log_ok_count", f"got {len(ok_entries)}")
            rec_path = results / record_filename(u)
            if not rec_path.exists():
                fail(uid, step, "record_missing", str(rec_path))
                continue
            raw = rec_path.read_bytes()
            rec_sha = sha256_bytes(raw)
            per_unit_digests.append(f"{uid}\t{rec_sha}")
            if ok_entries and ok_entries[0].get("record_sha256") != rec_sha:
                fail(uid, step, "record_sha_mismatch",
                     f"disk {rec_sha[:16]} vs log {str(ok_entries[0].get('record_sha256'))[:16]}")
            # 3. validator authority (schema+semantic atomic)
            cu = canonical_from_unit(u, source)
            try:
                validate_dm2.validate_semantic_extraction_json(cu, raw.decode())
            except Exception as exc:  # authority rejection
                fail(uid, step, "validator", str(exc)[:200])
                continue
            # 4. evidence spot-checks (independent of validator internals)
            rec = json.loads(raw)
            for p in rec["semantic_evidence"]["phrases"]:
                if p not in source:
                    fail(uid, step, "evidence_substring", p[:60])
            for n in rec["semantic_evidence"]["lines"]:
                if not (u["line_start"] <= n <= u["line_end"]):
                    fail(uid, step, "evidence_line_span", str(n))

    # 5. unresolved preservation
    for seg in units.get("unresolved_segments", []):
        lines = corpus[seg["file"]]
        live = "".join(lines[seg["line_start"] - 1: seg["line_end"]])
        if live != seg["text"]:
            failures.append({"unit_id": seg["segment_id"], "step": "-",
                             "check": "unresolved_text_mismatch"})
        if seg.get("reason_code") != "OUTSIDE_H1_BOUNDARY":
            failures.append({"unit_id": seg["segment_id"], "step": "-",
                             "check": "unresolved_reason_changed"})
    if not units.get("unresolved_segments"):
        failures.append({"unit_id": "-", "step": "-",
                         "check": "unresolved_segments_empty"})

    # 6. corpus untouched vs ledger freeze record
    for cf in units["corpus_files"]:
        live = sha256_bytes((Path(args.corpus) / cf["file"]).read_bytes())
        if live != cf["observed_sha256"]:
            failures.append({"unit_id": "-", "step": "-",
                             "check": "corpus_digest_drift",
                             "detail": cf["file"]})

    out = {
        "units_checked": checked,
        "n_units_ledger": units["n_units"],
        "records_ok": len(per_unit_digests),
        "failures": len(failures),
        "verdict": "PASS" if (not failures and checked == units["n_units"]
                              and len(per_unit_digests) == units["n_units"])
                   else "FAIL",
        "results_digest_p2": sha256_bytes(
            "\n".join(sorted(per_unit_digests)).encode()),
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))
    for f in failures[:40]:
        print("FAIL:", json.dumps(f, ensure_ascii=False))
    return 0 if out["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
