"""
test_canonical_history_join.py — Canonical ↔ History comparison path.

Ratified norms (RATIFIED_HUMAN 2026-11-11):
  ADR-001: PREPARED stays IN_DOUBT; never canonical, never in replay set.
  ADR-003: transaction-index claims hold in local scope until a Canonical-History
           comparison path exists; MISSING_EVIDENCE != PASS (fail-closed verdict).
  ADR-004: the fail-closed bridge is canonical authority.

Gates pinned here: JOIN_AGREED, JOIN_MISSING (committed without canonical effect),
JOIN_PHANTOM (canonical effect without commit — incl. IN_DOUBT leakage),
JOIN_HALTED (sticky fail-closed), RECOVER_REBUILD (Canonical reconstructible from
durable COMMITTED frames only, idempotent).
"""

import pytest
from causal_kernel.bridge.wal_triad_bridge import (
    ConflictHaltError,
    WALTriadIndex,
    join_canonical_history,
    recover_canonical,
)


def _index_with(*frames):
    idx = WALTriadIndex()
    for txid, payload, frame_type, seq in frames:
        idx.attach(txid, payload, frame_type, sequence=seq)
    return idx


def test_join_agreed_when_history_matches_committed():
    idx = _index_with(
        (1, {"node": "A"}, "PREPARED", None),
        (2, {"node": "B"}, "PREPARED", None),
        (2, {"node": "B"}, "COMMITTED", 1),
    )
    report = join_canonical_history(idx, [2])
    assert report["verdict"] == "AGREED"
    assert report["committed_txids"] == [2]
    assert report["in_doubt_txids"] == [1]
    assert report["missing_effects"] == []
    assert report["phantom_effects"] == []


def test_join_divergent_on_missing_effect():
    idx = _index_with((3, {"node": "C"}, "COMMITTED", 1))
    report = join_canonical_history(idx, [])
    # MISSING_EVIDENCE != PASS: committed txid absent from canonical history
    assert report["verdict"] == "DIVERGENT"
    assert report["missing_effects"] == [3]


def test_join_divergent_on_in_doubt_phantom():
    idx = _index_with((4, {"node": "D"}, "PREPARED", None))
    # An IN_DOUBT txid appearing in canonical history is a phantom effect (ADR-001)
    report = join_canonical_history(idx, [4])
    assert report["verdict"] == "DIVERGENT"
    assert report["phantom_effects"] == [4]
    assert report["in_doubt_txids"] == [4]


def test_join_halted_is_fail_closed():
    idx = WALTriadIndex()
    idx.attach(5, {"node": "E"}, "PREPARED", None)
    with pytest.raises(ConflictHaltError):
        idx.attach(5, {"node": "F"}, "COMMITTED", 1)
    report = join_canonical_history(idx, [])
    assert report["verdict"] == "HALTED"
    assert report["missing_effects"] == []  # never PASS from a halted index


def test_recover_rebuilds_canonical_from_committed_only():
    idx = _index_with(
        (1, {"node": "A"}, "PREPARED", None),
        (2, {"node": "B"}, "PREPARED", None),
        (2, {"node": "B"}, "COMMITTED", 1),
        (3, {"node": "C"}, "PREPARED", None),
        (3, {"node": "C"}, "ABORTED", None),
    )
    rec = recover_canonical(idx)
    assert rec["canonical_txids"] == [2]
    assert rec["replay_set"] == [2]
    assert rec["in_doubt_txids"] == [1]
    assert rec["sequence_basis"] == 1
    assert len(rec["effects"]) == 1  # I4: exactly one canonical effect per txid
    assert rec["halted"] is False


def test_recover_is_idempotent_and_rebuildable():
    idx = _index_with(
        (7, {"node": "G"}, "COMMITTED", 1),
        (8, {"node": "H"}, "COMMITTED", 2),
        (9, {"node": "I"}, "PREPARED", None),
    )
    r1 = recover_canonical(idx)
    r2 = recover_canonical(idx)
    assert r1 == r2
    # Canonical is reconstructible from the durable committed frames alone:
    # re-attaching those frames into a fresh index yields the same canonical set.
    rebuilt = WALTriadIndex()
    for env in r1["effects"]:
        rebuilt.attach(env["txid"], {"node": env["txid"]}, "COMMITTED",
                       sequence=env["sequence"])
    # (payload identity is pinned by the digest gate below, not by node text)
    assert rebuilt.replay_set() == r1["canonical_txids"]
    assert join_canonical_history(idx, r1["canonical_txids"])["verdict"] == "AGREED"


def test_recover_digest_pin_from_frames():
    # The effect envelopes carry content_hash; canonical reconstruction must
    # reproduce the same digests as the original payloads (payload immutable).
    payload = {"node": "X", "causes": [{"k": "s", "op": "EQ", "v": "ON"}]}
    idx = _index_with((11, payload, "COMMITTED", 1))
    rec = recover_canonical(idx)
    env = rec["effects"][0]
    from causal_kernel.bridge.wal_triad_bridge import content_hash
    assert env["content_hash"] == content_hash(payload)
