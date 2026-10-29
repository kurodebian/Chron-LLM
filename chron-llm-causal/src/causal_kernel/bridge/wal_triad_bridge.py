"""
wal_triad_bridge.py — G-02 bridge adapter (A1).

Binds the WAL triad record_id / txid / event_id onto WAL frames WITHOUT ever
touching the payload:

  HASH        = SHA256(JCS(payload))            # payload immutable, envelope NOT in hash
  RID         = "RID-"  + sha256hex(JCS(frame identity tuple))   # physical frame identity
  TXID        = int, supplied by the transaction engine          # atomicity unit
  EID         = "EID-"  + sha256hex(f"{txid}|v1|{content_hash}") # logical event identity

Invariants (STEP-24, 1-74.md:3936/4019-30/4055-56):
  I1 NON_UNIFIABLE : RID != TXID != EID, unforgeable by prefix+type discipline
  I2 DUP_REJECT    : duplicate record_id -> WAL_RECORD_ID_DUPLICATE, frame rejected
  I3 CONFLICT-HALT : same txid + differing payload digest -> HALT (sticky, fail-closed)
  I4 REPLAY-IDEMPOTENT : repeated identical/committed frames never duplicate canonical effect

State semantics:
  PREPARED  = IN_DOUBT   (isolated: never in canonical view or replay set)
  COMMITTED = CANONICAL  (one effect per txid; first commit wins)
  ABORTED   = DROP       (frame dropped; txid digest tombstone kept for I3)

Disciplines: MISSING_EVIDENCE != PASS (IN_DOUBT is not committed; no phantom effect).
Read-only with respect to extractor/ and contracts/: no payload mutation, no re-hashing,
no Lean writes. BANS honored: extractor/** unmodified, contracts/** unmodified.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, Optional

__all__ = [
    "jcs_bytes",
    "content_hash",
    "make_envelope",
    "WALTriadIndex",
    "TriadViolation",
    "RecordDuplicateError",
    "ConflictHaltError",
    "FrameTypeViolation",
]

_ENVELOPE_VERSION = "1"
_FRAME_TYPES = ("PREPARED", "COMMITTED", "ABORTED")


# --------------------------------------------------------------------- hashing
def jcs_bytes(obj: Any) -> bytes:
    """JCS-style canonical JSON (sort_keys, no insignificant whitespace, UTF-8).
    Independently implemented; byte-equivalence with the extractor's
    canonical_json_bytes is pinned by test (cross-check, read-only)."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def content_hash(payload: Any) -> str:
    """SHA256 over JCS(payload). Envelope fields are NEVER hash inputs."""
    return hashlib.sha256(jcs_bytes(payload)).hexdigest()


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ------------------------------------------------------------------- envelope
def make_envelope(
    txid: int,
    payload: Any,
    frame_type: str,
    sequence: Optional[int] = None,
    authority_ref: Optional[int] = None,
) -> Dict[str, Any]:
    """Build the triad envelope for one WAL frame. Payload is read-only."""
    if not isinstance(txid, int) or isinstance(txid, bool) or txid <= 0:
        # I1: TXID is a strictly-integer namespace; string IDs can never masquerade.
        raise FrameTypeViolation(f"TXID must be a positive int, got {txid!r}")
    if frame_type not in _FRAME_TYPES:
        raise FrameTypeViolation(f"frame_type must be one of {_FRAME_TYPES}")

    h = content_hash(payload)
    L = len(jcs_bytes(payload))

    # RID: physical frame identity (design: JCS over the frame-header tuple).
    # 'sequence' is a frame-header field, hence a RID input; 'authority_ref' is
    # a metadata mirror, deliberately NOT a RID input. A byte-identical replay
    # (same sequence) collides on RID (I2); a recovery re-log with a new
    # sequence is a distinct physical frame guarded by the I4 canonical effect.
    frame_identity = {
        "txid": txid,
        "payload_len": L,
        "content_hash": h,
        "frame_type": frame_type,
        "sequence": sequence,
    }
    record_id = "RID-" + _sha256_hex(jcs_bytes(frame_identity))

    # EID: logical event identity, one per (txid, payload) pair, version-salted.
    # Explicit '|' delimiter removes concatenation ambiguity.
    event_id = "EID-" + _sha256_hex(f"{txid}|v1|{h}".encode("utf-8"))

    # I1 runtime assertion: the three namespaces are pairwise disjoint by
    # construction (int vs 'RID-' vs 'EID-'); guard anyway.
    rid_s, eid_s = str(record_id), str(event_id)
    if rid_s == eid_s or rid_s == str(txid) or eid_s == str(txid):
        raise FrameTypeViolation(f"I1 NON_UNIFIABLE violated: {rid_s}/{txid}/{eid_s}")

    return {
        "envelope_version": _ENVELOPE_VERSION,
        "record_id": record_id,
        "txid": txid,
        "event_id": event_id,
        "content_hash": h,
        "payload_len": L,
        "frame_type": frame_type,
        "sequence": sequence,
        "authority_ref": authority_ref,
    }


# ------------------------------------------------------------------ violations
class TriadViolation(Exception):
    """Base for triad-bridge invariant violations."""


class RecordDuplicateError(TriadViolation):
    """I2: WAL_RECORD_ID_DUPLICATE — frame rejected, index state unchanged."""


class ConflictHaltError(TriadViolation):
    """I3: TXID_PAYLOAD_CONFLICT — index enters sticky HALT; no further accepts."""


class FrameTypeViolation(TriadViolation):
    """Malformed frame input (type/txid namespace violation; I1 guard)."""


# --------------------------------------------------------------------- index
class WALTriadIndex:
    """Append-only validator over WAL frames enforcing I1..I4 and state isolation.

    canonical_frames(): COMMITTED effects, exactly one envelope per txid
    in_doubt_frames():  PREPARED frames pending resolution (isolated)
    aborted_frames():   ABORTED frames (dropped from canonical; digest tombstones kept)
    """

    def __init__(self) -> None:
        self._frames: Dict[str, Dict[str, Any]] = {}      # record_id -> envelope
        self._txid_digest: Dict[int, str] = {}            # txid -> content_hash (tombstone-proof)
        self._committed: Dict[int, Dict[str, Any]] = {}   # txid -> first COMMITTED envelope
        self._in_doubt: Dict[str, Dict[str, Any]] = {}    # record_id -> envelope
        self._aborted: Dict[str, Dict[str, Any]] = {}     # record_id -> envelope
        self.halted = False
        self._halt_reason: Optional[str] = None

    # -- public
    def attach(
        self,
        txid: int,
        payload: Any,
        frame_type: str,
        sequence: Optional[int] = None,
        authority_ref: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Validate + index one frame. Payload bytes are never modified."""
        if self.halted:
            # fail-closed: after I3 nothing is accepted until external recovery.
            raise ConflictHaltError(f"HALT: {self._halt_reason}")

        snapshot = copy.deepcopy(payload)
        env = make_envelope(txid, payload, frame_type, sequence, authority_ref)
        # payload immutability guard (HASH: ENVELOPE∉HASH, payload untouched)
        if jcs_bytes(snapshot) != jcs_bytes(payload):
            raise TriadViolation("payload mutated during envelope construction")

        rid = env["record_id"]

        # I2: duplicate physical frame -> reject, state unchanged
        if rid in self._frames:
            raise RecordDuplicateError(f"WAL_RECORD_ID_DUPLICATE: {rid}")

        # I3: same txid, different payload digest -> HALT (sticky)
        known = self._txid_digest.get(txid)
        if known is not None and known != env["content_hash"]:
            self.halted = True
            self._halt_reason = (
                f"TXID_PAYLOAD_CONFLICT txid={txid} "
                f"known={known[:16]}.. new={env['content_hash'][:16]}.."
            )
            raise ConflictHaltError(self._halt_reason)

        # register
        self._frames[rid] = env
        self._txid_digest.setdefault(txid, env["content_hash"])

        if frame_type == "PREPARED":
            self._in_doubt[rid] = env
        elif frame_type == "ABORTED":
            self._aborted[rid] = env
            # IN_DOUBT resolution by abort: pending PREPARED frames for this txid
            # leave the in_doubt set (ABORTED=DROP), digest tombstone retained.
            for r in [r for r, e in self._in_doubt.items() if e["txid"] == txid]:
                del self._in_doubt[r]
        else:  # COMMITTED — I4: canonical effect exactly once per txid
            self._in_doubt = {
                r: e for r, e in self._in_doubt.items() if e["txid"] != txid
            }
            if txid not in self._committed:
                self._committed[txid] = env
            # else: replay of an already-applied txid — frame recorded as
            # physical evidence, canonical effect NOT duplicated (I4).

        return env

    # -- views
    def canonical_frames(self):
        """CANONICAL set: one envelope per committed txid (replay-idempotent)."""
        return list(self._committed.values())

    def in_doubt_frames(self):
        """IN_DOUBT set: PREPARED frames pending resolution. Never canonical."""
        return list(self._in_doubt.values())

    def aborted_frames(self):
        return list(self._aborted.values())

    def is_in_doubt(self, txid: int) -> bool:
        return any(e["txid"] == txid for e in self._in_doubt.values())

    def is_committed(self, txid: int) -> bool:
        return txid in self._committed

    def replay_set(self):
        """Recover(H) basis: committed txids only; IN_DOUBT excluded."""
        return sorted(self._committed)
