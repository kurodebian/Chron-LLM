#!/usr/bin/env python3
# tests/test_mdsheets_unitization_ext.py
"""
P1-EXT — 未pin 4ファイル (125-149/150-174/175-199/200-218, 99章) の
決定論的単位画定 + freeze 拡張 (CORPUS-FREEZE-MDSHEETS-02) の検証テスト。

Contract under test:
  - boundaries derived deterministically from the RATIFIED adopted index record
    (md_sheets/chapters_index.md master chapter map; branch-letter step ids for
    duplicate step numbers; no LLM boundary decisions).
  - chapter spans partition each extension file exactly; byte-exact
    concatenation reconstructs each file (digests equal the extension manifest).
  - seqs continue the P1 numbering (128..226); unit ids and step ids unique.
  - every '# ' H1 line is an anchor or flagged; range-style step refs never
    attributed; content outside anchors preserved as UNRESOLVED segments.
  - the P0 127-unit freeze layer stays byte-identical (records unchanged).

Disciplines: MISSING_EVIDENCE != PASS / VERIFICATION_IS_NOT_AUTHORIZATION.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.mdsheets_unitize import (
    P0_MANIFEST_PATH,
    canonical_digest,
    sha256_text,
)
from tools.mdsheets_unitize_ext import (
    CORPUS_FILES,
    INDEX_PATH,
    LEDGER_EXT_PATH,
    MANIFEST_EXT_PATH,
    SEQ_BASE,
    UNITS_EXT_PATH,
    build_ext_ledger,
    build_units_ext_artifact,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def ledger_ext():
    return build_ext_ledger()


@pytest.fixture(scope="module")
def artifact(ledger_ext):
    return build_units_ext_artifact(ledger_ext)


@pytest.fixture(scope="module")
def manifest():
    return json.loads(MANIFEST_EXT_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def corpus_lines():
    out = {}
    for name in CORPUS_FILES:
        text = (REPO_ROOT / "md_sheets" / name).read_text(encoding="utf-8")
        out[name] = text.splitlines(keepends=True)
    return out


def _spans(artifact):
    return artifact["units"] + artifact["unresolved_segments"]


# ==========================================================
# Inventory
# ==========================================================

def test_unit_count_is_99(artifact, ledger_ext):
    assert artifact["n_units"] == 99
    assert artifact["n_units"] == len(ledger_ext["chapters"]) == len(artifact["units"])


def test_unit_ids_and_seq_unique_contiguous_after_p1(artifact):
    ids = [u["unit_id"] for u in artifact["units"]]
    seqs = [u["seq"] for u in artifact["units"]]
    assert len(set(ids)) == 99
    assert seqs == list(range(SEQ_BASE, SEQ_BASE + 99))
    assert ids == ["mdsu%04d" % s for s in seqs]


def test_step_ids_unique_with_branch_letters(artifact):
    steps = [u["step"] for u in artifact["units"]]
    assert len(set(steps)) == 99
    branches = {s for s in steps if s[-1].isalpha()}
    assert branches == {"STEP-154a", "STEP-154b", "STEP-155a", "STEP-155b",
                        "STEP-161a", "STEP-161b", "STEP-162a", "STEP-162b",
                        "STEP-218a", "STEP-218b"}


def test_unit_spans_match_ext_ledger(artifact, ledger_ext):
    by_seq = {c["seq"]: c for c in ledger_ext["chapters"]}
    for u in artifact["units"]:
        c = by_seq[u["seq"]]
        assert u["file"] == c["file"]
        assert u["line_start"] == c["line_start"]
        assert u["line_end"] == c["line_end"]
        assert u["step"] == c["step"]
        assert u["n_lines"] == c["n_lines"] == u["line_end"] - u["line_start"] + 1


# ==========================================================
# H1 boundary determinism (index anchors resolve on live bytes)
# ==========================================================

def test_every_unit_starts_on_h1_anchor(artifact, corpus_lines):
    for u in artifact["units"]:
        assert corpus_lines[u["file"]][u["line_start"] - 1].startswith("# "), u["unit_id"]


def test_anchor_step_number_matches_unit_step(artifact, corpus_lines):
    import re
    from tools.mdsheets_unitize import ANCHOR_STEP_RE

    for u in artifact["units"]:
        line = corpus_lines[u["file"]][u["line_start"] - 1]
        m = ANCHOR_STEP_RE.match(line)
        assert m, (u["unit_id"], line[:60])
        assert int(m.group(1)) == int(re.match(r"STEP-(\d+)", u["step"]).group(1))


def test_unit_text_sha256_matches_source_slice(artifact, corpus_lines):
    for u in artifact["units"]:
        sl = corpus_lines[u["file"]][u["line_start"] - 1 : u["line_end"]]
        assert u["text_sha256"] == sha256_text("".join(sl)), u["unit_id"]


def test_anchor_digests_reproduce_from_live_bytes(artifact, corpus_lines):
    # ADR-008 (RATIFIED_HUMAN): LF-only convention; anchor line digest as read.
    for u in artifact["units"]:
        line = corpus_lines[u["file"]][u["line_start"] - 1]
        assert u["anchor_line_sha256"] == sha256_text(line), u["unit_id"]
        assert not line.endswith("\r\n"), u["unit_id"]


def test_files_start_on_anchor_no_preamble(artifact, corpus_lines):
    # Extension files begin at line 1 with an H1 anchor: no preamble segments.
    for name in CORPUS_FILES:
        assert corpus_lines[name][0].startswith("# "), name
    assert artifact["unresolved_segments"] == []


# ==========================================================
# Byte-exact reconstruction (no gaps, no overlaps)
# ==========================================================

def test_spans_partition_each_file_exactly(artifact, corpus_lines):
    for name in CORPUS_FILES:
        spans = sorted(
            ((s["line_start"], s["line_end"]) for s in _spans(artifact) if s["file"] == name)
        )
        pos = 1
        for start, end in spans:
            assert start == pos, (name, start, pos)
            assert end >= start
            pos = end + 1
        assert pos == len(corpus_lines[name]) + 1, (name, pos)


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


def test_corpus_digests_match_extension_freeze(artifact, manifest):
    expected = {f["path"].split("/")[-1]: f["sha256"] for f in manifest["files"]
                if f["path"].startswith("md_sheets/") and f["path"].endswith(".md")}
    observed = {f["file"]: f["observed_sha256"] for f in artifact["corpus_files"]}
    for name in CORPUS_FILES:
        assert observed[name] == expected[name], name


# ==========================================================
# Manifest bindings
# ==========================================================

def test_manifest_pins_index_and_artifacts(manifest):
    by_path = {f["path"]: f["sha256"] for f in manifest["files"]}
    idx_text = INDEX_PATH.read_text(encoding="utf-8")
    assert by_path["md_sheets/chapters_index.md"] == sha256_text(idx_text)
    assert by_path["specification-organizer-experiment/ledger/mdsheets_chapter_ledger_ext.json"] == \
        sha256_text(LEDGER_EXT_PATH.read_text(encoding="utf-8"))
    assert by_path["specification-organizer-experiment/ledger/units/mdsheets_units_ext.json"] == \
        sha256_text(UNITS_EXT_PATH.read_text(encoding="utf-8"))


def test_source_index_digest_is_live(manifest, artifact):
    idx_text = INDEX_PATH.read_text(encoding="utf-8")
    assert artifact["source"]["index_sha256"] == sha256_text(idx_text)


def test_p0_freeze_layer_unchanged(manifest):
    # CORPUS-FREEZE-MDSHEETS-01 (127-unit freeze) must remain byte-identical.
    p0 = json.loads(P0_MANIFEST_PATH.read_text(encoding="utf-8"))
    for f in p0["files"]:
        name = f["path"].split("/")[-1]
        if name in ("1-74.md", "75-99.md", "100-124.md"):
            live = (REPO_ROOT / "md_sheets" / name).read_text(encoding="utf-8")
            assert sha256_text(live) == f["sha256"], name
    assert manifest["manifest_id"] == "CORPUS-FREEZE-MDSHEETS-02"


# ==========================================================
# UNRESOLVED preservation
# ==========================================================

def test_no_h1_line_unaccounted_or_silently_attributed(artifact, corpus_lines):
    from tools.mdsheets_unitize import RANGE_STEP_REF_RE

    anchors = {(u["file"], u["line_start"]) for u in artifact["units"]}
    flagged = {(h["file"], h["line_start"]) for h in artifact["unresolved_h1_headers"]}
    for name in CORPUS_FILES:
        for i, line in enumerate(corpus_lines[name], start=1):
            if not line.startswith("# "):
                continue
            assert (name, i) in anchors or (name, i) in flagged, (name, i)
            if RANGE_STEP_REF_RE.search(line):
                assert (name, i) in flagged, (name, i, line[:60])
    assert artifact["unresolved_h1_headers"] == []


# ==========================================================
# Checks, digest, determinism
# ==========================================================

def test_all_checks_true(artifact):
    assert artifact["checks"]
    assert all(artifact["checks"].values()), artifact["checks"]


def test_results_digest_binds_content(artifact):
    core = {k: v for k, v in artifact.items() if k not in ("results_digest", "generated_utc")}
    assert artifact["results_digest"] == canonical_digest(core)


def test_build_is_deterministic():
    a = build_units_ext_artifact(build_ext_ledger())
    b = build_units_ext_artifact(build_ext_ledger())
    assert a["results_digest"] == b["results_digest"]


def test_digest_invariant_under_pythonhashseed():
    digests = set()
    for seed in ("0", "7", "12345"):
        proc = subprocess.run(
            [sys.executable, "tools/mdsheets_unitize_ext.py", "--print-digest"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            env={"PYTHONHASHSEED": seed, "PATH": "/usr/bin:/bin"},
        )
        assert proc.returncode == 0, proc.stderr
        digests.add(proc.stdout.strip())
    assert len(digests) == 1, digests


def test_written_artifacts_match_in_memory_build(artifact):
    written = json.loads(UNITS_EXT_PATH.read_text(encoding="utf-8"))
    assert written["results_digest"] == artifact["results_digest"]
    ledger_written = json.loads(LEDGER_EXT_PATH.read_text(encoding="utf-8"))
    assert ledger_written["chapters"] == build_ext_ledger()["chapters"]
