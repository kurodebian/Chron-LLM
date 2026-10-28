#!/usr/bin/env python3
# tools/mdsheets_dm2_runner.py
"""
p2-dm2: DM-2 semantic extraction over the md_sheets P1 units artifact.

Contract implemented by this runner:

  input     ledger/units/mdsheets_units.json (units-json)
  output    results/mdsheets-dm2/
              <step>.dm2.json      one DM-2 record per unit (1unit=1record)
              extraction_log.jsonl one append-only line per attempt (resume)
              report.json          run report incl. gate block + digests
              work/request/...     exact request payload per attempt (prov)
              work/raw/...         exact raw model output per attempt (prov)
  client    OpenAI-compatible endpoint, temperature=0, seed=0, grammar auto
            (tools/mdsheets_dm2_client.py)
  unit      source text is RECONSTRUCTED from corpus lines by
            [line_start, line_end] and verified against the units
            artifact's declared text_sha256 / anchor_line_sha256 before
            any model call (unit source reconstruct-from-lines,
            verify sha256)
  validate  authority: tools/validate_dm2.py
            validate_semantic_extraction_json runs the V1 schema,
            phrase-in-source, quote-in-source, line-in-range,
            no-extra-fields and identity checks. No repair.
            For the md_sheets units a mechanical schema PROFILE
            (schemas/dm2-semantic-extraction-record-v2.mdsheets.schema.json)
            is used whose only normative diff from the base v2 schema is
            unit_id.pattern (^mdsu[0-9]{4}$); the validator code itself
            is untouched.
  resume    units with a validator-OK log entry and an existing record
            file are not re-processed
  gate      step-1a + step-120 record presence with validator-OK
            provenance (schema-pass / semantic-pass) in report.json

Disciplines honored:
  ARTIFACT_EXISTENCE != NORMATIVE_ADOPTION
  VERIFICATION_IS_NOT_AUTHORIZATION
  MISSING_EVIDENCE != PASS   (gate of an unattempted/failed unit is
  FAIL/MISSING, never optimistic)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_DIR.parent
sys.path.insert(0, str(EXPERIMENT_DIR))

from tools import validate_dm2  # DM-2 validation authority (untouched)
from tools.dm2_extraction import build_dm2_prompt  # shared DM-2 V2 prompt
from tools.mdsheets_dm2_client import (
    ChatObservation,
    OpenAIChatConfig,
    OpenAIBackendError,
    call_openai_chat,
    resolve_model,
    sha256_text,
)

DEFAULT_UNITS_PATH = EXPERIMENT_DIR / "ledger" / "units" / "mdsheets_units.json"
DEFAULT_OUTPUT_ROOT = EXPERIMENT_DIR / "results" / "mdsheets-dm2"
DEFAULT_CORPUS_DIR = REPO_ROOT / "md_sheets"
PROFILE_SCHEMA_PATH = (
    EXPERIMENT_DIR
    / "schemas"
    / "dm2-semantic-extraction-record-v2.mdsheets.schema.json"
)
UNITS_SCHEMA = "chron-llm/mdsheets-units/1"

LLMCall = Callable[[str], "tuple[str, dict[str, Any], dict[str, Any]]"]
# LLMCall contract: prompt -> (raw_output, request_payload, metadata)


class UnitReconstructionError(RuntimeError):
    pass


def utc_now() -> str:
    return (
        datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        )
    )


@contextmanager
def validator_schema_profile(schema_path: Path) -> Iterator[None]:
    """
    Point the DM-2 validator at a schema profile for one call region.

    The validator MODULE and its logic are untouched; only its
    SCHEMA_PATH module constant is temporarily rebound and always
    restored. The profile swap is explicit, logged by the caller, and
    covered by tests.
    """
    original = validate_dm2.SCHEMA_PATH
    validate_dm2.SCHEMA_PATH = schema_path
    try:
        yield
    finally:
        validate_dm2.SCHEMA_PATH = original


def load_units(path: Path) -> dict[str, Any]:
    artifact = json.loads(path.read_text(encoding="utf-8"))
    if artifact.get("schema") != UNITS_SCHEMA:
        raise ValueError(
            f"units artifact schema mismatch: expected {UNITS_SCHEMA!r}, "
            f"got {artifact.get('schema')!r}"
        )
    return artifact


def load_corpus(corpus_dir: Path) -> dict[str, list[str]]:
    """{filename: lines with keepends}, P1 convention (CRLF-safe)."""
    return {
        name: (corpus_dir / name)
        .read_text(encoding="utf-8")
        .splitlines(keepends=True)
        for name in ("1-74.md", "75-99.md", "100-124.md")
    }


def reconstruct_unit(unit: dict[str, Any], corpus: dict[str, list[str]]) -> str:
    """
    Reconstruct the unit source text from corpus [line_start, line_end]
    and verify against declared digests BEFORE any model call.
    """
    try:
        lines = corpus[unit["file"]]
    except KeyError as exc:
        raise UnitReconstructionError(
            f"corpus file {unit['file']!r} not available for {unit['unit_id']}"
        ) from exc
    start, end = unit["line_start"], unit["line_end"]
    if not (1 <= start <= end <= len(lines)):
        raise UnitReconstructionError(
            f"{unit['unit_id']}: line span [{start}, {end}] outside "
            f"{unit['file']} ({len(lines)} lines)"
        )
    source_text = "".join(lines[start - 1 : end])
    observed = sha256_text(source_text)
    if observed != unit["text_sha256"]:
        raise UnitReconstructionError(
            f"{unit['unit_id']}: reconstructed text_sha256 mismatch "
            f"(observed {observed[:16]}… != declared {unit['text_sha256'][:16]}…)"
        )
    anchor = lines[start - 1]
    anchor_observed = sha256_text(anchor)
    if anchor_observed != unit["anchor_line_sha256"]:
        raise UnitReconstructionError(
            f"{unit['unit_id']}: anchor_line_sha256 mismatch "
            f"(observed {anchor_observed[:16]}… != declared "
            f"{unit['anchor_line_sha256'][:16]}…)"
        )
    return source_text


def canonical_from_unit(unit: dict[str, Any], source_text: str) -> dict[str, Any]:
    return {
        "unit_id": unit["unit_id"],
        "line_start": unit["line_start"],
        "line_end": unit["line_end"],
        "source_text": source_text,
    }


def validate_dm2_record(
    canonical: dict[str, Any], raw_output: str
) -> dict[str, Any]:
    """
    Run the authoritative DM-2 validator for one unit against the
    md_sheets schema profile, then return the parsed record verbatim.
    Raises ValueError on any violation (INVALID_DM2: V0-V8 — schema /
    phrase-in-source / quote-in-source / line-in-range / no-extra-fields
    / identity / semantics). The validator validates-only (returns None);
    the parsed object is never repaired here. Identity stamping (if any)
    happens in extract_one_unit before this call and is recorded in the
    log entry; the model's raw bytes on disk are never modified.
    """
    with validator_schema_profile(PROFILE_SCHEMA_PATH):
        validate_dm2.validate_semantic_extraction_json(canonical, raw_output)
    return json.loads(
        raw_output,
        object_pairs_hook=validate_dm2._reject_duplicate_json_keys,
    )


def record_filename(unit: dict[str, Any]) -> str:
    return f"{unit['step']}.dm2.json"


def read_log(log_path: Path) -> list[dict[str, Any]]:
    if not log_path.is_file():
        return []
    entries = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def resume_state(log_entries: list[dict[str, Any]]) -> dict[str, str]:
    """unit_id -> last logged status (log order)."""
    state: dict[str, str] = {}
    for entry in log_entries:
        state[entry["unit_id"]] = entry["status"]
    return state


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def append_log(log_path: Path, entry: dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def compute_max_tokens(n_chars: int) -> int:
    """
    Deterministic per-unit completion budget.

    Grounded in measured backend facts (Strata /health 2026-10-27:
    max_context=65536): the prompt for a unit of n_chars costs roughly
    0.7 tokens/char (measured: 1448-char unit -> 1980-token prompt)
    plus ~1600 chars of instruction text. The budget keeps
    prompt+completion inside 65536 with a 1024-token margin, floored at
    8192 (measured degenerate consumption for a small unit was ~5265
    completion tokens even for a ~2k-char response) and capped at 49152.
    The value is recorded per attempt in sampling_parameters provenance.
    """
    est_prompt_tokens = int((n_chars + 1600) * 0.7)
    return max(8192, min(49152, 65536 - est_prompt_tokens - 1024))


def extract_one_unit(
    unit: dict[str, Any],
    source_text: str,
    llm_call: LLMCall,
    *,
    root: Path,
    attempt: int,
    max_attempts: int,
) -> dict[str, Any]:
    """
    One full attempt: prompt -> model -> provenance -> validator.
    Never repairs model output. Logs exactly one entry per attempt.
    """
    log_path = root / "extraction_log.jsonl"
    canonical = canonical_from_unit(unit, source_text)
    # mdsheets profile: echo-waived protocol (see build_dm2_prompt note);
    # source_text is stamped from the canonical unit before validation.
    prompt = build_dm2_prompt(canonical, echo_source_text=False)

    raw_output, request_payload, metadata = llm_call(prompt)

    # Adjudicated identity policy (正典identityスタンプ, 2026-10-27):
    # the four canonical identity fields (unit_id, line_start, line_end,
    # source_text) are deterministically replaced with the exact values
    # the runner itself supplied in the prompt. The model's raw bytes are
    # persisted verbatim (raw_output_sha256 unchanged); the model-provided
    # identity block is hashed for audit. Semantic fields are never
    # touched, and the validator remains the sole authority on the
    # resulting record. Rationale: temp 0 / seed 0 retries are
    # byte-identical (empirically verified), so echo fidelity failures
    # are unrecoverable by retry, and identity binding is already
    # established by the 1-unit=1-request/response provenance pairing.
    identity_stamped = False
    model_identity_sha256 = None
    validation_input = raw_output
    try:
        _parsed = json.loads(
            raw_output,
            object_pairs_hook=validate_dm2._reject_duplicate_json_keys,
        )
        if isinstance(_parsed, dict):
            model_identity = {
                "unit_id": _parsed.get("unit_id"),
                "line_start": _parsed.get("line_start"),
                "line_end": _parsed.get("line_end"),
                "source_text": _parsed.get("source_text"),
            }
            model_identity_sha256 = sha256_text(
                json.dumps(model_identity, ensure_ascii=False, sort_keys=True)
            )
            _parsed["unit_id"] = canonical["unit_id"]
            _parsed["line_start"] = canonical["line_start"]
            _parsed["line_end"] = canonical["line_end"]
            _parsed["source_text"] = canonical["source_text"]
            validation_input = json.dumps(_parsed, ensure_ascii=False)
            identity_stamped = True
    except ValueError:
        pass

    # provenance: exact request + exact raw output, per attempt
    write_json(
        root / "work" / "request" / f"{unit['unit_id']}.attempt-{attempt}.request.json",
        request_payload,
    )
    raw_path = root / "work" / "raw" / f"{unit['unit_id']}.attempt-{attempt}.raw.txt"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(raw_output, encoding="utf-8")

    entry: dict[str, Any] = {
        "unit_id": unit["unit_id"],
        "step": unit["step"],
        "seq": unit["seq"],
        "attempt": attempt,
        "max_attempts": max_attempts,
        "timestamp": utc_now(),
        "prompt_sha256": sha256_text(prompt),
        "raw_output_sha256": sha256_text(raw_output),
        "request_file": str(raw_path.parent.parent / "request" / f"{unit['unit_id']}.attempt-{attempt}.request.json"),
        "raw_output_file": str(raw_path),
        "client": {
            "api": metadata.get("api", "openai"),
            "model": metadata.get("model"),
            "sampling_parameters": metadata.get("sampling_parameters"),
            "grammar_mode": metadata.get("grammar_mode"),
            "finish_reason": metadata.get("finish_reason"),
        },
        "validation": {
            "authority": "tools/validate_dm2.py:validate_semantic_extraction_json",
            "schema_profile": str(PROFILE_SCHEMA_PATH.relative_to(EXPERIMENT_DIR)),
            "schema_profile_diff": "unit_id.pattern ^mdsu[0-9]{4}$ (mechanical)",
            "identity_policy": (
                "adjudicated 2026-10-27: canonical identity stamping "
                "(four identity fields replaced deterministically; raw "
                "model bytes preserved; semantics untouched); "
                "2026-10-28 amendment: verbatim source_text echo waived "
                "in the mdsheets prompt protocol (model emits \"\"), "
                "justified by STEP-120 budget-exhaustion evidence "
                "(finish=length twice, byte-identical retries, semantics "
                "never reached) and by identity binding resting on "
                "provenance pairing + stamping, not echo fidelity"
            ),
            "identity_stamped": identity_stamped,
            "model_identity_sha256": model_identity_sha256,
        },
    }

    try:
        record = validate_dm2_record(canonical, validation_input)
    except (ValueError, RuntimeError) as exc:
        entry["status"] = "FAIL"
        entry["error"] = str(exc)
        entry["attempts_exhausted"] = attempt >= max_attempts
        append_log(log_path, entry)
        return entry

    record_rel = record_filename(unit)
    record_path = root / record_rel
    write_json(record_path, record)
    record_bytes = record_path.read_bytes()
    entry["status"] = "OK"
    entry["record_file"] = record_rel
    entry["record_sha256"] = sha256_text(record_bytes.decode("utf-8"))
    append_log(log_path, entry)
    return entry


def transport_fail_entry(
    unit: dict[str, Any],
    attempt: int,
    max_attempts: int,
    exc: OpenAIBackendError,
) -> dict[str, Any]:
    """
    Log entry for an attempt where the client itself failed (network /
    read timeout): no request/response pair completed, so no provenance
    files exist for this attempt. Logging the failure keeps the
    "exactly one entry per attempt" discipline and
    MISSING_EVIDENCE != PASS (the unit is FAIL, never optimistic).
    """
    return {
        "unit_id": unit["unit_id"],
        "step": unit["step"],
        "seq": unit["seq"],
        "attempt": attempt,
        "max_attempts": max_attempts,
        "timestamp": utc_now(),
        "status": "FAIL",
        "error": f"transport_error: {exc}",
        "provenance": "none (client failed before request/response completed)",
        "attempts_exhausted": attempt >= max_attempts,
    }


def plan_units(
    artifact: dict[str, Any],
    steps: list[str] | None,
    limit: int | None,
    resume: dict[str, str],
    root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    to_run, skipped = [], []
    for unit in artifact["units"]:
        if steps and unit["step"] not in steps:
            continue
        if resume.get(unit["unit_id"]) == "OK" and (root / record_filename(unit)).is_file():
            skipped.append(unit)
            continue
        to_run.append(unit)
    if limit is not None:
        to_run = to_run[:limit]
    return to_run, skipped


def gate_block(root: Path, log_entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Gate: step-1a + step-120, schema-pass + semantic-pass per step."""
    ok_steps = {
        e["step"] for e in log_entries if e.get("status") == "OK"
    }
    gate: dict[str, Any] = {}
    for step in ("STEP-1a", "STEP-120"):
        rec = root / f"{step}.dm2.json"
        has_ok_logline = step in ok_steps
        if rec.is_file() and has_ok_logline:
            status = "PASS"
            reason = (
                "record present with validator-OK log entry "
                "(schema-pass and semantic-pass enforced atomically by "
                "the validator authority)"
            )
        elif rec.is_file():
            status = "FAIL"
            reason = "record file present but no validator-OK log entry (provenance missing)"
        else:
            status = "MISSING"
            reason = "no record file and no validator-OK log entry"
        gate[step.lower()] = {
            "record_file": f"{step}.dm2.json",
            "record_present": rec.is_file(),
            "validator_ok_log_entry": has_ok_logline,
            "schema_pass": has_ok_logline and rec.is_file(),
            "semantic_pass": has_ok_logline and rec.is_file(),
            "status": status,
            "reason": reason,
        }
    gate["all_required_pass"] = all(
        gate[k]["status"] == "PASS" for k in ("step-1a", "step-120")
    )
    return gate


def run(
    *,
    units_path: Path = DEFAULT_UNITS_PATH,
    root: Path = DEFAULT_OUTPUT_ROOT,
    corpus_dir: Path = DEFAULT_CORPUS_DIR,
    steps: list[str] | None = None,
    limit: int | None = None,
    max_attempts: int = 2,
    llm_call: LLMCall | None = None,
    client_config: OpenAIChatConfig | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    artifact = load_units(units_path)
    corpus = load_corpus(corpus_dir)
    log_path = root / "extraction_log.jsonl"
    resume = resume_state(read_log(log_path))
    to_run, skipped = plan_units(artifact, steps, limit, resume, root)

    client_model: str | None = None
    grammar_probe: dict[str, Any] | None = None
    client_backed = False
    config = client_config or OpenAIChatConfig.from_env()
    effective_llm: LLMCall | None = llm_call
    if not dry_run and effective_llm is None:
        client_model, grammar_probe = resolve_model(config)

        def _client_llm_call(
            prompt: str,
            _cfg: OpenAIChatConfig = config,
            _m: str | None = client_model,
            _p: dict[str, Any] | None = grammar_probe,
            _mt: int | None = None,
        ) -> tuple[str, dict[str, Any], dict[str, Any]]:
            obs = call_openai_chat(prompt, _cfg, model=_m, grammar_probe=_p, max_tokens=_mt)
            return obs.raw_output, obs.request_payload, obs.metadata

        effective_llm = _client_llm_call
        client_backed = True

    results = {"ok": [], "fail": []}
    reconstruction_errors: list[str] = []
    for unit in to_run:
        try:
            source_text = reconstruct_unit(unit, corpus)
        except UnitReconstructionError as exc:
            # sha256 verification failure: no model call, hard stop for
            # this unit — integrity of units-json is a precondition.
            reconstruction_errors.append(str(exc))
            continue
        if dry_run:
            continue
        assert effective_llm is not None
        if client_backed:
            # per-unit deterministic completion budget (see compute_max_tokens)
            _mt = compute_max_tokens(len(source_text))

            def _llm(
                prompt: str,
                _cfg: OpenAIChatConfig = config,
                _m: str | None = client_model,
                _p: dict[str, Any] | None = grammar_probe,
                _mt: int = _mt,
            ) -> tuple[str, dict[str, Any], dict[str, Any]]:
                obs = call_openai_chat(
                    prompt, _cfg, model=_m, grammar_probe=_p, max_tokens=_mt
                )
                return obs.raw_output, obs.request_payload, obs.metadata

            effective_llm = _llm
        attempt = 0
        entry: dict[str, Any] = {}
        while attempt < max_attempts:
            attempt += 1
            try:
                entry = extract_one_unit(
                    unit,
                    source_text,
                    effective_llm,
                    root=root,
                    attempt=attempt,
                    max_attempts=max_attempts,
                )
            except OpenAIBackendError as exc:
                # transport failure is logged as FAIL for this unit and
                # the run continues: one dead unit must not orphan the
                # remaining units' attempts (resume re-plans FAILs).
                entry = transport_fail_entry(unit, attempt, max_attempts, exc)
                append_log(log_path, entry)
            if entry["status"] == "OK":
                break
        (results["ok"] if entry["status"] == "OK" else results["fail"]).append(
            unit["unit_id"]
        )

    log_entries = read_log(log_path)
    log_bytes = log_path.read_bytes() if log_path.is_file() else b""
    n_ok_total = sum(1 for e in log_entries if e.get("status") == "OK")
    set_check = {
        "policy": "1unit=1record enforced per-record by identity checks; "
        "set-level validate_semantic_extraction_set runs only on a full 127-unit pass",
        "records_present": len(list(root.glob("*.dm2.json"))),
        "units_total": len(artifact["units"]),
        "set_status": "NOT_ATTEMPTED (partial run)"
        if len(list(root.glob("*.dm2.json"))) != len(artifact["units"])
        else "RUN",
    }
    if set_check["set_status"] == "RUN":
        records = [
            json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(root.glob("*.dm2.json"))
        ]
        units_view = [
            {
                "unit_id": u["unit_id"],
                "line_start": u["line_start"],
                "line_end": u["line_end"],
            }
            for u in artifact["units"]
        ]
        with validator_schema_profile(PROFILE_SCHEMA_PATH):
            validate_dm2.validate_semantic_extraction_set(units_view, records)
        set_check["set_status"] = "PASS"

    report = {
        "task": "p2-dm2",
        "status": "COMPLETED" if not reconstruction_errors else "BLOCKED_UNIT_RECONSTRUCTION",
        "generated_utc": utc_now(),
        "input": {
            "units_json": str(units_path.relative_to(EXPERIMENT_DIR)),
            "units_artifact_id": artifact.get("units_artifact_id"),
            "units_results_digest": artifact.get("results_digest"),
            "corpus_dir": str(corpus_dir),
            "units_total": len(artifact["units"]),
        },
        "unit_source": {
            "mode": "reconstruct-from-lines",
            "verify": "text_sha256 + anchor_line_sha256 per unit before model call",
            "reconstruction_errors": reconstruction_errors,
        },
        "client": {
            "api": "openai",
            "base_url": config.base_url,
            "model": client_model if client_model else (config.model or "unresolved(dry-run)"),
            "temperature": config.temperature,
            "seed": config.seed,
            "grammar": "auto",
            "grammar_probe": grammar_probe,
        },
        "validation": {
            "authority": "tools/validate_dm2.py:validate_semantic_extraction_json",
            "checks": [
                "schema (profile)",
                "phrase in-source",
                "quote in-source",
                "line in-range",
                "no-extra-fields",
                "1unit=1record (identity + set check on full pass)",
            ],
            "schema_profile": str(PROFILE_SCHEMA_PATH.relative_to(EXPERIMENT_DIR)),
            "schema_profile_sha256": sha256_text(
                PROFILE_SCHEMA_PATH.read_text(encoding="utf-8")
            ),
            "schema_profile_diff": "unit_id.pattern only (mechanically derived)",
            "repair": "none (INVALID_DM2 logged; max 1 retry per unit)",
        },
        "run": {
            "steps_requested": steps,
            "limit": limit,
            "max_attempts_per_unit": max_attempts,
            "planned_this_run": [u["unit_id"] for u in to_run],
            "skipped_resume": [u["unit_id"] for u in skipped],
            "ok_this_run": results["ok"],
            "fail_this_run": results["fail"],
            "dry_run": dry_run,
        },
        "set_check": set_check,
        "gate": gate_block(root, log_entries),
        "provenance": {
            "request_raw": "work/request/<unit_id>.attempt-<n>.request.json",
            "raw_output": "work/raw/<unit_id>.attempt-<n>.raw.txt",
            "log": "extraction_log.jsonl",
            "log_sha256": sha256_text(log_bytes.decode("utf-8")) if log_bytes else None,
            "log_lines": len(log_entries),
        },
        "disciplines": [
            "ARTIFACT_EXISTENCE != NORMATIVE_ADOPTION",
            "VERIFICATION_IS_NOT_AUTHORIZATION",
            "MISSING_EVIDENCE != PASS",
        ],
    }
    write_json(root / "report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--units", type=Path, default=DEFAULT_UNITS_PATH)
    parser.add_argument("--root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS_DIR)
    parser.add_argument(
        "--steps",
        type=lambda s: [x.strip() for x in s.split(",")],
        default=None,
        help="comma-separated unit steps, e.g. STEP-1a,STEP-120",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="reconstruct + verify sha256 + plan only; no client, no model call",
    )
    args = parser.parse_args(argv)

    try:
        report = run(
            units_path=args.units,
            root=args.root,
            corpus_dir=args.corpus_dir,
            steps=args.steps,
            limit=args.limit,
            max_attempts=args.max_attempts,
            dry_run=args.dry_run,
        )
    except OpenAIBackendError as exc:
        print(f"BACKEND BLOCKER: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report["gate"], indent=2, ensure_ascii=False))
    print(f"status={report['status']} report={args.root / 'report.json'}")
    return 0 if report["status"] == "COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
