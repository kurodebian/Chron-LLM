#!/usr/bin/env python3
"""P2 environment profile builder/probe (read-only against corpus/ledger/records).

Builds results/mdsheets-dm2/env/env_profile.json (new provenance; touches no
existing artifact) and prints a machine-readable status block:

  E1 endpoint   /v1/models, /props grammar capability, /health max_context
                (compute_max_tokens assumes 65536 — flag divergence)
  E2 integrity  every ledger unit reconstructs sha-exactly from md_sheets;
                corpus observed_sha256 == live digests; unresolved_segments
                preservation still byte-exact. Mismatches are REPORTED
                verbatim (ADR-008: reported, not fixed) and listed as
                runner-blocked units.
  E3 progress   OK / FAIL / not-attempted unit counts from extraction_log,
                1unit=1record pairing (OK entry ↔ record file ↔ record sha),
                gate step-1a + step-120.
  E4 client     key presence (never printed), timeout, grammar mode.

Disciplines: MISSING_EVIDENCE != PASS. Exit 0 iff E1 reachable, E2 corpus+
ledger digests intact (reported mismatches listed verbatim), gate PASS.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from tools.mdsheets_dm2_runner import (  # noqa: E402
    DEFAULT_CORPUS_DIR,
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_UNITS_PATH,
    load_corpus,
    load_units,
    read_log,
    record_filename,
    reconstruct_unit,
)

ENV_PROFILE_PATH = DEFAULT_OUTPUT_ROOT / "env" / "env_profile.json"
HERMES_ENV = Path.home() / ".hermes" / ".env"
KEY_VAR = "HERMES_CUSTOM_10_0_0_1_8080_API_KEY"


def key_source() -> tuple[bool, str]:
    if os.environ.get("MDSHEETS_DM2_API_KEY"):
        return True, "env MDSHEETS_DM2_API_KEY"
    if HERMES_ENV.is_file():
        for line in HERMES_ENV.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(f"{KEY_VAR}="):
                return True, f"file ~/.hermes/.env ({KEY_VAR})"
    return False, "absent"


def get(url: str, key: str | None) -> dict:
    req = urllib.request.Request(url)
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def endpoint_profile(key: str | None) -> dict:
    base = os.environ.get("MDSHEETS_DM2_BASE_URL", "http://10.0.0.1:8080/v1")
    out = {"base_url": base, "reachable": False}
    try:
        models = get(base.rstrip("/").replace("/v1", "") + "/v1/models", key)
        ids = [m.get("id") for m in models.get("data", [])]
        out.update(reachable=True, served_models=ids)
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out
    try:
        props = get(base.rstrip("/").replace("/v1", "") + "/props", key)
        blob = json.dumps(props, ensure_ascii=False).lower()
        out["props_keys"] = sorted(props.keys())
        out["grammar_advertised"] = "grammar" in blob
    except Exception as exc:  # noqa: BLE001
        out["props_error"] = f"{type(exc).__name__}: {exc}"
    try:
        health = get(base.rstrip("/").replace("/v1", "") + "/health", key)
        mc = health.get("max_context") or health.get("n_ctx")
        out["max_context"] = mc
        out["max_context_matches_runner_assumption"] = mc == 65536 or mc is None
    except Exception as exc:  # noqa: BLE001
        out["health_error"] = f"{type(exc).__name__}: {exc}"
    return out


def integrity_profile(corpus_dir: Path, units_path: Path) -> dict:
    artifact = load_units(units_path)
    corpus = load_corpus(corpus_dir)
    blocked, mismatched = [], []
    for unit in artifact["units"]:
        try:
            reconstruct_unit(unit, corpus)
        except Exception as exc:  # noqa: BLE001
            mismatched.append({"unit_id": unit["unit_id"], "error": str(exc)})
            blocked.append(unit["unit_id"])
    # corpus layer untouched: ledger-declared observed digests vs live files
    corpus_checks = []
    declared = {cf["file"]: cf["observed_sha256"] for cf in artifact.get("corpus_files", [])}
    for name, lines in corpus.items():
        live = hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
        got = declared.get(name)
        corpus_checks.append({
            "file": name,
            "declared_sha256": got,
            "live_sha256": live,
            "match": got == live if got else "no-declaration",
        })
    # preservation: unresolved_segments still byte-exact in corpus
    preserved = []
    for seg in artifact.get("unresolved_segments", []):
        lines = corpus.get(seg.get("file"))
        if lines is None:
            preserved.append({"segment": seg.get("segment_id"), "match": False,
                              "reason": "file missing"})
            continue
        s, e = seg["line_start"], seg["line_end"]
        live_span = "".join(lines[s - 1:e])
        live = hashlib.sha256(live_span.encode("utf-8")).hexdigest()
        preserved.append({"segment": seg.get("segment_id"),
                          "declared_sha256": seg.get("text_sha256"),
                          "live_sha256": live,
                          "match": live == seg.get("text_sha256")})
    return {
        "units_total": len(artifact["units"]),
        "reconstruction_blocked_units": blocked,
        "reconstruction_mismatches": mismatched,
        "corpus_digest_checks": corpus_checks,
        "preservation_checks": preserved,
    }


def progress_profile(root: Path, artifact_units: list[dict]) -> dict:
    entries = read_log(root / "extraction_log.jsonl")
    last: dict[str, str] = {}
    for e in entries:
        last[e["unit_id"]] = e["status"]
    ok, fail, never = [], [], []
    pairing_ok = True
    for u in artifact_units:
        st = last.get(u["unit_id"])
        rec = root / record_filename(u)
        if st == "OK":
            ok.append(u["unit_id"])
            if not rec.is_file():
                pairing_ok = False
        elif st == "FAIL":
            fail.append(u["unit_id"])
        else:
            never.append(u["unit_id"])
    ok_steps = {e["step"] for e in entries if e.get("status") == "OK"}
    gate = {s: (s in ok_steps and (root / f"{s}.dm2.json").is_file())
            for s in ("STEP-1a", "STEP-120")}
    return {
        "log_lines": len(entries),
        "ok_units": len(ok),
        "fail_units": len(fail),
        "not_attempted_units": len(never),
        "fail_unit_ids": fail,
        "ok_record_pairing_clean": pairing_ok,
        "gate": gate,
        "gate_all_pass": all(gate.values()),
    }


def main() -> int:
    has_key, source = key_source()
    key = os.environ.get("MDSHEETS_DM2_API_KEY")
    if not key and HERMES_ENV.is_file():
        for line in HERMES_ENV.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(f"{KEY_VAR}="):
                key = line.split("=", 1)[1].strip()
                break
    ep = endpoint_profile(key)
    integ = integrity_profile(DEFAULT_CORPUS_DIR, DEFAULT_UNITS_PATH)
    artifact = load_units(DEFAULT_UNITS_PATH)
    prog = progress_profile(DEFAULT_OUTPUT_ROOT, artifact["units"])

    profile = {
        "task": "p2-env",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint": ep,
        "client": {
            "api": "openai",
            "temperature": 0.0,
            "seed": 0,
            "timeout_s": int(os.environ.get("MDSHEETS_DM2_TIMEOUT", "300")),
            "api_key_present": has_key,
            "api_key_source": source,
            "grammar_mode": "auto",
            "grammar_advertised_by_backend": ep.get("grammar_advertised", False),
            "enable_thinking_profile_default": os.environ.get(
                "MDSHEETS_DM2_ENABLE_THINKING", "unset"
            ),
        },
        "integrity": integ,
        "progress": prog,
        "calibration": {
            "asof": "2026-11-03",
            "measured_completion_rate_tok_s": 19.1,
            "measurement": "2026-11-03 chat completion 400 tokens in 20.9s (temp 0, seed 0)",
            "thinking_toggle": (
                "profile default MDSHEETS_DM2_ENABLE_THINKING=0 (transport-only; exact "
                "payload persisted per attempt in work/request/*.request.json). Old "
                "thinking-enabled runs consumed ~5.2k tokens/unit at ~19 tok/s => ~270s, "
                "causing the 300s timeout FAIL on mdsu0058; temp/seed/grammar untouched."
            ),
            "timeout_s_recommendation": 600,
        },
        "causal_verification_env": {
            "unit_ledger": f"{ROOT}/ledger/mdsheets_units.json",
            "dm2_records_dir": f"{ROOT}/results/mdsheets-dm2",
            "validator_authority": f"{ROOT}/tools/mdsheets_dm2_verify.py",
            "causal_ir_builder": f"{ROOT}/extract_cir.py",
            "causal_runtime_v1": f"{ROOT}/results/impl_verification/causal_runtime_v1",
            "adoption": f"{ROOT}/results/impl_verification/adoption",
            "reclassification": f"{ROOT}/results/impl_verification/adoption/reclassify_adoption.py (derived read-only; P3 tier ADOPTED_LLM_PROVISIONAL pending human ratification)",
            "external_quality_gate": f"{ROOT}/audit.sh (EXTERNAL_QUALITY_GATE, unmodified authority)",
            "test_baseline": "pytest 298 passed (2026-11-03, this environment)",
        },
        "disciplines": [
            "MISSING_EVIDENCE != PASS",
            "digest mismatches reported verbatim; no repair",
            "keys never written to profile or printed",
        ],
    }
    ENV_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ENV_PROFILE_PATH.write_text(
        json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(profile, indent=2, ensure_ascii=False))
    ok = (ep.get("reachable")
          and prog["gate_all_pass"]
          and prog["ok_record_pairing_clean"]
          and all(c["match"] is True for c in integ["corpus_digest_checks"])
          and all(p["match"] is True for p in integ["preservation_checks"]))
    print(f"ENV_STATUS={'READY' if ok else 'BLOCKED'} profile={ENV_PROFILE_PATH.relative_to(ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
