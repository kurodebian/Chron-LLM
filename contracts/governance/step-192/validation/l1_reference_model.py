"""L1 contract-level reference model — STEP-192 (D11 V4 adjudication).

STATUS: REFERENCE MODEL L1 (not production implementation).
  LINEARIZATION_VALIDATION evidence track only. IMPLEMENTATION_STATUS for the
  production commit kernel remains NOT_VERIFIED. Model-validation PASS is not
  implementation validation (TEST_PASS != ACCEPTANCE, ACCEPTANCE != GLOBAL_ACCEPTANCE).

Implements, as pure functions over explicit byte-level disk state:
  execute(scenario, crash)  -> disk_state   (commit_attempt + crash at CP1..CP6)
  recover(disk_state)       -> final_state  (deterministic reconciliation)

Rules encoded (ADJUDICATIONS.md):
  §3 transaction order, §4 intent fixation, §5 WAL order / gapless, §6 Receipt,
  §7 CP1..CP6, §8 three-valued classification, §9 Idempotency reconciliation,
  §10 linearization point = persistence-confirmation point, determinism,
  §11 audit correspondence / INVALID_COMMIT, §12 frozen layer untouched.
  D3 half-open [a,b) gapless; D6 audit outside Canonical History;
  D7 R1..R6 verify-then-decide tail reconciliation;
  D8 M1..M6 Receipt = pure function of persisted state (no wall-clock),
     M5 regeneration allowed / reissue fault;
  D9 G1..G4 orphan Intent pipeline (retain -> ORPHAN_RESOLVED -> transfer,
     idempotent, no wall-clock GC);
  D10 I1 independent audit hash chain (audit-namespace sequence),
      I4 DISCARDED_INTERVAL verbatim evacuation + NO_SILENT_DISCARD,
      I5 audit-write failure -> admission HOLD, AUDIT_GAP append,
      admission-before-intent / receipt-after-record ordering.
  D12 X1..X4: frozen valid / AuthorityProof semantics unchanged here; historical
      validity = canonical prefix fold; NO_RETROACTIVE_INVALIDATION is checked
      harness-side (governance revocation events never invalidate prior records).

Determinism discipline (INV-H1, D11 V6): stdlib-only; no wall-clock reads; all
iteration over sorted() orders; no set/dict-iteration-order dependence;
random series only via explicit seeds (harness side).

Frozen layer (contracts/ChronLLM/*.lean) is read-only and untouched (D2).
"""

from __future__ import annotations

import hashlib
import json

# ---------------------------------------------------------------------------
# Vocabularies (Closed Vocabulary direction — OI-191-19)
# ---------------------------------------------------------------------------

IDEMPOTENCY_STATES = (
    "INTENT_FIXED",
    "WRITE_STARTED",
    "PERSISTENCE_CONFIRMED",
    "RECEIPT_ISSUED",
    "ORPHAN_RESOLVED",
)

FAULTS = (
    "AUDIT_INTEGRITY_FAULT",
    "AUDIT_GAP",
    "INVALID_COMMIT",
    "RECEIPT_REISSUE_FAULT",
    "DISCARDED_INTERVAL",
    "ORPHAN_TRANSFER",
    "ADMISSION_HOLD",
    "RECONCILIATION_REQUIRED",
)

REASON_CODES = (
    "TORN_FRAMING",
    "HASH_LINK_BROKEN",
    "POSITION_GAP",
    "DUPLICATE_OPERATION",
    "AUDIT_CORRESPONDENCE_MISSING",
)

# ---------------------------------------------------------------------------
# Deterministic hashing helpers
# ---------------------------------------------------------------------------


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def event_hash(rec: dict) -> str:
    """Canonical event identifier of a canonical record (D8 M1 input)."""
    return sha256_hex(canonical_json({
        "position": rec["position"],
        "operation_id": rec["operation_id"],
        "content_hash": rec["content_hash"],
        "authority_ref": rec["authority_ref"],
        "prev_hash": rec["prev_hash"],
    }))


def compute_receipt(rec: dict) -> str:
    """D8 M1: Receipt = H(OperationID, canonical event id, position n,
    prev-hash chain state, AuthorityRef). Wall-clock never participates."""
    return sha256_hex(canonical_json({
        "operation_id": rec["operation_id"],
        "event_hash": event_hash(rec),
        "position": rec["position"],
        "prev_hash": rec["prev_hash"],
        "authority_ref": rec["authority_ref"],
    }))


def record_bytes(rec: dict) -> str:
    """Verbatim on-disk byte representation (framing included) — D10 I4."""
    return canonical_json({
        "frame": "CANON_REC_V1",
        "position": rec["position"],
        "operation_id": rec["operation_id"],
        "content_hash": rec["content_hash"],
        "authority_ref": rec["authority_ref"],
        "prev_hash": rec["prev_hash"],
    })


def framing_intact(rec) -> bool:
    return (
        isinstance(rec, dict)
        and rec.get("frame") == "CANON_REC_V1"
        and isinstance(rec.get("position"), int)
        and isinstance(rec.get("operation_id"), str)
        and isinstance(rec.get("content_hash"), str)
        and isinstance(rec.get("authority_ref"), str)
        and isinstance(rec.get("prev_hash"), str)
    )


# ---------------------------------------------------------------------------
# Audit store (D6: outside Canonical History; D10 I1: independent chain)
# ---------------------------------------------------------------------------


def _audit_append(audit: list, event_type: str, operation_id, content,
                  discarded_bytes=None) -> dict:
    s = len(audit)
    prev = audit[-1]["content_hash"] if audit else "GENESIS"
    rec = {
        "audit_seq": s,                      # audit-namespace sequence (I1: never
        "event_type": event_type,            # reuses canonical position)
        "operation_id": operation_id,
        "content": content,
        "discarded_bytes": discarded_bytes,  # verbatim evacuation (I4) or None
        "prev_audit_hash": prev,
    }
    rec["content_hash"] = sha256_hex(canonical_json({
        "audit_seq": s,
        "event_type": event_type,
        "operation_id": operation_id,
        "content": content,
        "discarded_bytes": discarded_bytes,
        "prev_audit_hash": prev,
    }))
    audit.append(rec)
    return rec


def _audit_append_idempotent(audit: list, event_type: str, operation_id, content,
                             discarded_bytes=None) -> None:
    """Recovery-phase append: skip if an identical logical audit record is
    already present (same event_type / operation_id / content / discarded_bytes).
    Recovery is audit-idempotent: re-recovery performs no second append
    (INV-03 restart-count independence; D10 I5 append-only is preserved —
    nothing is ever mutated or removed)."""
    for a in audit:
        if (a["event_type"] == event_type
                and a["operation_id"] == operation_id
                and a["content"] == content
                and a["discarded_bytes"] == discarded_bytes):
            return
    _audit_append(audit, event_type, operation_id, content, discarded_bytes)


def verify_audit_chain(audit: list) -> list:
    """I1: gap / prev-audit-hash mismatch -> AUDIT_INTEGRITY_FAULT (recorded
    on the audit chain itself by the caller). Returns fault descriptors."""
    faults = []
    by_seq = sorted(audit, key=lambda r: r["audit_seq"])
    prev = "GENESIS"
    seen = set()
    for rec in by_seq:
        if rec["audit_seq"] in seen:
            faults.append({"kind": "AUDIT_SEQ_DUPLICATE", "audit_seq": rec["audit_seq"]})
        seen.add(rec["audit_seq"])
        if rec["audit_seq"] != len(seen) - 1:
            faults.append({"kind": "AUDIT_SEQ_GAP", "audit_seq": rec["audit_seq"]})
        if rec["prev_audit_hash"] != prev:
            faults.append({"kind": "AUDIT_LINK_BROKEN", "audit_seq": rec["audit_seq"]})
        recomputed = sha256_hex(canonical_json({
            "audit_seq": rec["audit_seq"],
            "event_type": rec["event_type"],
            "operation_id": rec["operation_id"],
            "content": rec["content"],
            "discarded_bytes": rec["discarded_bytes"],
            "prev_audit_hash": rec["prev_audit_hash"],
        }))
        if recomputed != rec["content_hash"]:
            faults.append({"kind": "AUDIT_CONTENT_MISMATCH", "audit_seq": rec["audit_seq"]})
        prev = rec["content_hash"]
    return faults


# ---------------------------------------------------------------------------
# Scenario / execution model
# ---------------------------------------------------------------------------

CRASH_POINTS = ("CP1", "CP2", "CP3", "CP4", "CP5", "CP6")
PERSISTENCE_VARIANTS = ("survives", "lost")  # CP4: post-write/pre-fsync ambiguity


def make_scenario(n_ops: int, audit_fail_ops=(), revocation=None):
    """Deterministic scenario builder. Single canonical append path (T-191-D):
    linearization order == ops order; concurrency lives only in
    [admission, commit_point) (D11 V1).

    revocation: optional dict {"authority_ref": str, "after_index": int} —
    governance event committed at canonical position after ops[after_index]
    (D5 candidate A / D12 X2 position-based). L1 models it as a canonical
    governance event record; validAt admission enforcement is the future
    extension contract (D12 X1) and is NOT modeled here.
    """
    ops = [{"operation_id": f"op{i}", "authority_ref": "authA"} for i in range(n_ops)]
    # audit_fail_ops: "opN" ids or bare int op indices (fuzz corpus) —
    # normalized to ids so execute() matches.
    fail_ids = {oid if isinstance(oid, str) else f"op{oid}" for oid in audit_fail_ops}
    return {
        "ops": ops,
        "audit_fail_ops": sorted(fail_ids),
        "revocation": revocation,
    }


def execute(scenario: dict, crash_point, crash_index: int, persistence: str = "survives"):
    """Run the transaction sequence for each op in linearization order and
    crash at (crash_point, crash_index). Returns byte-level disk_state.

    crash_index: index of the op whose transaction is interrupted.
    persistence: CP4 variant — whether the un-fsynced canonical write survives.
    """
    canonical: list = []
    torn: list = []
    intents: dict = {}
    idem: dict = {}
    receipts: dict = {}
    audit: list = []
    holds: list = []
    attempted: list = []

    for i, op in enumerate(scenario["ops"]):
        oid = op["operation_id"]
        if i == crash_index and crash_point == "CP1":
            break  # crash before admission fixation: no side effects (§7 CP1)

        # Admission + audit record (D10 I5 admission-before-intent).
        audit_ok = oid not in scenario["audit_fail_ops"]
        if audit_ok:
            _audit_append(audit, "ADMISSION_APPROVED", oid,
                          {"op_index": i, "authority_ref": op["authority_ref"]})
        else:
            _audit_append(audit, "AUDIT_WRITE_FAILURE", oid, {"op_index": i})
            holds.append(oid)
            break  # new admissions HOLD; later ops not attempted (I5)

        attempted.append(oid)
        idem[oid] = {"state": "INTENT_FIXED", "intent_ref": f"intent-{oid}"}
        intents[oid] = {
            "operation_id": oid,
            "content_hash": sha256_hex(canonical_json({"op": oid})),
            "authority_ref": op["authority_ref"],
            # declared time boundaries [intent_begin, intent_expiry) — contract
            # level only (§12 / D12 X2); never used in validity decisions.
            "declared_boundaries": [i, i + 1],
        }

        if i == crash_index and crash_point == "CP2":
            break  # intent persisted, canonical write not started (§7 CP2)

        idem[oid]["state"] = "WRITE_STARTED"
        n = len(canonical)
        prev_hash = event_hash(canonical[-1]) if canonical else "GENESIS"  # §5: hash of previous event
        rec = {
            "frame": "CANON_REC_V1",
            "position": n,
            "operation_id": oid,
            "content_hash": intents[oid]["content_hash"],
            "authority_ref": op["authority_ref"],
            "prev_hash": prev_hash,
        }

        if i == crash_index and crash_point == "CP3":
            raw = record_bytes(rec)
            torn.append({"raw": raw[: max(1, len(raw) // 2)]})  # torn framing
            break  # partial write (§7 CP3)

        if i == crash_index and crash_point == "CP4":
            if persistence == "survives":
                canonical.append(rec)  # write landed, fsync never confirmed
            break  # INDETERMINATE (§7 CP4 / §8)

        canonical.append(rec)
        idem[oid]["state"] = "PERSISTENCE_CONFIRMED"

        if i == crash_index and crash_point == "CP5":
            break  # persisted, receipt not yet issued -> regenerated in recover (§7 CP5)

        receipts[oid] = compute_receipt(rec)
        idem[oid]["state"] = "RECEIPT_ISSUED"
        _audit_append(audit, "COMMIT_RESULT", oid,
                      {"position": rec["position"], "event_hash": event_hash(rec)})
        # CP6: crash after receipt, before finality declaration — state above
        # is already finality-ready (§7 CP6).

    # Governance revocation event (D5 candidate A / D12 X2): committed to the
    # canonical chain after ops[after_index]. Never mutates prior records
    # (NO_RETROACTIVE_INVALIDATION — D12 X3).
    rev = scenario.get("revocation")
    if rev is not None and crash_point is None:
        after = rev["after_index"]
        if after < len(scenario["ops"]):
            n = len(canonical)
            prev_hash = event_hash(canonical[-1]) if canonical else "GENESIS"
            rec = {
                "frame": "CANON_REC_V1",
                "position": n,
                "operation_id": f"gov-revocation-{n}",
                "content_hash": sha256_hex(canonical_json(
                    {"revokes": rev["authority_ref"], "kind": "GOVERNANCE_EVENT"})),
                "authority_ref": rev["authority_ref"],
                "prev_hash": prev_hash,
            }
            # governance events commit through the same admission-before-intent
            # path (D5 candidate A / D10 I5): audit record first.
            _audit_append(audit, "ADMISSION_APPROVED", rec["operation_id"],
                          {"governance_event": True, "authority_ref": rev["authority_ref"]})
            canonical.append(rec)
            _audit_append(audit, "COMMIT_RESULT", rec["operation_id"],
                          {"position": n, "event_hash": event_hash(rec)})

    return {
        "canonical": canonical,
        "torn": torn,
        "intents": intents,
        "idem": idem,
        "receipts": receipts,
        "audit": audit,
        "holds": holds,
        "attempted": attempted,
    }


# ---------------------------------------------------------------------------
# Recovery / reconciliation (deterministic pure function of disk_state)
# ---------------------------------------------------------------------------


def recover(disk_state: dict) -> dict:
    canon = [r for r in disk_state["canonical"] if framing_intact(r)]
    canon.sort(key=lambda r: r["position"])
    torn = sorted(disk_state["torn"], key=lambda t: t["raw"])
    intents = dict(disk_state["intents"])
    idem = {k: dict(v) for k, v in disk_state["idem"].items()}
    receipts = dict(disk_state["receipts"])
    audit = sorted([dict(a) for a in disk_state["audit"]], key=lambda a: a["audit_seq"])
    faults: list = []

    # --- head walk: intact gapless prefix (§5 / D3) ------------------------
    k = 0
    prev_hash = "GENESIS"
    head_ops = set()
    while k < len(canon):
        rec = canon[k]
        if rec["position"] != k or rec["prev_hash"] != prev_hash:
            break
        if rec["operation_id"] in head_ops:
            break  # duplicate OperationID in head -> reconciliation boundary
        head_ops.add(rec["operation_id"])
        prev_hash = event_hash(rec)
        k += 1

    if k < len(canon) or torn:
        faults.append({"kind": "RECONCILIATION_REQUIRED"})

    # --- tail classification [k, N) (D7 R1) --------------------------------
    kept = list(canon[:k])
    kept_ops = set(head_ops)
    discarded = []
    for rec in canon[k:]:
        reason = None
        expected_prev = event_hash(kept[-1]) if kept else "GENESIS"
        if not framing_intact(rec):
            reason = "TORN_FRAMING"
        elif rec["prev_hash"] != expected_prev:
            reason = "HASH_LINK_BROKEN"
        elif rec["position"] != len(kept):
            reason = "POSITION_GAP"
        elif rec["operation_id"] in kept_ops:
            reason = "DUPLICATE_OPERATION"
        elif not any(a["event_type"] == "ADMISSION_APPROVED"
                     and a["operation_id"] == rec["operation_id"] for a in audit):
            reason = "AUDIT_CORRESPONDENCE_MISSING"  # INVALID_COMMIT direction (§11)
            faults.append({"kind": "INVALID_COMMIT", "operation_id": rec["operation_id"]})
            _audit_append_idempotent(audit, "INVALID_COMMIT", rec["operation_id"], {
                "reason_code": reason,
                "record_sha256": sha256_hex(record_bytes(rec)),
            })
        if reason is not None:
            discarded.append((rec, reason))
        else:
            kept.append(rec)
            kept_ops.add(rec["operation_id"])

    # --- torn bytes are always discarded (framing not intact) --------------
    for t in torn:
        discarded.append(({"raw": t["raw"], "position": len(kept)}, "TORN_FRAMING"))

    # --- D7 R4 Receipt anchor: never discard a record with a valid stored
    #     Receipt (kept records above already satisfy this by construction;
    #     guard asserted below).
    for rec, _reason in discarded:
        if framing_intact(rec) and receipts.get(rec["operation_id"]) == compute_receipt(rec):
            raise AssertionError("NO_RECEIPT_ANCHOR_VIOLATION: receipt-anchored record discarded")

    # --- D7 R5 / D10 I4: verbatim evacuation, NO_SILENT_DISCARD ------------
    for rec, reason in sorted(
        discarded,
        key=lambda d: (d[0].get("position", -1), d[0].get("raw", ""), d[1]),
    ):
        raw = rec.get("raw") if "raw" in rec else record_bytes(rec)
        _audit_append_idempotent(audit, "DISCARDED_INTERVAL", rec.get("operation_id"), {
            "reason_code": reason,
            "canonical_range": [rec.get("position"), rec.get("position")],
            "intent_ref": intents.get(rec.get("operation_id"), {}).get(
                "intent_ref") if rec.get("operation_id") else None,
            "idem_state": idem.get(rec.get("operation_id"), {}).get("state"),
            "discarded_sha256": sha256_hex(raw),
            "chain_state_at_discard": {"position": rec.get("position"),
                                       "prev_hash": rec.get("prev_hash", "GENESIS")},
        }, discarded_bytes=raw)
        faults.append({"kind": "DISCARDED_INTERVAL", "operation_id": rec.get("operation_id"),
                       "reason_code": reason})

    # --- D9 G1..G3: orphan Intent pipeline (retain -> resolve -> transfer) -
    for oid in sorted(intents):
        if oid in kept_ops:
            continue
        idem.setdefault(oid, {"state": "INTENT_FIXED", "intent_ref": f"intent-{oid}"})
        if oid in disk_state["holds"]:
            # D10 I6: an admission-HOLDed operation is retained for
            # reconciliation — it is NOT an orphan Intent; no transfer.
            continue
        if idem[oid]["state"] == "ORPHAN_RESOLVED":
            # idempotent: re-recovery performs no second transfer, but the
            # fault set is canonical across restarts (INV-03).
            faults.append({"kind": "ORPHAN_TRANSFER", "operation_id": oid})
            continue
        idem[oid]["state"] = "ORPHAN_RESOLVED"
        _audit_append_idempotent(audit, "ORPHAN_INTENT_TRANSFER", oid, {
            "intent_ref": intents[oid].get("intent_ref", f"intent-{oid}"),
            "idem_state_before": "ORPHAN_RESOLVED",
        })
        faults.append({"kind": "ORPHAN_TRANSFER", "operation_id": oid})

    # --- D8 M1/M5: Receipt regeneration / reissue fault --------------------
    for rec in kept:
        oid = rec["operation_id"]
        recomputed = compute_receipt(rec)
        stored = receipts.get(oid)
        if stored is None:
            receipts[oid] = recomputed  # regeneration (CP5): allowed, byte-identical
            if oid in idem and idem[oid]["state"] in ("PERSISTENCE_CONFIRMED", "WRITE_STARTED"):
                idem[oid]["state"] = "RECEIPT_ISSUED"
        elif stored != recomputed:
            faults.append({"kind": "RECEIPT_REISSUE_FAULT", "operation_id": oid})
            # §6: never pick one without reconciliation; both retained as evidence.
        if not any(a["event_type"] == "COMMIT_RESULT" and a["operation_id"] == oid
                   and a["content"].get("position") == rec["position"]
                   and a["content"].get("event_hash") == event_hash(rec)
                   for a in audit):
            # recovery is audit-idempotent: a COMMIT_RESULT already present
            # (written by execute, or by a prior recovery pass) is not
            # duplicated — INV-03 restart-count independence.
            _audit_append(audit, "COMMIT_RESULT", oid,
                          {"position": rec["position"], "event_hash": event_hash(rec)})

    # --- I5: audit gaps recorded by append, never retroactive mutation -----
    for oid in sorted(disk_state["holds"]):
        faults.append({"kind": "ADMISSION_HOLD", "operation_id": oid})

    # --- I1: final audit chain verification ---------------------------------
    chain_faults = verify_audit_chain(audit)
    for f in chain_faults:
        faults.append({"kind": "AUDIT_INTEGRITY_FAULT", **f})

    # --- fault set is derivable from the audit trail (D10 I4: every fault
    #     has its audit record; D10 I5: records are never removed). After
    #     torn bytes have been evacuated, re-recovery re-derives the same
    #     fault set from the audit records themselves — INV-03 restart-count
    #     independence.
    for a in audit:
        if a["event_type"] == "DISCARDED_INTERVAL":
            faults.append({"kind": "DISCARDED_INTERVAL",
                           "operation_id": a["operation_id"],
                           "reason_code": a["content"]["reason_code"]})
        elif a["event_type"] == "INVALID_COMMIT":
            faults.append({"kind": "INVALID_COMMIT", "operation_id": a["operation_id"]})
    if torn or any(a["event_type"] == "DISCARDED_INTERVAL" for a in audit):
        faults.append({"kind": "RECONCILIATION_REQUIRED"})

    # faults are a canonical SET (deduplicated): re-recovery derives the
    # same fault set — INV-03 restart-count independence.
    faults = sorted({canonical_json(f): f for f in faults}.values(),
                    key=canonical_json)
    audit.sort(key=lambda a: a["audit_seq"])

    return {
        "canonical": kept,
        "idem": idem,
        "receipts": receipts,
        "audit": audit,
        "faults": faults,
        "attempted": list(disk_state["attempted"]),
        "holds": sorted(disk_state["holds"]),
    }


def state_digest(final_state: dict) -> str:
    """Canonical digest of a recovered state — used for determinism checks."""
    return sha256_hex(canonical_json({
        "canonical": [event_hash(r) for r in final_state["canonical"]],
        "idem": {k: final_state["idem"][k]["state"] for k in sorted(final_state["idem"])},
        "receipts": {k: final_state["receipts"][k] for k in sorted(final_state["receipts"])},
        "audit_head": final_state["audit"][-1]["content_hash"] if final_state["audit"] else None,
        "audit_len": len(final_state["audit"]),
        "faults": final_state["faults"],
    }))
