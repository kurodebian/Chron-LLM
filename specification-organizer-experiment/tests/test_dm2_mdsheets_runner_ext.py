"""
P2 EXT-layer regression tests (mdsheets-dm2 extension).

Three cases fixed by P2_EXT_TEST_SPEC_AUDIT and
P2_EXT_TEST_IMPLEMENTATION_PREFLIGHT:

  TC-1 EXT_RUNNER_INTEGRATION
       load_units() consumes the frozen ext artifact, run() executes the
       ext corpus pin (CORPUS-FREEZE-MDSHEETS-02 files via artifact
       corpus_files), ext gate anchors PASS under an explicit gate_steps
       pass, the results_digest echo is preserved, partial runs keep
       set_check NOT_ATTEMPTED, and the P0 default gate anchors never
       pass on an ext-only run.

  TC-2 SCHEMA_ACCEPT_REJECT_NAMESPACE
       loader accepts exactly UNITS_SCHEMA / UNITS_EXT_SCHEMA, rejects any
       other schema string, and the ext vs P0 results digests stay in
       disjoint namespaces.

  TC-3 VERIFIER_INPUT_CONTRACT_TEST
       tools/mdsheets_dm2_verify.main() over a synthetic 3-unit ext tree
       whose records and extraction log are generated DIRECTLY under
       tmp_path following the verifier input contract (verify :68-116:
       record file {step}.dm2.json; exactly one OK log entry per unit
       with record_sha256 equal to the sha256 of the record file bytes)
       — no run() involvement on the synthetic tree.
       PASS verdict + exit 0 + results_digest_p2 recomputed here from the
       documented formula, then two negatives: a non-empty
       unresolved_segments under the ext schema policy
       (ext_unresolved_segments_not_empty) and corpus byte drift
       (corpus_digest_drift).

Fixtures: frozen artifacts are READ-ONLY; every write lands under
pytest tmp_path. No full real results/ tree dependency and no full
digest-value pinning of real ext results: the artifact digest is pinned
only by its frozen prefix (b991f3f4, CORPUS-FREEZE-MDSHEETS-02), and the
results_digest_p2 for the synthetic tree is recomputed inside the test
rather than hardcoded. The real ext results digest (28f7f8be...) is
deliberately NOT pinned anywhere here.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from tools import mdsheets_dm2_verify
from tools.mdsheets_dm2_client import OpenAIChatConfig, sha256_text
from tools.mdsheets_dm2_runner import (
    EXPERIMENT_DIR,
    GATE_STEPS_DEFAULT,
    UNITS_EXT_SCHEMA,
    UNITS_SCHEMA,
    gate_block,
    load_units,
    record_filename,
    run,
)
from tests.test_dm2_mdsheets_runner import fake_llm

EXT_UNITS_PATH = EXPERIMENT_DIR / "ledger" / "units" / "mdsheets_units_ext.json"
P0_UNITS_PATH = EXPERIMENT_DIR / "ledger" / "units" / "mdsheets_units.json"

# Ext gate anchors (preflight: resolved from the artifact itself; the
# real ext run report carries gate keys step-125 / step-148 / step-218b).
EXT_GATE_STEPS = ("STEP-125", "STEP-148", "STEP-218b")

# Frozen ext artifact digest prefix (CORPUS-FREEZE-MDSHEETS-02,
# results_digest b991f3f4...). Prefix pin only: full value is re-read
# from the artifact at runtime and compared for equality.
EXT_ARTIFACT_DIGEST_PREFIX = "b991f3f4"

# Real ext RESULTS-tree digest prefix from P2_EXT_VERIFY evidence.
# Never pinned as an expected value; used only as a separation guard so a
# synthetic digest can never be mistaken for the real P2 results digest.
REAL_EXT_RESULTS_DIGEST_PREFIX = "28f7f8be"


def _parse_first_json_object(text: str) -> dict[str, Any]:
    start = text.index("{")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise ValueError(f"no JSON object in verifier output: {text[:200]!r}")


# --------------------------------------------------------------------------
# TC-1 EXT_RUNNER_INTEGRATION
# --------------------------------------------------------------------------


def test_ext_runner_gate_and_digest_echo(tmp_path):
    ext = load_units(EXT_UNITS_PATH)
    assert ext["schema"] == UNITS_EXT_SCHEMA
    assert ext["n_units"] == 99

    gate_unit_steps = [u["step"] for u in ext["units"] if u["step"] in EXT_GATE_STEPS]
    assert set(gate_unit_steps) == set(EXT_GATE_STEPS)

    report = run(
        units_path=EXT_UNITS_PATH,
        root=tmp_path,
        steps=list(gate_unit_steps),
        llm_call=fake_llm(),
        client_config=OpenAIChatConfig(),
        gate_steps=EXT_GATE_STEPS,
    )

    assert report["status"] == "COMPLETED"
    assert not report["unit_source"]["reconstruction_errors"]

    # results_digest echo: equality against the live artifact + frozen prefix
    echoed = report["input"]["units_results_digest"]
    assert echoed == ext["results_digest"]
    assert echoed.startswith(EXT_ARTIFACT_DIGEST_PREFIX)
    assert report["input"]["units_json"] == "ledger/units/mdsheets_units_ext.json"
    assert report["input"]["units_total"] == 99

    # ext anchors pass only because gate_steps was passed explicitly
    gate = report["gate"]
    for step in EXT_GATE_STEPS:
        entry = gate[step.lower()]
        assert entry["status"] == "PASS"
        assert entry["schema_pass"] is True
        assert entry["semantic_pass"] is True
    assert gate["all_required_pass"] is True

    # partial run: set-level check stays NOT_ATTEMPTED (3 records, 99 units)
    assert report["set_check"]["set_status"] == "NOT_ATTEMPTED (partial run)"
    assert report["set_check"]["records_present"] == 3
    assert report["set_check"]["units_total"] == 99

    # negative: P0 default anchors (STEP-1a / STEP-120) must never pass on
    # the ext-only output tree
    default_gate = gate_block(tmp_path, [], GATE_STEPS_DEFAULT)
    for step in GATE_STEPS_DEFAULT:
        assert default_gate[step.lower()]["status"] == "MISSING"
    assert default_gate["all_required_pass"] is False


# --------------------------------------------------------------------------
# TC-2 SCHEMA_ACCEPT_REJECT_NAMESPACE
# --------------------------------------------------------------------------


def test_units_schema_accept_reject_and_namespace(tmp_path):
    ext = load_units(EXT_UNITS_PATH)
    p0 = load_units(P0_UNITS_PATH)

    # acceptance: loader accepts both frozen namespaces verbatim
    assert ext["schema"] == UNITS_EXT_SCHEMA
    assert p0["schema"] == UNITS_SCHEMA
    assert UNITS_EXT_SCHEMA != UNITS_SCHEMA

    # namespace separation: ext and P0 artifact digests are disjoint
    # (different content sets must never collide)
    assert ext["results_digest"] != p0["results_digest"]
    assert ext["results_digest"].startswith(EXT_ARTIFACT_DIGEST_PREFIX)

    # rejection: a schema string outside UNITS_SCHEMAS must raise
    bad = json.loads(json.dumps(ext))
    bad["schema"] = "chron-llm/mdsheets-units-ext/2"
    bad_path = tmp_path / "bad_units.json"
    bad_path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="units artifact schema mismatch"):
        load_units(bad_path)

    # rejection: P0 artifact rewritten with the ext schema label also fails
    # the ext-only consumer guard used by the verifier policy path
    swapped = json.loads(json.dumps(p0))
    swapped["schema"] = "chron-llm/mdsheets-units/2"
    swapped_path = tmp_path / "swapped_units.json"
    swapped_path.write_text(json.dumps(swapped), encoding="utf-8")
    with pytest.raises(ValueError, match="units artifact schema mismatch"):
        load_units(swapped_path)


# --------------------------------------------------------------------------
# TC-3 VERIFIER_INPUT_CONTRACT_TEST
# --------------------------------------------------------------------------


def _write_dm2_records_and_log(
    results_dir: Path,
    units: list[dict[str, Any]],
    corpus: dict[str, list[str]],
) -> None:
    """Generate DM-2 records + extraction log DIRECTLY under tmp_path per
    the verifier input contract (tools/mdsheets_dm2_verify.py:68-116):
      - record file name = record_filename(u) = {step}.dm2.json
      - exactly one OK log entry per unit (unit_id, step, status=OK,
        record_sha256)
      - log record_sha256 == sha256 of the record file's on-disk bytes
    Record shape = the 8 root-required keys of the md_sheets profile
    schema (additionalProperties=false), with attribute/resolution
    vocabulary mirroring the real passing ext records (e.g.
    STEP-125.dm2.json)."""
    results_dir.mkdir(parents=True, exist_ok=True)
    log_lines: list[str] = []
    for u in units:
        lo, hi = u["line_start"], u["line_end"]
        source = "".join(corpus[u["file"]][lo - 1 : hi])
        body = [
            ln.strip()
            for ln in source.splitlines()
            if ln.strip() and not ln.startswith("#")
        ]
        record = {
            "unit_id": u["unit_id"],
            "line_start": lo,
            "line_end": hi,
            "source_text": source,
            "semantic_kind": "Requirement",
            "semantic_evidence": {
                "phrases": [source.splitlines()[0].strip(), body[0]],
                "lines": list(range(lo, hi + 1)),
            },
            "semantic_attributes": {
                "modality": "must",
                "structural_form": "other",
                "semantic_strength": "strong",
                "semantic_scope": "system-wide",
            },
            "resolution": {"status": "resolved", "reason": None},
        }
        rec_bytes = (
            json.dumps(record, ensure_ascii=False, indent=2) + "\n"
        ).encode("utf-8")
        (results_dir / record_filename(u)).write_bytes(rec_bytes)
        log_lines.append(
            json.dumps(
                {
                    "unit_id": u["unit_id"],
                    "step": u["step"],
                    "attempt": 1,
                    "status": "OK",
                    "record_sha256": hashlib.sha256(rec_bytes).hexdigest(),
                },
                ensure_ascii=False,
            )
        )
    (results_dir / "extraction_log.jsonl").write_text(
        "\n".join(log_lines) + "\n", encoding="utf-8"
    )


def _synthetic_ext_tree(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, Any]]:
    """Corpus (2 files, 3 H1 units) + minimal ext artifact + directly
    generated verifier-contract records/log (no run() on this path)."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    c1 = (
        "# UNIT ALPHA - synthetic\n"
        "\n"
        "alpha body phrase.\n"
        "\n"
        "# UNIT BETA - synthetic\n"
        "\n"
        "beta body phrase.\n"
    )
    c2 = "# UNIT GAMMA - synthetic\n\ngamma body phrase.\n"
    (corpus_dir / "c1.md").write_text(c1, encoding="utf-8")
    (corpus_dir / "c2.md").write_text(c2, encoding="utf-8")

    def unit(uid: str, step: str, fname: str, start: int, end: int, seq: int) -> dict[str, Any]:
        lines = (corpus_dir / fname).read_text(encoding="utf-8").splitlines(
            keepends=True
        )
        return {
            "unit_id": uid,
            "step": step,
            "seq": seq,
            "file": fname,
            "line_start": start,
            "line_end": end,
            "text_sha256": sha256_text("".join(lines[start - 1 : end])),
            "anchor_line_sha256": sha256_text(lines[start - 1]),
        }

    artifact: dict[str, Any] = {
        "schema": UNITS_EXT_SCHEMA,
        "n_units": 3,
        "units": [
            unit("mdsu9001", "STEP-901", "c1.md", 1, 3, 1),
            unit("mdsu9002", "STEP-902", "c1.md", 5, 7, 2),
            unit("mdsu9003", "STEP-903", "c2.md", 1, 3, 3),
        ],
        "corpus_files": [
            {
                "file": name,
                "observed_sha256": hashlib.sha256(
                    (corpus_dir / name).read_bytes()
                ).hexdigest(),
            }
            for name in ("c1.md", "c2.md")
        ],
        "unresolved_segments": [],
        "unresolved_h1_headers": [],
    }
    artifact_path = tmp_path / "units_ext_synth.json"
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

    root = tmp_path / "out"
    corpus = {
        name: (corpus_dir / name)
        .read_text(encoding="utf-8")
        .splitlines(keepends=True)
        for name in ("c1.md", "c2.md")
    }
    _write_dm2_records_and_log(root, artifact["units"], corpus)
    return artifact_path, root, corpus_dir, artifact


def _verify(
    monkeypatch,
    capsys,
    artifact_path: Path,
    results: Path,
    corpus_dir: Path,
) -> tuple[int, dict[str, Any], str]:
    monkeypatch.setattr(
        "sys.argv",
        [
            "mdsheets_dm2_verify",
            "--units",
            str(artifact_path),
            "--results",
            str(results),
            "--corpus",
            str(corpus_dir),
        ],
    )
    capsys.readouterr()
    rc = mdsheets_dm2_verify.main()
    out = capsys.readouterr().out
    return rc, _parse_first_json_object(out), out


def test_verifier_synthetic_ext_smoke(tmp_path, monkeypatch, capsys):
    artifact_path, root, corpus_dir, artifact = _synthetic_ext_tree(tmp_path)

    # positive: PASS verdict, exit 0
    rc, out_obj, _ = _verify(monkeypatch, capsys, artifact_path, root, corpus_dir)
    assert rc == 0
    assert out_obj["verdict"] == "PASS"
    assert out_obj["units_checked"] == 3
    assert out_obj["n_units_ledger"] == 3
    assert out_obj["records_ok"] == 3
    assert out_obj["failures"] == 0

    # results_digest_p2: independently recomputed here from the documented
    # verifier formula (sorted "unit_id<TAB>record-file-sha256" lines,
    # joined with \n, sha256 of utf-8 bytes) — never hardcoded.
    per_unit = []
    for u in artifact["units"]:
        rec_bytes = (root / record_filename(u)).read_bytes()
        per_unit.append(f"{u['unit_id']}\t{hashlib.sha256(rec_bytes).hexdigest()}")
    expected_digest = hashlib.sha256(
        "\n".join(sorted(per_unit)).encode("utf-8")
    ).hexdigest()
    assert out_obj["results_digest_p2"] == expected_digest
    # separation guard: the synthetic digest must never collide with the
    # real ext results-tree digest prefix (28f7f8be..., evidence-only pin)
    assert not expected_digest.startswith(REAL_EXT_RESULTS_DIGEST_PREFIX)

    # negative 1: ext schema policy — any unresolved segment FAILS
    polluted = json.loads(json.dumps(artifact))
    polluted["unresolved_segments"] = [
        {
            "segment_id": "mdseg9001",
            "file": "c1.md",
            "line_start": 4,
            "line_end": 4,
            "text": "\n",
            "reason_code": "OUTSIDE_H1_BOUNDARY",
        }
    ]
    artifact_path.write_text(json.dumps(polluted), encoding="utf-8")
    rc, out_obj, raw = _verify(monkeypatch, capsys, artifact_path, root, corpus_dir)
    assert rc == 1
    assert out_obj["verdict"] == "FAIL"
    assert out_obj["failures"] >= 1
    assert "ext_unresolved_segments_not_empty" in raw

    # negative 2: corpus byte drift vs frozen observed_sha256
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
    (corpus_dir / "c2.md").write_bytes(b"# tampered\n")
    rc, out_obj, raw = _verify(monkeypatch, capsys, artifact_path, root, corpus_dir)
    assert rc == 1
    assert out_obj["verdict"] == "FAIL"
    assert "corpus_digest_drift" in raw
