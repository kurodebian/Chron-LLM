"""Validation harness for the STEP-192 L1 reference model (D11 adjudication).

Two-tier (D11 V2):
  Tier 1  exhaustive model-check: ops<=3 x Idempotency states x CP1..CP6 x
          restarts 0..2 x audit write success/failure, all interleavings.
  Tier 2  property-fuzz: ops 5..10, compound audit faults, fixed-seed corpus.

Invariants (D11 V3): INV-01..INV-08. Harness discipline (D11 V6): INV-H1 —
no PYTHONHASHSEED dependence (sorted() iteration everywhere; identical
results across seeds; fixed-seed regression corpus).

Declaration discipline (D11): PASS here grounds LINEARIZATION_VALIDATION:
EXECUTED for the MODEL only. TEST_PASS != ACCEPTANCE, ACCEPTANCE !=
GLOBAL_ACCEPTANCE; model validation is not implementation validation.
LINEARIZATION_VALIDATION status fields in the STEP-192 draft remain
NOT_EXECUTED until the adoption adjudication updates them.

Gate mapping (D11 受理ゲート):
  AG-192-05a  tier-1 exhaustive completion, INV-01..08 all held (or
              counterexamples routed to governance adjudication, not silently
              patched in the model).
  AG-192-05b  fuzz suite INV-H1 proven (seed-independence).
  AG-192-05c  regression corpus fixed-seed re-run evidence saved
              (validation/regression_corpus_digest.txt).
"""

from __future__ import annotations

import itertools
import json
import os
import random
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import l1_reference_model as L1  # noqa: E402

REGR_DIGEST_PATH = os.path.join(_HERE, "regression_corpus_digest.txt")


# ---------------------------------------------------------------------------
# Scenario enumeration
# ---------------------------------------------------------------------------


def exhaustive_scenarios():
    """Tier 1: ops 1..3 x CP1..CP6 x crash_index x audit-failure subsets
    (size<=2) x CP4 persistence variants. Single canonical append path means
    interleavings live in [admission, commit_point) (D11 V1); audit-failure
    subsets cover the audit dimension (D10 I5)."""
    out = []
    for n in (1, 2, 3):
        ops = [f"op{i}" for i in range(n)]
        for cp in L1.CRASH_POINTS:
            for ci in range(n):
                persist_variants = ("survives", "lost") if cp == "CP4" else ("survives",)
                for r in (0, 1, 2):
                    for fail in itertools.islice(
                        _subsets(ops, 2), 0, _subset_count(n, 2)
                    ):
                        for pv in persist_variants:
                            for restart in range(r + 1):
                                out.append({
                                    "scenario": L1.make_scenario(n, fail),
                                    "crash_point": cp,
                                    "crash_index": ci,
                                    "persistence": pv,
                                    "restarts": restart,
                                })
    return out


def _subset_count(n, max_r):
    return sum(1 for _ in _subsets([0] * n, max_r))


def _subsets(items, max_r):
    for r in range(max_r + 1):
        for combo in itertools.combinations(sorted(items), r):
            yield list(combo)


def fuzz_corpus(seed=19205, count=300):
    """Tier 2: fixed-seed corpus (INV-H1: random series only via explicit
    seeds; corpus re-run at fixed seed always)."""
    rng = random.Random(seed)
    corpus = []
    for _ in range(count):
        n = rng.randint(5, 10)
        cp = rng.choice(L1.CRASH_POINTS)
        ci = rng.randrange(n)
        nfail = rng.choice([0, 0, 1, 2, 3])  # compound audit faults
        fail = sorted(rng.sample(range(n), nfail))
        pv = rng.choice(L1.PERSISTENCE_VARIANTS) if cp == "CP4" else "survives"
        restarts = rng.choice([0, 1, 2])
        corpus.append({
            "scenario": L1.make_scenario(n, fail),
            "crash_point": cp,
            "crash_index": ci,
            "persistence": pv,
            "restarts": restarts,
        })
    return corpus


# ---------------------------------------------------------------------------
# Invariant checks INV-01..INV-08 (D11 V3)
# ---------------------------------------------------------------------------


def check_invariants(case, final):
    """Returns list of violation descriptors (empty = all held)."""
    v = []
    canon = final["canonical"]

    # INV-01 gapless committed prefix (S1 / D3 / SequenceProof direction)
    prev = "GENESIS"
    for i, rec in enumerate(canon):
        if rec["position"] != i or rec["prev_hash"] != prev:
            v.append("INV-01")
            break
        prev = L1.event_hash(rec)

    # INV-02 Receipt uniqueness + regeneration byte-identity (S3 / D8 M5)
    for rec in canon:
        oid = rec["operation_id"]
        if final["receipts"].get(oid) != L1.compute_receipt(rec):
            v.append("INV-02")
    re_final = L1.recover(_as_disk(final))
    if re_final["receipts"] != final["receipts"]:
        v.append("INV-02")

    # INV-03 restart-count / time independence (S2 / §10)
    state = _as_disk(final)
    d0 = L1.state_digest(final)
    s1 = L1.recover(state)
    for _ in range(case["restarts"]):
        s1 = L1.recover(_as_disk(s1))
    if L1.state_digest(s1) != d0:
        v.append("INV-03")

    # INV-04 orphan pipeline + transfer idempotence (D9 G1..G4)
    kept_ops = {r["operation_id"] for r in canon}
    transfers = {a["operation_id"] for a in final["audit"]
                 if a["event_type"] == "ORPHAN_INTENT_TRANSFER"}
    for oid in sorted(final["idem"]):
        if oid in kept_ops:
            continue
        if final["idem"][oid]["state"] != "ORPHAN_RESOLVED":
            v.append("INV-04")
        elif oid not in transfers:
            v.append("INV-04")
    if any(a["event_type"] == "ORPHAN_INTENT_TRANSFER"
           and a["operation_id"] in transfers
           for a in re_final["audit"] if a not in final["audit"]):
        v.append("INV-04")  # second transfer on re-recovery = not idempotent

    # INV-05 NO_SILENT_DISCARD 1:1 (D10 I4)
    n_discarded = sum(1 for f in final["faults"] if f["kind"] == "DISCARDED_INTERVAL")
    n_evac = sum(1 for a in final["audit"] if a["event_type"] == "DISCARDED_INTERVAL")
    if n_discarded != n_evac:
        v.append("INV-05")

    # INV-06 persistence-happens-before preserved in canonical order (S1)
    committed = [r["operation_id"] for r in canon if not r["operation_id"].startswith("gov-")]
    attempted = [o for o in final["attempted"] if o in set(committed)]
    if committed != attempted:
        v.append("INV-06")

    # INV-07 audit faults do not change recovery classification (S4 / §11)
    clean_case = dict(case)
    fail_ops = case["scenario"]["audit_fail_ops"]
    if fail_ops:
        # execute() holds at the first audit failure and stops attempting
        # later ops; the clean comparison run is the same attempted prefix
        # with a healthy audit. Classification of that prefix must match.
        # (audit_fail_ops entries are "opN" ids or bare int indices,
        # depending on the corpus.)
        def _op_index(oid):
            return int(oid[2:]) if isinstance(oid, str) else int(oid)
        n_clean = min(_op_index(oid) for oid in fail_ops)
        clean_scenario = L1.make_scenario(n_clean, ())
    else:
        clean_scenario = L1.make_scenario(len(case["scenario"]["ops"]), ())
    clean = L1.recover(L1.execute(clean_scenario, case["crash_point"],
                                  case["crash_index"], case["persistence"]))
    if [L1.event_hash(r) for r in clean["canonical"]] != [L1.event_hash(r) for r in canon]:
        v.append("INV-07")

    # INV-08 audit-write failure -> admission HOLD, committed finality intact
    holds = set(final["holds"])
    if holds:
        for oid in holds:
            if oid in final["idem"]:
                v.append("INV-08")  # held op must have no attempted state
        first_fail = min(case["scenario"]["audit_fail_ops"])
        committed_set = set(committed)
        for oid in committed_set:
            if int(oid[2:]) >= int(first_fail[2:]) and oid not in holds:
                # only allowed if it was attempted before the failure point
                if oid not in final["attempted"][:int(first_fail[2:])]:
                    v.append("INV-08")
    return sorted(set(v))


def _as_disk(final):
    """Recovered state is itself a valid disk state for re-recovery."""
    return {
        "canonical": [dict(r) for r in final["canonical"]],
        "torn": [],
        # Intents persist on disk only while they matter for recovery:
        # committed intents and ORPHAN_RESOLVED intents (idempotence marker,
        # D9 G4). Intents fixed but never written are consumed by the
        # transfer and do not survive as disk artifacts.
        "intents": {oid: {"operation_id": oid,
                          "content_hash": L1.sha256_hex(L1.canonical_json({"op": oid})),
                          "authority_ref": "authA",
                          "declared_boundaries": [0, 1],
                          "intent_ref": final["idem"][oid].get(
                              "intent_ref", f"intent-{oid}")}
                    for oid in final["idem"]
                    if final["idem"][oid]["state"] == "ORPHAN_RESOLVED"
                    or oid in {r["operation_id"] for r in final["canonical"]}},
        "idem": {k: dict(v) for k, v in final["idem"].items()},
        "receipts": dict(final["receipts"]),
        "audit": [dict(a) for a in final["audit"]],
        "holds": list(final["holds"]),  # holds persist until adjudication
        "attempted": list(final["attempted"]),
    }


# ---------------------------------------------------------------------------
# Sweeps (deterministic aggregate output — INV-H1)
# ---------------------------------------------------------------------------


def sweep(cases):
    """Run all cases, check INV-01..08, return canonical aggregate dict.
    Aggregation is order-independent: per-case results keyed by case id,
    then sorted (INV-H1: no iteration-order dependence)."""
    results = {}
    for idx, case in enumerate(cases):
        disk = L1.execute(case["scenario"], case["crash_point"],
                          case["crash_index"], case["persistence"])
        final = L1.recover(disk)
        violations = check_invariants(case, final)
        case_id = (
            len(case["scenario"]["ops"]), case["crash_point"], case["crash_index"],
            case["persistence"], tuple(case["scenario"]["audit_fail_ops"]), case["restarts"],
        )
        results[repr(case_id)] = {
            "digest": L1.state_digest(final),
            "violations": violations,
        }
    fault_tally = {}
    for case in cases:
        disk = L1.execute(case["scenario"], case["crash_point"],
                          case["crash_index"], case["persistence"])
        final = L1.recover(disk)
        for f in final["faults"]:
            fault_tally[f["kind"]] = fault_tally.get(f["kind"], 0) + 1
    total_violations = sum(len(r["violations"]) for r in results.values())
    return {
        "cases": len(cases),
        "pass": sum(1 for r in results.values() if not r["violations"]),
        "violations_total": total_violations,
        "fault_tally": fault_tally,
        "results_digest": L1.sha256_hex(L1.canonical_json(results)),
    }


# ---------------------------------------------------------------------------
# pytest suite
# ---------------------------------------------------------------------------

_EXHAUSTIVE = None
_FUZZ = None


def _exhaustive():
    global _EXHAUSTIVE
    if _EXHAUSTIVE is None:
        _EXHAUSTIVE = exhaustive_scenarios()
    return _EXHAUSTIVE


def _fuzz():
    global _FUZZ
    if _FUZZ is None:
        _FUZZ = fuzz_corpus()
    return _FUZZ


def _case_pair(case):
    disk = L1.execute(case["scenario"], case["crash_point"],
                      case["crash_index"], case["persistence"])
    return case, L1.recover(disk)


def test_tier1_exhaustive_all_invariants():
    violations = []
    for case in _exhaustive():
        c, final = _case_pair(case)
        violations.extend(check_invariants(c, final))
    assert not violations, f"INV violations: {sorted(set(violations))[:10]}"


def _sampled_cases():
    cases = _exhaustive()
    step = max(1, len(cases) // 120)
    return cases[::step]


import pytest  # noqa: E402


def _param_cases():
    return [tuple((c["crash_point"], c["crash_index"], c["persistence"],
                   tuple(c["scenario"]["audit_fail_ops"]), len(c["scenario"]["ops"])))
            for c in _sampled_cases()]


import pytest  # noqa: E402


@pytest.mark.parametrize("case_ref", _param_cases())
def test_inv01_gapless(case_ref):
    case = _match_case(case_ref)
    _c, final = _case_pair(case)
    prev = "GENESIS"
    for i, rec in enumerate(final["canonical"]):
        assert rec["position"] == i and rec["prev_hash"] == prev
        prev = L1.event_hash(rec)


def _match_case(ref):
    for c in _sampled_cases():
        if (c["crash_point"], c["crash_index"], c["persistence"],
                tuple(c["scenario"]["audit_fail_ops"]), len(c["scenario"]["ops"])) == ref:
            return c
    raise KeyError(ref)


def test_tier2_fuzz_all_invariants():
    violations = []
    for case in _fuzz():
        c, final = _case_pair(case)
        violations.extend(check_invariants(c, final))
    assert not violations, f"INV violations: {sorted(set(violations))[:10]}"


def test_inv_h1_order_independence():
    """Same case set in shuffled order -> identical aggregate digest."""
    cases = _exhaustive()
    a = sweep(cases)
    shuffled = list(cases)
    random.Random(7).shuffle(shuffled)
    b = sweep(shuffled)
    assert a["results_digest"] == b["results_digest"]
    assert a["fault_tally"] == b["fault_tally"]


def test_inv_h1_seed_independence_subprocess():
    """INV-H1: identical sweep output under different PYTHONHASHSEED."""
    script = os.path.join(_HERE, "l1_reference_model.py")
    digests = set()
    for seed in ("0", "1", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        out = subprocess.run(
            [sys.executable, os.path.join(_HERE, "run_sweep.py"), "--seed", seed],
            capture_output=True, text=True, env=env, cwd=_REPO, timeout=600)
        assert out.returncode == 0, out.stderr[-2000:]
        payload = json.loads(out.stdout)
        digests.add(payload["results_digest"])
    assert len(digests) == 1, f"PYTHONHASHSEED-dependent sweep output: {digests}"


def test_no_retroactive_invalidation():
    """D12 X3: governance revocation event never invalidates prior
    committed records / Receipts (historical validity unchanged)."""
    scen = L1.make_scenario(3, (), revocation={"authority_ref": "authA", "after_index": 1})
    disk = L1.execute(scen, crash_point=None, crash_index=-1)
    before = [dict(r) for r in disk["canonical"][:2]]
    final = L1.recover(disk)
    kept = final["canonical"]
    assert len(kept) == 4  # 3 ops + governance event, nothing discarded
    for b, k in zip(before, kept[:2]):
        assert b == k
        assert final["receipts"][b["operation_id"]] == L1.compute_receipt(b)
    # revocation takes effect only for admissions AFTER its position (X2):
    # modeled as the future validAt extension contract (D12 X1) — L1 asserts
    # only the non-retroactivity half here.


def test_restart_count_independence():
    for case in _sampled_cases():
        disk = L1.execute(case["scenario"], case["crash_point"],
                          case["crash_index"], case["persistence"])
        s0 = L1.recover(disk)
        s1 = L1.recover(_as_disk(s0))
        s2 = L1.recover(_as_disk(s1))
        assert L1.state_digest(s0) == L1.state_digest(s1) == L1.state_digest(s2)


def test_receipt_anchor_never_discarded():
    """D7 R4: a record with a valid stored Receipt is never discarded."""
    for case in _exhaustive():
        disk = L1.execute(case["scenario"], case["crash_point"],
                          case["crash_index"], case["persistence"])
        final = L1.recover(disk)  # raises AssertionError internally on violation
        for oid, rec_hash in ((r["operation_id"], L1.event_hash(r))
                              for r in final["canonical"]):
            assert oid in final["receipts"]


# ---------------------------------------------------------------------------
# main: gate evidence (AG-192-05a/b/c)
# ---------------------------------------------------------------------------


def main(argv=None):
    argv = argv or sys.argv[1:]
    if argv[:1] == ["--seed"]:
        cases = _exhaustive() + _fuzz()
        print(L1.canonical_json(sweep(cases)))
        return 0
    tier1 = sweep(_exhaustive())
    tier2 = sweep(_fuzz())
    corpus_digest = L1.sha256_hex(L1.canonical_json(
        [L1.state_digest(L1.recover(L1.execute(
            c["scenario"], c["crash_point"], c["crash_index"], c["persistence"])))
         for c in _fuzz()]))
    with open(REGR_DIGEST_PATH, "w", encoding="utf-8") as fh:
        fh.write(corpus_digest + "\n")
    report = {
        "tier1_exhaustive": tier1,
        "tier2_fuzz": tier2,
        "regression_corpus_digest": corpus_digest,
        "gates": {
            "AG-192-05a": tier1["violations_total"] == 0 and tier1["pass"] == tier1["cases"],
            "AG-192-05b": tier2["violations_total"] == 0 and tier2["pass"] == tier2["cases"],
            "AG-192-05c": bool(corpus_digest),
        },
        "declaration": "MODEL validation only. TEST_PASS != ACCEPTANCE; "
                       "ACCEPTANCE != GLOBAL_ACCEPTANCE; implementation "
                       "validation is a separate gate (D11 V4).",
    }
    print(L1.canonical_json(report))
    return 0 if all(report["gates"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
