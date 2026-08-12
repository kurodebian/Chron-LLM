#!/usr/bin/env python3
# cae_extractor.py
# Phase B extractor with 2PC prepare/commit flow for Phase A (R2.1-D compliant).
# - prepare_commit_payload(...) -> calls Phase A prepare, returns txid + prepared rec
# - finalize_commit(txid) -> calls Phase A commit, handles LamportClock update hooks
# - abort_tx(txid) -> calls Phase A abort
#
# Notes:
# - Phase A is expected to implement prepare(txid, payload)->(rec, OK) and commit(txid)->(rec,OK),
#   abort(txid)->(rec,OK), and recover() per R2.1-D.
# - content_hash is SHA-256 over JCS/RFC8785 canonical JSON bytes; payload_len is exact byte length.
# - This module is intentionally implementation-agnostic about Phase A transport (HTTP/gRPC/local API).
# - Replace llm_fallback_extract stub with real LLM Structured Output in production.

from __future__ import annotations
import re
import json
import hashlib
import math
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Any


# ---------------------------------------------------------------------
# 0. Exceptions
# ---------------------------------------------------------------------
class PrepareError(RuntimeError):
    pass


class CommitError(RuntimeError):
    pass


class AbortError(RuntimeError):
    pass


# ---------------------------------------------------------------------
# 1. Kernel state vocabulary (seed). Populate from docs__ir__06-kernel-state-machine.spec.
# ---------------------------------------------------------------------
STATE_VOCAB: Dict[str, List[str]] = {
    "session.state": ["AUTHENTICATED", "UNAUTHENTICATED", "EXPIRED", "LOCKED"],
    "tx.status": [
        "STAGED",
        "MOVED",
        "COMMITTED",
        "PUBLISHED",
        "QUARANTINED",
        "ABORTED",
    ],
    "memory.state": ["CLEAN", "DIRTY", "FLUSHING", "PERSISTED"],
    "kernel.execution": ["IDLE", "RUNNING", "PAUSED", "PANIC", "RECOVERING"],
    "auth.token": ["VALID", "INVALID", "REVOKED", "ABSENT"],
}
VALID_VARIABLES = set(STATE_VOCAB.keys())


# ---------------------------------------------------------------------
# 2. Data classes
# ---------------------------------------------------------------------
@dataclass
class Condition:
    variable: str
    op: str
    value: str

    def to_dict(self) -> Dict[str, Any]:
        return {"variable": self.variable, "op": self.op, "value": self.value}


@dataclass
class CAENode:
    node_id: str
    title: str
    causes: List[Condition]
    action: str
    effects: List[Condition]
    raw_text: str
    provenance: Dict[str, Any]
    scope: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def canonical_payload(self) -> Dict[str, Any]:
        """
        Build canonical payload dict according to schema guidance.
        Arrays preserve extractor order; object keys will be sorted at serialization.
        """
        node_obj = {
            "node_id": self.node_id,
            "title": self.title,
            "causes": [c.to_dict() for c in self.causes],
            "action": self.action,
            "effects": [e.to_dict() for e in self.effects],
            "raw_text": self.raw_text,
            "provenance": {
                "pos": int(self.provenance.get("pos", 0)),
                "phase": int(self.provenance.get("phase", 0)),
                "token_score": float(self.provenance.get("token_score", 0.0)),
            },
            "scope": {
                "scope_id": str(self.scope.get("scope_id", "")),
                "lamport_clock": int(self.scope.get("lamport_clock", 0)),
            },
            "metadata": {k: self.metadata[k] for k in sorted(self.metadata.keys())},
        }
        payload = {
            "canonical_clock": int(self.scope.get("lamport_clock", 0)),
            "node": node_obj,
        }
        return payload


# ---------------------------------------------------------------------
# 3. Canonicalization & Hashing (JCS / RFC 8785 style)
# ---------------------------------------------------------------------
def canonical_json_bytes(obj: Any) -> bytes:
    """
    Deterministic JSON serialization:
    - sort_keys=True ensures object keys are lexicographically ordered
    - separators=(',', ':') removes insignificant whitespace
    - ensure_ascii=False preserves UTF-8
    Arrays preserve order as provided by the extractor.
    """
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def compute_content_hash_and_len(node: CAENode) -> Tuple[str, int]:
    """
    Returns (sha256_hex_lowercase, payload_len_bytes)
    payload_len is the exact byte length of the canonical JSON bytes.
    """
    payload = node.canonical_payload()
    b = canonical_json_bytes(payload)
    h = hashlib.sha256(b).hexdigest()
    return h, len(b)


# ---------------------------------------------------------------------
# 4. Rule-based extractor (unchanged core, but kept here for completeness)
# ---------------------------------------------------------------------
RULES: List[Tuple[re.Pattern, str]] = [
    (
        re.compile(
            r"(?:\bif\b|\bwhen\b|\bgiven\b)\s+(?P<var>[\w\.]+)\s*(?:==|=|is)\s*(?P<val>[\w\-]+)",
            re.I,
        ),
        "cause_assign",
    ),
    (
        re.compile(r"(?:\bif\b|\bwhen\b|\bgiven\b)\s+(?P<cause>[^,.;。]+)", re.I),
        "cause_text",
    ),
    (
        re.compile(
            r"(?:\bthen\b|\bresult\b|\bso that\b)\s*(?:set\s+)?(?P<var>[\w\.]+)\s*(?:=|to)\s*(?P<val>[\w\-]+)",
            re.I,
        ),
        "effect_assign",
    ),
    (
        re.compile(r"(?:\bthen\b|\bresult\b)\s+(?P<effect>[^,.;。]+)", re.I),
        "effect_text",
    ),
    (
        re.compile(
            r"\b(commit|reject|defer|retry|abort|quarantine|publish|move)\b", re.I
        ),
        "action_verb",
    ),
    (re.compile(r"memory-write:(?P<target>\w+)=(?P<val>\w+)", re.I), "memory_write"),
]


def normalize_variable(var_candidate: str) -> str:
    cleaned = var_candidate.strip().lower()
    if cleaned in VALID_VARIABLES:
        return cleaned
    aliases = {"session": "session.state", "tx": "tx.status", "memory": "memory.state"}
    if cleaned in aliases:
        return aliases[cleaned]
    cleaned = cleaned.replace(" ", "_").replace("-", "_")
    return f"custom.{cleaned}"


CONFIDENCE_BASE = 0.4
CONFIDENCE_PER_MATCH = 0.2


def rule_based_extract(
    text: str, pos: int, phase: int, score: float, scope_id: str, lamport_clock: int
) -> Tuple[Optional[CAENode], float]:
    causes: List[Condition] = []
    effects: List[Condition] = []
    action: str = "noop"
    matched = 0

    sentences = re.split(r"[。\.；;]", text)
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        for pattern, kind in RULES:
            m = pattern.search(s)
            if not m:
                continue
            matched += 1
            gd = m.groupdict()
            if kind == "cause_assign":
                var = normalize_variable(gd["var"])
                val = gd["val"].upper()
                causes.append(Condition(variable=var, op="EQ", value=val))
            elif kind == "cause_text":
                causes.append(
                    Condition(
                        variable="custom.condition",
                        op="IS_TRUE",
                        value=gd["cause"].strip(),
                    )
                )
            elif kind == "effect_assign":
                var = normalize_variable(gd["var"])
                val = gd["val"].upper()
                effects.append(Condition(variable=var, op="EQ", value=val))
            elif kind == "effect_text":
                effects.append(
                    Condition(
                        variable="custom.effect",
                        op="IS_TRUE",
                        value=gd["effect"].strip(),
                    )
                )
            elif kind == "action_verb":
                action = m.group(0).lower()
            elif kind == "memory_write":
                tgt = normalize_variable("memory." + gd["target"])
                effects.append(
                    Condition(variable=tgt, op="EQ", value=gd["val"].upper())
                )

    if matched == 0:
        return None, 0.0

    confidence = min(1.0, CONFIDENCE_BASE + matched * CONFIDENCE_PER_MATCH)
    node = CAENode(
        node_id=f"node-{phase:02d}-{pos:04d}",
        title=(text[:200].strip()),
        causes=causes
        or [Condition(variable="system.state", op="IS_TRUE", value="TRUE")],
        action=action,
        effects=effects,
        raw_text=text,
        provenance={"pos": pos, "phase": phase, "token_score": float(score)},
        scope={"scope_id": scope_id, "lamport_clock": int(lamport_clock)},
        metadata={"extraction_method": "rule_based"},
    )
    return node, confidence


# ---------------------------------------------------------------------
# 5. LLM fallback (stub)
# ---------------------------------------------------------------------
def llm_fallback_extract(
    text: str, pos: int, phase: int, score: float, scope_id: str, lamport_clock: int
) -> CAENode:
    node = CAENode(
        node_id=f"node-fallback-{phase:02d}-{pos:04d}",
        title=(text[:200].strip()),
        causes=[Condition(variable="session.state", op="EQ", value="AUTHENTICATED")],
        action="commit",
        effects=[Condition(variable="tx.status", op="EQ", value="COMMITTED")],
        raw_text=text,
        provenance={"pos": pos, "phase": phase, "token_score": float(score)},
        scope={"scope_id": scope_id, "lamport_clock": int(lamport_clock)},
        metadata={"extraction_method": "llm_fallback"},
    )
    return node


CONFIDENCE_THRESHOLD = 0.75


def run_extraction_pipeline(
    text: str, pos: int, phase: int, score: float, scope_id: str, lamport_clock: int
) -> Tuple[CAENode, float]:
    node, confidence = rule_based_extract(
        text, pos, phase, score, scope_id, lamport_clock
    )
    if node and confidence >= CONFIDENCE_THRESHOLD:
        return node, confidence
    node = llm_fallback_extract(text, pos, phase, score, scope_id, lamport_clock)
    return node, 0.95


# ---------------------------------------------------------------------
# 6. Phase A 2PC integration helpers
# ---------------------------------------------------------------------
# Phase A engine interface expectations (duck-typed):
# - prepare(payload: bytes or dict) -> {"txid": <int|string>, "rec": <record dict>, "status": "OK"|"CORRUPT"|...}
# - commit(txid) -> {"rec": <record dict>, "status": "OK"|"CORRUPT"|...}
# - abort(txid) -> {"rec": <record dict>, "status": "OK"|"CORRUPT"|...}
# - recover() -> {"status": "OK"|"TRUNCATED"|...}


def prepare_commit_payload(phase_a_engine: Any, node: CAENode) -> Dict[str, Any]:
    """
    1) Build canonical payload, compute content_hash and payload_len
    2) Call phase_a_engine.prepare(txid=None, payload=bytes_or_dict) -> returns txid and rec
       (Phase A issues txid)
    3) Validate returned rec (payload_len, crc if provided)
    Returns dict: {"txid": txid, "rec": rec, "content_hash": h, "payload_len": L}
    Raises PrepareError on failure.
    """
    # compute canonical payload and hash/len
    content_hash, payload_len = compute_content_hash_and_len(node)

    # Build the payload dict that Phase A expects (we send canonical payload)
    payload_dict = node.canonical_payload()
    # Attach content_hash and payload_len as metadata for Phase A header verification
    payload_dict["_meta"] = {"content_hash": content_hash, "payload_len": payload_len}

    # Call Phase A prepare. Phase A should return txid and prepared record.
    res = phase_a_engine.prepare(payload_dict)  # duck-typed API
    if not res or res.get("status") not in ("OK",):
        raise PrepareError(f"Phase A prepare failed: {res}")

    txid = res.get("txid")
    rec = res.get("rec")

    # Validate rec payload_len if Phase A returns it
    hdr_payload_len = None
    if rec and isinstance(rec, dict):
        hdr = rec.get("hdr", {})
        hdr_payload_len = hdr.get("payload_len")
    if hdr_payload_len is not None and hdr_payload_len != payload_len:
        # mismatch -> abort and raise
        try:
            phase_a_engine.abort(txid)
        except Exception:
            pass
        raise PrepareError(
            f"Payload length mismatch: local={payload_len} header={hdr_payload_len}"
        )

    # Optionally validate CRC if rec contains crc/status
    if rec and rec.get("crc_status") == "BAD":
        try:
            phase_a_engine.abort(txid)
        except Exception:
            pass
        raise PrepareError("Phase A reported CRC failure on prepared record")

    return {
        "txid": txid,
        "rec": rec,
        "content_hash": content_hash,
        "payload_len": payload_len,
    }


def finalize_commit(
    phase_a_engine: Any, txid: Any, kernel_apply_hook: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Call Phase A commit(txid). On success, Phase A will apply_sm() and update header.clock.
    kernel_apply_hook (optional) is a callable invoked after commit to update Phase B's Kernel state:
      kernel_apply_hook(rec) -> should update Canonical.History and LamportClock locally.
    Returns commit result dict.
    Raises CommitError on failure.
    """
    res = phase_a_engine.commit(txid)
    if not res or res.get("status") not in ("OK",):
        # try abort as fallback
        try:
            phase_a_engine.abort(txid)
        except Exception:
            pass
        raise CommitError(f"Phase A commit failed: {res}")

    rec = res.get("rec")
    # Optionally call kernel_apply_hook to reflect apply_sm() side-effects in Phase B
    if kernel_apply_hook:
        try:
            kernel_apply_hook(rec)
        except Exception as e:
            # kernel hook failure is serious but commit already happened; surface error
            raise CommitError(f"Kernel apply hook failed after commit: {e}")

    return res


def abort_tx(phase_a_engine: Any, txid: Any) -> Dict[str, Any]:
    """
    Abort a prepared txid. Returns Phase A abort result or raises AbortError.
    """
    res = phase_a_engine.abort(txid)
    if not res or res.get("status") not in ("OK",):
        raise AbortError(f"Phase A abort failed: {res}")
    return res


# ---------------------------------------------------------------------
# 7. Example Kernel apply hook (user should implement real logic)
# ---------------------------------------------------------------------
def example_kernel_apply_hook(
    rec: Dict[str, Any], kernel_state: Dict[str, Any]
) -> None:
    """
    Apply the committed record to local kernel state:
    - Append events to Canonical.History
    - Increment LamportClock to match header.clock if provided
    This is a simple example; real implementation must follow Kernel invariants.
    """
    hdr = rec.get("hdr", {})
    payload = rec.get("payload")
    # Append to history if payload contains events (domain-specific)
    events = payload.get("node", {}).get("causes", []) if payload else []
    kernel_state.setdefault("Canonical", {}).setdefault("History", []).extend(events)
    # Update LamportClock if header.clock present
    header_clock = hdr.get("clock")
    if header_clock is not None:
        kernel_state.setdefault("Canonical", {})["LamportClock"] = int(header_clock)


# ---------------------------------------------------------------------
# 8. CLI demo / local test harness (lightweight)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    # Minimal in-memory Phase A mock implementing prepare/commit/abort/recover
    class PhaseAMock:
        def __init__(self):
            self.wal = []
            self.next_txid = 1
            self.records = {}  # txid -> rec

        def prepare(self, payload_dict):
            txid = self.next_txid
            self.next_txid += 1
            # simulate header and rec
            payload_bytes = canonical_json_bytes(payload_dict)
            rec = {
                "hdr": {
                    "type": "PREPARED",
                    "txid": txid,
                    "payload_len": len(payload_bytes),
                    "clock": 0,
                },
                "payload": payload_dict,
                "crc_status": "OK",
            }
            self.records[txid] = rec
            return {"txid": txid, "rec": rec, "status": "OK"}

        def commit(self, txid):
            rec = self.records.get(txid)
            if not rec:
                return {"status": "CORRUPT"}
            # simulate apply_sm and lamport clock increment
            rec["hdr"]["type"] = "COMMITTED"
            rec["hdr"]["clock"] = rec["hdr"].get("clock", 0) + 1
            self.wal.append(rec)
            return {"rec": rec, "status": "OK"}

        def abort(self, txid):
            rec = self.records.get(txid)
            if not rec:
                return {"status": "CORRUPT"}
            rec["hdr"]["type"] = "ABORTED"
            return {"rec": rec, "status": "OK"}

        def recover(self):
            # simplistic: check CRC and return OK
            return {"status": "OK"}

    # Demo extraction + 2PC
    sample_text = "If session.state == AUTHENTICATED then set tx.status = COMMITTED with commit action"
    node, conf = run_extraction_pipeline(
        sample_text, pos=1, phase=2, score=0.98, scope_id="session-001", lamport_clock=0
    )
    print("Extracted node id:", node.node_id, "confidence:", conf)

    engine = PhaseAMock()
    # prepare
    try:
        prep = prepare_commit_payload(engine, node)
        txid = prep["txid"]
        print(
            "Prepared txid:",
            txid,
            "content_hash:",
            prep["content_hash"],
            "payload_len:",
            prep["payload_len"],
        )
    except PrepareError as e:
        print("Prepare failed:", e)
        raise SystemExit(1)

    # finalize commit
    kernel_state = {}
    try:
        res = finalize_commit(
            engine,
            txid,
            kernel_apply_hook=lambda rec: example_kernel_apply_hook(rec, kernel_state),
        )
        print("Commit result:", res["status"])
        print("Kernel state after apply:", kernel_state)
    except CommitError as e:
        print("Commit failed:", e)
        # attempt abort
        try:
            abort_tx(engine, txid)
        except AbortError:
            pass
        raise SystemExit(1)
