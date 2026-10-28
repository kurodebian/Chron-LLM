"""
p2-dm2 runner contract tests (offline; no live backend).

Covers the contract test dimensions:
  range, sha256, prompt, schema, semantic, resume, digest, provenance
plus the gate block. All validation runs through the authority
(tools/validate_dm2.py) with the mechanically-derived md_sheets
schema profile.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools import validate_dm2
from tools.dm2_extraction import build_dm2_prompt
from tools.mdsheets_dm2_client import sha256_text
from tools.mdsheets_dm2_runner import (
    DEFAULT_CORPUS_DIR,
    DEFAULT_UNITS_PATH,
    PROFILE_SCHEMA_PATH,
    UnitReconstructionError,
    canonical_from_unit,
    extract_one_unit,
    gate_block,
    load_corpus,
    load_units,
    reconstruct_unit,
    record_filename,
    resume_state,
    run,
)

ARTIFACT = load_units(DEFAULT_UNITS_PATH)
BY_STEP = {u["step"]: u for u in ARTIFACT["units"]}
CORPUS = load_corpus(DEFAULT_CORPUS_DIR)

REQUIRED_UNIT_FIELDS = {
    "unit_id",
    "step",
    "seq",
    "file",
    "line_start",
    "line_end",
    "text_sha256",
    "anchor_line_sha256",
}


def fake_llm(record_mutator=None, kind="Heading"):
    """Prompt -> (raw, payload, meta); record built from canonical in prompt."""

    def call(prompt: str):
        section = prompt.split("## Canonical unit", 1)[1]
        canonical = json.loads(section[section.index("{") : section.rindex("}") + 1])
        source = canonical["source_text"]
        phrase = source.splitlines()[0].lstrip("# ").strip()
        record = {
            "unit_id": canonical["unit_id"],
            "line_start": canonical["line_start"],
            "line_end": canonical["line_end"],
            "source_text": source,
            "semantic_kind": kind,
            "semantic_evidence": {
                "phrases": [phrase],
                "lines": [canonical["line_start"]],
            },
            "semantic_attributes": {
                "modality": "none",
                "structural_form": "heading",
                "semantic_strength": "descriptive",
                "semantic_scope": "local",
            },
            "resolution": {"status": "resolved", "reason": None},
        }
        if record_mutator:
            record_mutator(record)
        raw = json.dumps(record, ensure_ascii=False, indent=2)
        payload = {
            "model": "fake-model",
            "temperature": 0,
            "seed": 0,
            "messages": [{"role": "user", "content": prompt}],
        }
        meta = {
            "api": "openai",
            "model": "fake-model",
            "sampling_parameters": {"temperature": 0, "seed": 0},
            "grammar_mode": {"mode": "no_backend_support", "grammar_applied": False},
        }
        return raw, payload, meta

    return call


# ---------------------------------------------------------------- range


def test_unit_fields_present():
    for unit in ARTIFACT["units"]:
        assert REQUIRED_UNIT_FIELDS <= set(unit)


def test_reconstruct_line_range_slice():
    unit = BY_STEP["STEP-1a"]
    source = reconstruct_unit(unit, CORPUS)
    lines = CORPUS[unit["file"]]
    assert source == "".join(lines[unit["line_start"] - 1 : unit["line_end"]])
    assert source.startswith(lines[unit["line_start"] - 1])


def test_all_units_reconstruct_and_verify():
    # sha256 verification of every unit in the artifact
    for unit in ARTIFACT["units"]:
        reconstruct_unit(unit, CORPUS)


# ---------------------------------------------------------------- sha256


def test_tampered_text_sha256_rejected():
    unit = copy.deepcopy(BY_STEP["STEP-1a"])
    unit["text_sha256"] = "0" * 64
    with pytest.raises(UnitReconstructionError, match="text_sha256"):
        reconstruct_unit(unit, CORPUS)


def test_tampered_anchor_sha256_rejected():
    unit = copy.deepcopy(BY_STEP["STEP-1a"])
    unit["anchor_line_sha256"] = "0" * 64
    with pytest.raises(UnitReconstructionError, match="anchor_line_sha256"):
        reconstruct_unit(unit, CORPUS)


# ---------------------------------------------------------------- prompt


def test_prompt_sha256_in_log(tmp_path):
    unit = BY_STEP["STEP-1a"]
    source = reconstruct_unit(unit, CORPUS)
    seen = {}

    def probe(prompt):
        seen["prompt"] = prompt
        return fake_llm()(prompt)

    entry = extract_one_unit(
        unit, source, probe, root=tmp_path, attempt=1, max_attempts=2
    )
    assert entry["status"] == "OK"
    assert entry["prompt_sha256"] == sha256_text(seen["prompt"])
    assert unit["unit_id"] in seen["prompt"]
    section = seen["prompt"].split("## Canonical unit", 1)[1]
    parsed = json.loads(section[section.index("{") : section.rindex("}") + 1])
    assert parsed["source_text"] == source
    assert parsed["unit_id"] == unit["unit_id"]


def test_waived_protocol_in_prompt(tmp_path):
    # mdsheets runner uses the echo-waived protocol (2026-10-28 amendment).
    unit = BY_STEP["STEP-1a"]
    source = reconstruct_unit(unit, CORPUS)
    waived = build_dm2_prompt(canonical_from_unit(unit, source),
                              echo_source_text=False)
    default = build_dm2_prompt(canonical_from_unit(unit, source))
    assert "MUST NOT modify source_text." not in waived
    assert 'MUST be the empty string ""' in waived
    assert '  "source_text": "",' in waived
    assert "MUST NOT modify source_text." in default  # legacy byte-preserved
    assert default != waived


def test_waived_empty_source_text_ok_via_stamp(tmp_path):
    unit = BY_STEP["STEP-1a"]
    source = reconstruct_unit(unit, CORPUS)
    llm = fake_llm(record_mutator=lambda rec: rec.update({"source_text": ""}))
    entry = extract_one_unit(
        unit, source, llm, root=tmp_path, attempt=1, max_attempts=2
    )
    assert entry["status"] == "OK"
    saved = json.loads((tmp_path / f"{unit['step']}.dm2.json").read_text())
    assert saved["source_text"] == source  # canonical stamped back
    assert entry["validation"]["identity_stamped"] is True


# ---------------------------------------------------------------- schema / semantic


def test_profile_diff_is_unit_id_pattern_only():
    base = json.loads(
        (
            PROFILE_SCHEMA_PATH.parents[1]
            / "dm2-semantic-extraction-record-v2.schema.json"
        ).read_text(encoding="utf-8")
    )
    profile = json.loads(PROFILE_SCHEMA_PATH.read_text(encoding="utf-8"))
    for key in ("$id", "title", "description", "$comment"):
        base.pop(key, None)
        profile.pop(key, None)
    assert base["properties"]["unit_id"]["pattern"] != profile["properties"][
        "unit_id"
    ]["pattern"]
    base["properties"]["unit_id"]["pattern"] = profile["properties"]["unit_id"][
        "pattern"
    ]
    assert base == profile


def test_extra_top_level_field_rejected(tmp_path):
    unit = BY_STEP["STEP-1a"]
    source = reconstruct_unit(unit, CORPUS)

    def add_extra(record):
        record["causal_relation"] = {"to": "anything"}

    entry = extract_one_unit(
        unit,
        source,
        fake_llm(record_mutator=add_extra),
        root=tmp_path,
        attempt=1,
        max_attempts=1,
    )
    assert entry["status"] == "FAIL"
    assert "INVALID_DM2" in entry["error"]
    assert not (tmp_path / record_filename(unit)).exists()


def test_semantic_enum_rejected(tmp_path):
    unit = BY_STEP["STEP-120"]
    source = reconstruct_unit(unit, CORPUS)

    def bad_strength(record):
        record["semantic_attributes"]["semantic_strength"] = "definitely"

    entry = extract_one_unit(
        unit,
        source,
        fake_llm(record_mutator=bad_strength),
        root=tmp_path,
        attempt=1,
        max_attempts=1,
    )
    assert entry["status"] == "FAIL"
    assert "INVALID_DM2" in entry["error"]


def test_non_json_output_rejected(tmp_path):
    unit = BY_STEP["STEP-120"]
    source = reconstruct_unit(unit, CORPUS)

    def garbage(prompt):
        return "sorry, here is a table", {}, {"api": "openai"}

    entry = extract_one_unit(
        unit, source, garbage, root=tmp_path, attempt=1, max_attempts=1
    )
    assert entry["status"] == "FAIL"
    assert "INVALID_DM2" in entry["error"]


# ---------------------------------------------------------------- provenance


def test_request_and_raw_provenance_exact(tmp_path):
    unit = BY_STEP["STEP-1a"]
    source = reconstruct_unit(unit, CORPUS)
    llm = fake_llm()
    entry = extract_one_unit(
        unit, source, llm, root=tmp_path, attempt=1, max_attempts=2
    )
    request_file = Path(entry["request_file"])
    raw_file = Path(entry["raw_output_file"])
    assert request_file.is_file() and raw_file.is_file()
    request = json.loads(request_file.read_text(encoding="utf-8"))
    assert request["temperature"] == 0 and request["seed"] == 0
    raw_text = raw_file.read_text(encoding="utf-8")
    assert entry["raw_output_sha256"] == sha256_text(raw_text)
    record = json.loads((tmp_path / record_filename(unit)).read_text("utf-8"))
    assert record == json.loads(raw_text)  # no repair: record == raw parsed
    # no secret material in artifacts
    for blob in (request_file.read_text(), raw_text):
        assert "authorization" not in blob.lower()


# ---------------------------------------------------------------- resume + digest + gate


def test_resume_skip_and_gate_and_digest(tmp_path):
    steps = ["STEP-1a", "STEP-120"]
    calls = {"n": 0}

    def counting(prompt):
        calls["n"] += 1
        return fake_llm()(prompt)

    report1 = run(
        root=tmp_path, steps=steps, llm_call=counting, max_attempts=1
    )
    assert calls["n"] == 2
    assert report1["status"] == "COMPLETED"
    assert report1["gate"]["step-1a"]["status"] == "PASS"
    assert report1["gate"]["step-120"]["status"] == "PASS"
    assert report1["gate"]["all_required_pass"] is True
    assert report1["gate"]["step-1a"]["schema_pass"] is True
    assert report1["gate"]["step-120"]["semantic_pass"] is True

    log_path = tmp_path / "extraction_log.jsonl"
    digest1 = report1["provenance"]["log_sha256"]
    assert digest1 == sha256_text(log_path.read_text(encoding="utf-8"))

    report2 = run(root=tmp_path, steps=steps, llm_call=counting, max_attempts=1)
    assert calls["n"] == 2  # resume: no new model calls
    assert set(report2["run"]["skipped_resume"]) == {
        BY_STEP[s]["unit_id"] for s in steps
    }
    assert report2["provenance"]["log_sha256"] == digest1
    assert report2["gate"]["all_required_pass"] is True


def test_gate_never_passes_without_validator_ok(tmp_path):
    gate = gate_block(tmp_path, [])
    assert gate["step-1a"]["status"] == "MISSING"
    assert gate["all_required_pass"] is False

    # record file copied in WITHOUT a validator-OK log entry: must not pass
    unit = BY_STEP["STEP-1a"]
    (tmp_path / record_filename(unit)).write_text("{}", encoding="utf-8")
    gate = gate_block(tmp_path, [])
    assert gate["step-1a"]["status"] == "FAIL"
    assert gate["all_required_pass"] is False


def test_fail_retry_then_ok_counts_one_record(tmp_path):
    unit = BY_STEP["STEP-120"]
    source = reconstruct_unit(unit, CORPUS)
    state = {"n": 0}

    def first_bad(prompt):
        state["n"] += 1
        if state["n"] == 1:
            return "not json at all", {"model": "fake"}, {"api": "openai"}
        return fake_llm()(prompt)

    entry1 = extract_one_unit(
        unit, source, first_bad, root=tmp_path, attempt=1, max_attempts=2
    )
    assert entry1["status"] == "FAIL"
    entry2 = extract_one_unit(
        unit, source, first_bad, root=tmp_path, attempt=2, max_attempts=2
    )
    assert entry2["status"] == "OK"
    log = (tmp_path / "extraction_log.jsonl").read_text("utf-8").splitlines()
    assert len(log) == 2  # one line per attempt
    assert (tmp_path / record_filename(unit)).is_file()
    assert len(list(tmp_path.glob("*.dm2.json"))) == 1  # fail+ok => one record


def test_one_unit_one_record_identity(tmp_path):
    steps = ["STEP-1a", "STEP-120"]
    run(root=tmp_path, steps=steps, llm_call=fake_llm(kind="Heading"), max_attempts=1)
    log = [
        json.loads(l)
        for l in (tmp_path / "extraction_log.jsonl").read_text("utf-8").splitlines()
    ]
    ok_units = [e["unit_id"] for e in log if e["status"] == "OK"]
    assert len(ok_units) == len(set(ok_units))
    records = sorted(tmp_path.glob("*.dm2.json"))
    assert len(records) == 2
    for rec_path in records:
        rec = json.loads(rec_path.read_text("utf-8"))
        unit = BY_STEP[rec_path.name.removesuffix(".dm2.json")]
        assert rec["unit_id"] == unit["unit_id"]
        assert rec["line_start"] == unit["line_start"]
        assert rec["line_end"] == unit["line_end"]


def test_identity_stamp_recovers_broken_echo(tmp_path):
    """Adjudicated policy: mangled identity echo is deterministically
    replaced with canonical values; model raw bytes stay verbatim."""
    unit = BY_STEP["STEP-1a"]
    source = reconstruct_unit(unit, CORPUS)

    def mangle(rec):
        rec["source_text"] = rec["source_text"][:-1]
        rec["line_end"] = 99

    entry = extract_one_unit(
        unit,
        source,
        fake_llm(record_mutator=mangle),
        root=tmp_path,
        attempt=1,
        max_attempts=1,
    )
    assert entry["status"] == "OK"
    assert entry["validation"]["identity_stamped"] is True
    assert entry["validation"]["model_identity_sha256"]
    saved = json.loads((tmp_path / record_filename(unit)).read_text("utf-8"))
    assert saved["source_text"] == source
    assert saved["line_end"] == unit["line_end"]
    raw = (tmp_path / "work" / "raw" / f"{unit['unit_id']}.attempt-1.raw.txt").read_text("utf-8")
    assert '"line_end": 99' in raw  # raw preserved verbatim, not repaired
    assert entry["raw_output_sha256"] == sha256_text(raw)


def test_identity_stamp_does_not_rescue_extra_field(tmp_path):
    unit = BY_STEP["STEP-1a"]
    source = reconstruct_unit(unit, CORPUS)
    entry = extract_one_unit(
        unit,
        source,
        fake_llm(record_mutator=lambda r: r.update({"mood": "declarative"})),
        root=tmp_path,
        attempt=1,
        max_attempts=1,
    )
    assert entry["status"] == "FAIL"


# ------------------------------------------------- transport resilience


def test_timeout_env_override(monkeypatch):
    """MDSHEETS_DM2_TIMEOUT is a transport-only knob (read timeout)."""
    from tools.mdsheets_dm2_client import DEFAULT_TIMEOUT, OpenAIChatConfig

    monkeypatch.delenv("MDSHEETS_DM2_TIMEOUT", raising=False)
    assert OpenAIChatConfig.from_env().timeout == DEFAULT_TIMEOUT
    monkeypatch.setenv("MDSHEETS_DM2_TIMEOUT", "1800")
    assert OpenAIChatConfig.from_env().timeout == 1800.0
    monkeypatch.setenv("MDSHEETS_DM2_TIMEOUT", "")
    assert OpenAIChatConfig.from_env().timeout == DEFAULT_TIMEOUT


def test_transport_error_logged_and_run_continues(tmp_path):
    """An OpenAIBackendError mid-run: FAIL line in log, next unit still
    attempted, and the FAILed unit is re-planned by resume (never skipped).
    """
    from tools.mdsheets_dm2_client import OpenAIBackendError

    steps = ["STEP-1a", "STEP-1b"]
    ok_call = fake_llm()
    state = {"calls": 0}

    def flaky(prompt: str):
        state["calls"] += 1
        if state["calls"] == 1:
            raise OpenAIBackendError("simulated read timeout")
        return ok_call(prompt)

    report = run(root=tmp_path, steps=steps, llm_call=flaky, max_attempts=1)
    entries = [
        json.loads(line)
        for line in (tmp_path / "extraction_log.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(entries) == 2  # exactly one log entry per attempt
    assert entries[0]["status"] == "FAIL"
    assert entries[0]["error"].startswith("transport_error:")
    assert entries[0]["attempts_exhausted"] is True
    assert entries[1]["status"] == "OK"
    assert report["run"]["fail_this_run"] == ["mdsu0001"]
    assert report["run"]["ok_this_run"] == ["mdsu0002"]

    # resume: FAILed unit re-planned, OK unit skipped
    report2 = run(
        root=tmp_path, steps=steps, llm_call=fake_llm(), max_attempts=1
    )
    assert report2["run"]["skipped_resume"] == ["mdsu0002"]
    assert report2["run"]["ok_this_run"] == ["mdsu0001"]
