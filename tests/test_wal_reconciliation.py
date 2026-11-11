"""
test_wal_reconciliation.py — Canonical ↔ History join path, ratified norms.

Ratified 2026-11-11 (RATIFIED_HUMAN): ADR-001/002/003/004.
  - Recovery never resolves PREPARED by assumption: IN_DOUBT preserved, isolated.
  - Corrupt/torn records are quarantined (preserved aside), never truncated away.
  - Canonical ↔ History comparison path (join) is fail-closed:
    MISSING_EVIDENCE != PASS.
  - Canonical is reconstructible from durable COMMITTED frames only (recoverability).
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_BRIDGE = ROOT / "chron-llm-causal" / "src" / "causal_kernel" / "bridge" / "wal_triad_bridge.py"


def _load_bridge():
    spec = importlib.util.spec_from_file_location("wal_triad_bridge", str(_BRIDGE))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bridge = _load_bridge()
WALTriadIndex = bridge.WALTriadIndex
join_canonical_history = bridge.join_canonical_history
recover_canonical = bridge.recover_canonical

sys.path.insert(0, str(ROOT / "tests"))
from test_cae_e2e import PhaseAWALEngineMock

from tools.cae_extractor import (
    CAENode,
    Condition,
    finalize_commit,
    prepare_commit_payload,
)


def _node(node_id):
    return CAENode(
        node_id=node_id,
        title="Reconcile node",
        causes=[Condition("session.state", "EQ", "AUTHENTICATED")],
        action="commit",
        effects=[Condition("tx.status", "EQ", "COMMITTED")],
        raw_text="raw text",
        provenance={"pos": 0, "phase": 1, "token_score": 0.9},
        scope={"scope_id": "scope-01"},
    )


def _engine_with_crash():
    """Prepare tx for node A (crash before commit), then commit tx for node B."""
    engine = PhaseAWALEngineMock()
    node_a, node_b = _node("node-A"), _node("node-B")
    prep_a = prepare_commit_payload(engine, node_a)
    # crash: finalize_commit for A never called
    kernel_state = {"Canonical": {"CanonicalSequence": None, "History": [], "Txids": []}}

    def apply_hook(rec):
        kernel_state["Canonical"]["CanonicalSequence"] = rec["hdr"]["sequence"]
        kernel_state["Canonical"]["History"].append(node_b.node_id)
        kernel_state["Canonical"]["Txids"].append(rec["hdr"]["txid"])

    prep_b = prepare_commit_payload(engine, node_b)
    finalize_commit(engine, prep_b["txid"], kernel_apply_hook=apply_hook)
    return engine, kernel_state, prep_a["txid"], prep_b["txid"]


def _attach_all(engine, index):
    for rec in engine.wal_log:
        index.attach(
            rec["hdr"]["txid"], rec["payload"], rec["hdr"]["type"],
            sequence=rec["hdr"]["sequence"],
        )
    return index


def test_recovered_prepared_stays_in_doubt_never_canonical():
    engine, kernel_state, txid_a, txid_b = _engine_with_crash()
    rec_res = engine.recover()
    assert rec_res["status"] == "OK"
    # ADR-001: PREPARED preserved as IN_DOUBT; nothing truncated
    assert rec_res["in_doubt_records"] == 1
    assert rec_res["quarantined_records"] == 0
    assert rec_res["recovered_records"] == 1
    # durable log still carries the unresolved prepared record
    assert any(r["hdr"]["txid"] == txid_a and r["hdr"]["type"] == "PREPARED"
               for r in engine.wal_log)
    # IN_DOUBT never entered canonical history
    assert txid_a not in kernel_state["Canonical"]["Txids"]
    # the committed tx did enter canonical history
    assert txid_b in kernel_state["Canonical"]["Txids"]


def test_join_agrees_after_recovered_recovery():
    engine, kernel_state, txid_a, txid_b = _engine_with_crash()
    engine.recover()
    idx = _attach_all(engine, WALTriadIndex())
    report = join_canonical_history(idx, kernel_state["Canonical"]["Txids"])
    assert report["verdict"] == "AGREED"
    assert report["committed_txids"] == [txid_b]
    assert report["in_doubt_txids"] == [txid_a]
    assert report["phantom_effects"] == []


def test_join_flags_in_doubt_leak_as_phantom():
    engine, kernel_state, txid_a, txid_b = _engine_with_crash()
    engine.recover()
    idx = _attach_all(engine, WALTriadIndex())
    # Simulate a violation: IN_DOUBT effect wrongly present in canonical history.
    kernel_state["Canonical"]["Txids"].append(txid_a)
    report = join_canonical_history(idx, kernel_state["Canonical"]["Txids"])
    assert report["verdict"] == "DIVERGENT"
    assert report["phantom_effects"] == [txid_a]
    assert txid_b in report["committed_txids"]  # legit committed effect stays agreed
    assert report["missing_effects"] == []


def test_corrupt_record_quarantined_not_lost():
    engine = PhaseAWALEngineMock()
    # Inject a corrupt prepared frame directly to exercise the recovery boundary.
    prep = engine.prepare({"node": {"id": "x"}})
    prep["rec"]["crc_status"] = "BAD"
    rec_res = engine.recover()
    assert rec_res["quarantined_records"] == 1
    assert rec_res["in_doubt_records"] == 0
    assert rec_res["recovered_records"] == 0
    # quarantined frames preserved aside, never dropped
    assert len(engine.quarantine) == 1
    assert engine.quarantine[0]["crc_status"] == "BAD"


def test_canonical_reconstructible_from_durable_frames():
    engine, kernel_state, txid_a, txid_b = _engine_with_crash()
    engine.recover()
    idx = _attach_all(engine, WALTriadIndex())
    rec = recover_canonical(idx)
    assert rec["canonical_txids"] == [txid_b]
    assert rec["sequence_basis"] == kernel_state["Canonical"]["CanonicalSequence"]
    assert rec["in_doubt_txids"] == [txid_a]
    assert rec["replay_set"] == rec["canonical_txids"]
    assert rec == recover_canonical(idx)  # idempotent


def test_explicit_resolution_after_recovery_is_accepted():
    # After recovery, an explicit resolution frame (commit) may resolve IN_DOUBT.
    engine, kernel_state, txid_a, txid_b = _engine_with_crash()
    engine.recover()
    kernel_state["Canonical"]["Txids"].append(txid_a)  # resolution arrives
    idx = _attach_all(engine, WALTriadIndex())
    rec_a = next(r for r in engine.wal_log if r["hdr"]["txid"] == txid_a)
    seq_next = max(
        r["hdr"]["sequence"] for r in engine.wal_log
        if r["hdr"]["sequence"] is not None
    ) + 1
    idx.attach(txid_a, rec_a["payload"], "COMMITTED", sequence=seq_next)
    report = join_canonical_history(idx, kernel_state["Canonical"]["Txids"])
    assert report["verdict"] == "AGREED"
    assert report["in_doubt_txids"] == []
    assert txid_b in report["committed_txids"]
