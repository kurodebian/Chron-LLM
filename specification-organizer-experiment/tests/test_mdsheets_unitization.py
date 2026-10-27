#!/usr/bin/env python3
# tests/test_mdsheets_unitization.py
"""
P1 — 章レベル単位画定の決定論的検証テスト (md_sheets chapter segmentation).

Contract under test:
  - 127 chapters from ledger/mdsheets_chapter_ledger.json are sliced
    deterministically at H1 boundaries (no LLM boundary decisions).
  - Per corpus file, unit spans + unresolved segments partition every
    line exactly once: byte-exact concatenation reconstructs the
    frozen source (digest must equal the P0 freeze manifest digests).
  - Content outside H1 boundaries is preserved as UNRESOLVED segments
    (not silently dropped, not guessed).
  - Range-style step references in H1 anchors (e.g. "STEP-31–96") are
    preserved as unresolved headers, never silently attributed.

Disciplines: MISSING_EVIDENCE != PASS / VERIFICATION_IS_NOT_AUTHORIZATION.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.mdsheets_unitize import (
    ARTIFACT_PATH,
    CORPUS_FILES,
    LEDGER_PATH,
    P0_MANIFEST_PATH,
    build_units_artifact,
    canonical_digest,
    sha256_text,
)

@pytest.fixture(scope="module")
def artifact():
    return build_units_artifact()


@pytest.fixture(scope="module")
def ledger():
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def p0_manifest():
    return json.loads(P0_MANIFEST_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def corpus_lines():
    """{filename: lines with keepends} from the frozen corpus."""
    out = {}
    for name in CORPUS_FILES:
        text = (Path(__file__).resolve().parents[2] / "md_sheets" / name).read_text(
            encoding="utf-8"
        )
        out[name] = text.splitlines(keepends=True)
    return out


def _spans(artifact):
    return artifact["units"] + artifact["unresolved_segments"]


# ==========================================================
# Inventory
# ==========================================================

def test_unit_count_matches_ledger(artifact, ledger):
    assert artifact["n_units"] == 127
    assert artifact["n_units"] == len(ledger["chapters"]) == len(artifact["units"])


def test_unit_ids_and_seq_unique_and_contiguous(artifact):
    ids = [u["unit_id"] for u in artifact["units"]]
    seqs = [u["seq"] for u in artifact["units"]]
    assert len(set(ids)) == len(ids)
    assert seqs == list(range(1, 128))


def test_step_ids_unique(artifact):
    steps = [u["step"] for u in artifact["units"]]
    assert len(set(steps)) == 127


def test_unit_spans_match_ledger(artifact, ledger):
    by_seq = {c["seq"]: c for c in ledger["chapters"]}
    for u in artifact["units"]:
        c = by_seq[u["seq"]]
        assert u["file"] == c["file"]
        assert u["line_start"] == c["line_start"]
        assert u["line_end"] == c["line_end"]
        assert u["step"] == c["step"]


# ==========================================================
# H1 boundary determinism
# ==========================================================

def test_every_unit_starts_on_h1_anchor(artifact, corpus_lines):
    for u in artifact["units"]:
        line = corpus_lines[u["file"]][u["line_start"] - 1]
        assert line.startswith("# "), u["unit_id"]


def test_anchor_step_number_matches_unit_step(artifact, corpus_lines):
    from tools.mdsheets_unitize import ANCHOR_STEP_RE
    import re

    for u in artifact["units"]:
        line = corpus_lines[u["file"]][u["line_start"] - 1]
        m = ANCHOR_STEP_RE.match(line)
        assert m, (u["unit_id"], line[:60])
        assert int(m.group(1)) == int(re.match(r"STEP-(\d+)", u["step"]).group(1))


def test_unit_text_sha256_matches_source_slice(artifact, corpus_lines):
    for u in artifact["units"]:
        sl = corpus_lines[u["file"]][u["line_start"] - 1 : u["line_end"]]
        assert u["text_sha256"] == sha256_text("".join(sl)), u["unit_id"]


def test_n_chars_uses_ledger_convention(artifact, corpus_lines, ledger):
    by_seq = {c["seq"]: c for c in ledger["chapters"]}
    for u in artifact["units"]:
        sl = corpus_lines[u["file"]][u["line_start"] - 1 : u["line_end"]]
        # ledger convention: splitlines() view (terminators stripped) joined
        # by "\n" — CRLF-safe.
        joined = "\n".join("".join(sl).splitlines())
        assert u["n_chars"] == len(joined) == by_seq[u["seq"]]["n_chars"]
        assert u["n_lines"] == u["line_end"] - u["line_start"] + 1


# ==========================================================
# Byte-exact reconstruction (no gaps, no overlaps)
# ==========================================================

def test_spans_partition_each_file_exactly(artifact, corpus_lines):
    for name in CORPUS_FILES:
        spans = sorted(
            ((s["line_start"], s["line_end"]) for s in _spans(artifact) if s["file"] == name)
        )
        n = len(corpus_lines[name])
        pos = 1
        for start, end in spans:
            assert start == pos, (name, start, pos)
            assert end >= start
            pos = end + 1
        assert pos == n + 1, (name, pos, n + 1)


def test_byte_exact_concatenation_reconstructs_corpus(artifact, corpus_lines):
    for name in CORPUS_FILES:
        parts = sorted(
            (s for s in _spans(artifact) if s["file"] == name),
            key=lambda s: s["line_start"],
        )
        rebuilt = "".join(
            "".join(corpus_lines[name][s["line_start"] - 1 : s["line_end"]])
            for s in parts
        )
        assert sha256_text(rebuilt) == sha256_text("".join(corpus_lines[name]))


def test_reconstruction_digests_match_p0_freeze(artifact, p0_manifest):
    expected = {f["path"].split("/")[-1]: f["sha256"] for f in p0_manifest["files"]}
    observed = {f["file"]: f["observed_sha256"] for f in artifact["corpus_files"]}
    for name in CORPUS_FILES:
        assert observed[name] == expected[name], name


# ==========================================================
# UNRESOLVED preservation
# ==========================================================

def test_unresolved_segments_preserved_with_evidence(artifact, corpus_lines):
    segs = artifact["unresolved_segments"]
    assert len(segs) == 1
    seg = segs[0]
    assert seg["file"] == "1-74.md"
    assert seg["line_start"] == 1
    assert seg["line_end"] == 33
    assert seg["reason_code"] == "OUTSIDE_H1_BOUNDARY"
    src = "".join(corpus_lines[seg["file"]][seg["line_start"] - 1 : seg["line_end"]])
    assert seg["text"] == src
    assert seg["text_sha256"] == sha256_text(src)


def test_no_range_style_h1_headers_silently_attributed(artifact, corpus_lines):
    # Independent re-scan: every H1 line in the corpus must be either a
    # unit anchor or flagged. Range-style step refs in H1 text (e.g.
    # "STEP-31–96") must never be attributed to a single chapter.
    from tools.mdsheets_unitize import RANGE_STEP_REF_RE

    anchors = {
        (u["file"], u["line_start"]) for u in artifact["units"]
    }
    flagged = {
        (h["file"], h["line_start"]) for h in artifact["unresolved_h1_headers"]
    }
    for name in CORPUS_FILES:
        for i, line in enumerate(corpus_lines[name], start=1):
            if not line.startswith("# "):
                continue
            assert (name, i) in anchors or (name, i) in flagged, (name, i)
            if RANGE_STEP_REF_RE.search(line):
                assert (name, i) in flagged, (name, i, line[:60])
    # chapters_index.md recorded 0 range-style chapter headings.
    assert artifact["unresolved_h1_headers"] == []


# ==========================================================
# Checks, digest, determinism
# ==========================================================

def test_all_checks_true(artifact):
    assert artifact["checks"], "no checks computed"
    assert all(artifact["checks"].values()), artifact["checks"]


def test_results_digest_binds_content(artifact):
    core = {k: v for k, v in artifact.items() if k not in ("results_digest", "generated_utc")}
    assert artifact["results_digest"] == canonical_digest(core)


def test_build_is_deterministic():
    a = build_units_artifact()
    b = build_units_artifact()
    assert a["results_digest"] == b["results_digest"]


def test_digest_invariant_under_pythonhashseed():
    digests = set()
    for seed in ("0", "7", "12345"):
        proc = subprocess.run(
            [sys.executable, "tools/mdsheets_unitize.py", "--print-digest"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            env={"PYTHONHASHSEED": seed, "PATH": "/usr/bin:/bin"},
        )
        assert proc.returncode == 0, proc.stderr
        digests.add(proc.stdout.strip())
    assert len(digests) == 1, digests


def test_written_artifact_matches_in_memory_build(artifact):
    proc = subprocess.run(
        [sys.executable, "tools/mdsheets_unitize.py"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    written = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert written["results_digest"] == artifact["results_digest"]
