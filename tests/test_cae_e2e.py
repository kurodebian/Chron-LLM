#!/usr/bin/env python3
# test_cae_e2e.py
# E2E Test Suite for Phase B (cae_extractor.py) and Phase A (R2.1-D WAL 2PC contract)

import pytest
import zlib
from typing import Dict, Any, Optional

from tools.cae_extractor import (
    CAENode,
    Condition,
    run_extraction_pipeline,
    prepare_commit_payload,
    finalize_commit,
    abort_tx,
    PrepareError,
    CommitError,
    AbortError,
    canonical_json_bytes,
)


# ---------------------------------------------------------------------
# Phase A Mock Engine (R2.1-D Compliant Simulation)
# ---------------------------------------------------------------------
class PhaseAWALEngineMock:
    """
    Simulates Phase A Durable Storage WAL with 2PC (prepare/commit/abort)
    and crash recovery mechanics (recover/truncate).
    """

    def __init__(self):
        self.wal_log = []
        self.next_txid = 1001
        self.active_transactions: Dict[int, Dict[str, Any]] = {}
        self.corrupt_next_prepare_len = False
        self.fail_next_prepare_crc = False

    def prepare(self, payload_dict: Dict[str, Any]) -> Dict[str, Any]:
        txid = self.next_txid
        self.next_txid += 1

        payload_bytes = canonical_json_bytes(payload_dict)
        meta = payload_dict.get("_meta", {})
        base_len = meta.get("payload_len", len(payload_bytes))

        # Allow test injection of header length mismatch
        hdr_payload_len = base_len + 10 if self.corrupt_next_prepare_len else base_len
        crc_status = "BAD" if self.fail_next_prepare_crc else "OK"

        hdr = {
            "type": "PREPARED",
            "txid": txid,
            "payload_len": hdr_payload_len,
            "clock": 0,
            "target_hash_hi": 0x12345678,
            "target_hash_lo": 0x9ABCDEF0,
        }

        rec = {
            "hdr": hdr,
            "payload": payload_dict,
            "crc32": zlib.crc32(payload_bytes),
            "crc_status": crc_status,
        }

        self.active_transactions[txid] = rec
        self.wal_log.append(rec)

        # Reset injected fault flags
        self.corrupt_next_prepare_len = False
        self.fail_next_prepare_crc = False

        return {"txid": txid, "rec": rec, "status": "OK"}

    def commit(self, txid: int) -> Dict[str, Any]:
        rec = self.active_transactions.get(txid)
        if not rec or rec["hdr"]["type"] != "PREPARED":
            return {"status": "CORRUPT", "message": f"Invalid txid {txid} for commit"}

        rec["hdr"]["type"] = "COMMITTED"
        rec["hdr"]["clock"] += 1  # Lamport Clock increment on commit

        del self.active_transactions[txid]
        return {"rec": rec, "status": "OK", "hdr_clock": rec["hdr"]["clock"]}

    def abort(self, txid: int) -> Dict[str, Any]:
        rec = self.active_transactions.get(txid)
        if not rec:
            return {"status": "CORRUPT", "message": f"Invalid txid {txid} for abort"}

        rec["hdr"]["type"] = "ABORTED"
        del self.active_transactions[txid]
        return {"rec": rec, "status": "OK"}

    def recover(self) -> Dict[str, Any]:
        """
        Simulates Phase A startup recovery per R2.1-D:
        Scans WAL log, truncates/discards uncommitted PREPARED or CORRUPT records.
        """
        recovered_log = []
        truncated_count = 0

        for rec in self.wal_log:
            hdr_type = rec["hdr"]["type"]
            if hdr_type in ("COMMITTED", "ABORTED") and rec.get("crc_status") == "OK":
                recovered_log.append(rec)
            else:
                truncated_count += 1

        self.wal_log = recovered_log
        self.active_transactions.clear()

        return {
            "status": "OK",
            "recovered_records": len(recovered_log),
            "truncated_records": truncated_count,
        }


# ---------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------
def test_2pc_happy_path():
    """Verify normal extraction -> prepare -> commit -> kernel clock update flow."""
    engine = PhaseAWALEngineMock()
    text = "If session.state == AUTHENTICATED then set tx.status = COMMITTED"

    node, conf = run_extraction_pipeline(
        text, pos=0, phase=1, score=0.95, scope_id="scope-01", lamport_clock=10
    )
    assert conf >= 0.75

    # 1. Prepare
    prep = prepare_commit_payload(engine, node)
    txid = prep["txid"]
    assert txid >= 1001
    assert prep["payload_len"] > 0
    assert len(prep["content_hash"]) == 64

    # 2. Commit & Apply Hook
    kernel_state = {"Canonical": {"LamportClock": 10, "History": []}}

    def apply_hook(rec):
        hdr = rec["hdr"]
        kernel_state["Canonical"]["LamportClock"] = hdr["clock"]
        kernel_state["Canonical"]["History"].append(node.node_id)

    commit_res = finalize_commit(engine, txid, kernel_apply_hook=apply_hook)

    assert commit_res["status"] == "OK"
    assert commit_res["rec"]["hdr"]["type"] == "COMMITTED"
    assert kernel_state["Canonical"]["LamportClock"] == 1  # Updated by header.clock
    assert node.node_id in kernel_state["Canonical"]["History"]


def test_2pc_payload_len_mismatch_triggers_abort():
    """Verify PrepareError and automatic abort when Phase A payload_len header mismatches."""
    engine = PhaseAWALEngineMock()
    engine.corrupt_next_prepare_len = True

    node = CAENode(
        node_id="node-test-len",
        title="Test Payload Len Mismatch",
        causes=[Condition("session.state", "EQ", "EXPIRED")],
        action="reject",
        effects=[Condition("tx.status", "EQ", "ABORTED")],
        raw_text="raw text",
        provenance={"pos": 0, "phase": 1, "token_score": 0.9},
        scope={"scope_id": "scope-01", "lamport_clock": 5},
    )

    with pytest.raises(PrepareError, match="Payload length mismatch"):
        prepare_commit_payload(engine, node)

    # Verify transaction was safely cleaned up/aborted in Phase A
    assert len(engine.active_transactions) == 0


def test_2pc_crc_failure_triggers_abort():
    """Verify PrepareError when Phase A reports BAD CRC on prepared record."""
    engine = PhaseAWALEngineMock()
    engine.fail_next_prepare_crc = True

    node = CAENode(
        node_id="node-test-crc",
        title="Test CRC Failure",
        causes=[Condition("memory.state", "EQ", "DIRTY")],
        action="quarantine",
        effects=[Condition("memory.state", "EQ", "PERSISTED")],
        raw_text="raw text",
        provenance={"pos": 1, "phase": 1, "token_score": 0.85},
        scope={"scope_id": "scope-01", "lamport_clock": 2},
    )

    with pytest.raises(PrepareError, match="CRC failure"):
        prepare_commit_payload(engine, node)

    assert len(engine.active_transactions) == 0


def test_phase_a_recover_truncates_uncommitted_prepare():
    """
    Simulates crash recovery scenario:
    Prepare succeeds, but process crashes before commit. Phase A recover()
    must truncate uncommitted PREPARED records upon startup.
    """
    engine = PhaseAWALEngineMock()

    node = CAENode(
        node_id="node-test-crash",
        title="Crash Before Commit Test",
        causes=[Condition("kernel.execution", "EQ", "RUNNING")],
        action="commit",
        effects=[Condition("kernel.execution", "EQ", "PAUSED")],
        raw_text="raw text",
        provenance={"pos": 2, "phase": 1, "token_score": 0.99},
        scope={"scope_id": "scope-01", "lamport_clock": 12},
    )

    # Prepare succeeds
    prep = prepare_commit_payload(engine, node)
    txid = prep["txid"]

    # Process crashes here -> finalize_commit is NEVER called!
    assert txid in engine.active_transactions

    # System restarts -> Phase A runs recover()
    rec_res = engine.recover()

    assert rec_res["status"] == "OK"
    assert rec_res["truncated_records"] == 1
    assert rec_res["recovered_records"] == 0
    assert len(engine.wal_log) == 0  # Uncommitted PREPARED record removed
