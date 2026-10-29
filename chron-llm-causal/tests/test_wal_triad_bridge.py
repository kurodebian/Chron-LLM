"""
test_wal_triad_bridge.py — G-02 A1 gate tests.

Required gates (directive): DISTINCT, DUP_REJECT, CONFLICT, REPLAY, HASH_STABLE, IN_DOUBT.
Read-only toward extractor/**: import used solely to pin JCS byte-equivalence.
"""

import copy

import pytest

from causal_kernel.bridge.wal_triad_bridge import (
    ConflictHaltError,
    FrameTypeViolation,
    RecordDuplicateError,
    WALTriadIndex,
    content_hash,
    jcs_bytes,
    make_envelope,
)
from causal_kernel.extractor.cae_extractor_v1 import (  # read-only cross-check
    canonical_json_bytes,
)

PAYLOAD = {
    "schema_version": 2,
    "nodes": [{"id": "N1", "text": "causal-edge vocabulary", "type": "claim"}],
    "edges": [],
    "source_ref": {"chapter": 53, "file": "1-74.md"},
}


def frame(txid, payload=None, frame_type="PREPARED", **kw):
    return make_envelope(txid, payload if payload is not None else copy.deepcopy(PAYLOAD), frame_type, **kw)


# ---------------------------------------------------------------- DISTINCT (I1)
def test_distinct_rid_txid_eid():
    env = frame(1001)
    rid, txid, eid = env["record_id"], env["txid"], env["event_id"]
    assert rid != str(txid) != eid and rid != eid
    assert rid.startswith("RID-") and eid.startswith("EID-")
    assert isinstance(txid, int)
    # namespace injection guard: string "txid" can never unify with the int namespace
    with pytest.raises(FrameTypeViolation):
        make_envelope("RID-abc", PAYLOAD, "PREPARED")  # type: ignore[arg-type]
    # EID deterministic per (txid, payload); RID deterministic per frame tuple
    assert frame(1001)["event_id"] == env["event_id"]
    assert frame(1001, frame_type="COMMITTED")["event_id"] == env["event_id"]
    assert frame(1001, frame_type="COMMITTED")["record_id"] != env["record_id"]
    # different payload -> different EID
    other = copy.deepcopy(PAYLOAD)
    other["nodes"][0]["text"] = "changed"
    assert frame(1001, other)["event_id"] != env["event_id"]


# ------------------------------------------------------------- DUP_REJECT (I2)
def test_dup_reject():
    idx = WALTriadIndex()
    idx.attach(10, copy.deepcopy(PAYLOAD), "PREPARED")
    with pytest.raises(RecordDuplicateError):
        idx.attach(10, copy.deepcopy(PAYLOAD), "PREPARED")  # identical frame -> RID dup
    # rejection left state unchanged: still exactly one frame indexed
    assert len(idx.in_doubt_frames()) == 1
    assert not idx.halted


# --------------------------------------------------------------- CONFLICT (I3)
def test_conflict_halt_sticky():
    idx = WALTriadIndex()
    idx.attach(20, copy.deepcopy(PAYLOAD), "PREPARED")
    mutated = copy.deepcopy(PAYLOAD)
    mutated["nodes"] = []
    with pytest.raises(ConflictHaltError):
        idx.attach(20, mutated, "COMMITTED")
    assert idx.halted
    # fail-closed: nothing accepted after HALT, even unrelated txids
    with pytest.raises(ConflictHaltError):
        idx.attach(21, copy.deepcopy(PAYLOAD), "PREPARED")
    assert idx.canonical_frames() == []


# ----------------------------------------------------------------- REPLAY (I4)
def test_replay_idempotent():
    idx = WALTriadIndex()
    p = copy.deepcopy(PAYLOAD)
    idx.attach(30, copy.deepcopy(p), "PREPARED")
    first = idx.attach(30, copy.deepcopy(p), "COMMITTED", sequence=1)
    # recovery re-log: same txid+digest, new frame-header sequence ->
    # distinct RID, accepted as physical evidence
    second = idx.attach(30, copy.deepcopy(p), "COMMITTED", sequence=2)
    assert second["record_id"] != first["record_id"]
    # canonical effect exactly once per txid
    canonical = idx.canonical_frames()
    assert len(canonical) == 1 and canonical[0]["txid"] == 30
    assert idx.replay_set() == [30]
    # byte-identical replay (same sequence) is RID-duplicated (I2) -> no double effect
    with pytest.raises(RecordDuplicateError):
        idx.attach(30, copy.deepcopy(p), "COMMITTED", sequence=2)
    assert len(idx.canonical_frames()) == 1


# ----------------------------------------------------------- HASH_STABLE (envelope∉hash)
def test_hash_stable():
    idx = WALTriadIndex()
    payload = copy.deepcopy(PAYLOAD)
    before = jcs_bytes(payload)
    env = idx.attach(40, payload, "PREPARED", sequence=None, authority_ref=3)
    # payload unmutated by envelope construction
    assert jcs_bytes(payload) == before
    # HASH = SHA256(JCS(payload)); envelope fields are not hash inputs
    assert env["content_hash"] == content_hash(PAYLOAD)
    # varying envelope metadata never moves the hash
    env2 = idx.attach(41, copy.deepcopy(PAYLOAD), "COMMITTED", sequence=9, authority_ref=None)
    assert env2["content_hash"] == env["content_hash"]
    assert env2["payload_len"] == env["payload_len"]
    # JCS byte-equivalence with extractor canonicalization (read-only pin)
    assert jcs_bytes(PAYLOAD) == canonical_json_bytes(PAYLOAD)


# -------------------------------------------------------------- IN_DOUBT isolation
def test_in_doubt_isolation():
    idx = WALTriadIndex()
    idx.attach(50, copy.deepcopy(PAYLOAD), "PREPARED")
    # PREPARED = IN_DOUBT: isolated from canonical and replay
    assert idx.is_in_doubt(50)
    assert idx.canonical_frames() == []
    assert idx.replay_set() == []
    # COMMITTED = CANONICAL: leaves in_doubt
    idx.attach(50, copy.deepcopy(PAYLOAD), "COMMITTED")
    assert not idx.is_in_doubt(50)
    assert idx.is_committed(50)
    assert idx.replay_set() == [50]
    # ABORTED = DROP: pending prepared removed, digest tombstone kept
    idx.attach(60, copy.deepcopy(PAYLOAD), "PREPARED")
    idx.attach(60, copy.deepcopy(PAYLOAD), "ABORTED")
    assert not idx.is_in_doubt(60)
    assert not idx.is_committed(60)
    assert len(idx.aborted_frames()) == 1
    assert 60 not in idx.replay_set()
    # tombstone still guards I3 after drop
    mutated = copy.deepcopy(PAYLOAD)
    mutated["schema_version"] = 99
    with pytest.raises(ConflictHaltError):
        idx.attach(60, mutated, "PREPARED")
