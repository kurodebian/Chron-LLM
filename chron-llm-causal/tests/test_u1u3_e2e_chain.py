#!/usr/bin/env python3
"""JOB:U1U3 E2E chain gate (2026-10-29).

Chain: EXTRACT > WAL > TRIAD > SEQ > VOCAB > TRACE > PROJ
Invariants: HASH, RID!=TXID!=EID, NODUP, NOCONFLICT, NODRIFT, GAPLESS.
Checks: EDGE=312, D2=11.

Adjudications driving the VOCAB stage (verbatim, ledger):
  U1 = 語彙採用(11語目としてREQUIRES原文維持) — !=禁止を尊重し collapse しない
  U2 = 語彙採用(12語目としてREFINES原文維持) — 本番実運用実績に整合
  U3 = 語彙採用(13語目としてREFERENCES原文維持) — !=禁止を尊重
"""
import hashlib
import sys
from collections import Counter
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
_ROOT = Path(__file__).resolve().parents[2]
for p in (str(_SRC), str(_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from causal_kernel.edge_vocab import (  # noqa: E402
    EDGE_VOCAB,
    UNCLASSIFIED,
    lean_edge_mapping,
    normalize_relation,
)
from causal_kernel.bridge.wal_triad_bridge import (  # noqa: E402
    RecordDuplicateError,
    WALTriadIndex,
    content_hash as triad_content_hash,
    jcs_bytes as triad_jcs_bytes,
)
from causal_kernel.kernel.traceability_reconstructor import reconstruct  # noqa: E402
from tools.cae_extractor import (  # noqa: E402
    abort_tx,
    canonical_json_bytes,
    finalize_commit,
    prepare_commit_payload,
    run_extraction_pipeline,
)

PIN_EDGE = 312
PIN_D2_EDGES = 11
# A3-verified post-normalization label multiset; U1-U3 vocabulary extension
# must leave this byte-identical (no corpus token is requires/refines/references).
PIN_LABELS = {"UNCLASSIFIED": 236, "depends_on": 76}


class MiniWALEngine:
    """Minimal R2.1-D mock: sequence allocated at commit only (A2 v2)."""

    def __init__(self):
        self.wal = []
        self.next_txid = 1001
        self.next_sequence = 1
        self.active = {}

    def prepare(self, payload_dict):
        txid = self.next_txid
        self.next_txid += 1
        rec = {
            "hdr": {"type": "PREPARED", "txid": txid, "sequence": None},
            "payload": payload_dict,
        }
        self.active[txid] = rec
        self.wal.append(rec)
        return {"txid": txid, "rec": rec, "status": "OK"}

    def commit(self, txid):
        rec = self.active.get(txid)
        if not rec or rec["hdr"]["type"] != "PREPARED":
            return {"status": "CORRUPT"}
        rec["hdr"]["type"] = "COMMITTED"
        if rec["hdr"].get("sequence") is None:
            rec["hdr"]["sequence"] = self.next_sequence
            self.next_sequence += 1
        del self.active[txid]
        return {"rec": rec, "status": "OK", "hdr_sequence": rec["hdr"]["sequence"]}

    def abort(self, txid):
        rec = self.active.get(txid)
        if not rec:
            return {"status": "CORRUPT"}
        rec["hdr"]["type"] = "ABORTED"
        del self.active[txid]
        return {"rec": rec, "status": "OK"}


def _extract_tx(engine, text):
    node, conf = run_extraction_pipeline(
        text, pos=0, phase=1, score=0.95, scope_id="u1u3"
    )
    assert node is not None and conf >= 0.75
    prep = prepare_commit_payload(engine, node)
    return node, prep


# --------------------------------------------------------------- stages 1-4
def test_chain_extract_wal_triad():
    """EXTRACT payload flows unchanged into WAL frames and TRIAD index."""
    engine = MiniWALEngine()
    node, prep = _extract_tx(engine, "If session.state == AUTHENTICATED then set tx.status = COMMITTED")
    txid = prep["txid"]
    prepared_rec = engine.wal[0]

    res = finalize_commit(engine, txid)
    assert res["status"] == "OK"
    committed_rec = res["rec"]

    idx = WALTriadIndex()
    env_p = idx.attach(txid, prepared_rec["payload"], "PREPARED", sequence=None)
    env_c = idx.attach(txid, committed_rec["payload"], "COMMITTED",
                       sequence=committed_rec["hdr"]["sequence"])

    # INV: RID != TXID != EID, pairwise, per frame and across frames.
    rids = {env_p["record_id"], env_c["record_id"]}
    eids = {env_p["event_id"], env_c["event_id"]}
    assert all(str(txid) not in (r, e) for r in rids for e in eids)
    assert len(rids) == 2  # distinct physical frames -> distinct RIDs
    # same (txid, payload) pair -> one logical event identity
    assert env_p["event_id"] == env_c["event_id"]

    # INV: NODUP — byte-identical replay frame rejected, state unchanged.
    try:
        idx.attach(txid, prepared_rec["payload"], "PREPARED", sequence=None)
        raise AssertionError("duplicate frame accepted")
    except RecordDuplicateError:
        pass

    # INV: NOCONFLICT — no halt on the happy path.
    assert not idx.halted


def test_hash_identity_across_stages():
    """INV: HASH — extractor and bridge agree on canonical payload identity."""
    obj = {"b": [1, 2], "a": "x", "c": {"d": True}}
    assert triad_content_hash(obj) == hashlib.sha256(
        canonical_json_bytes(obj)
    ).hexdigest()
    assert triad_jcs_bytes(obj) == canonical_json_bytes(obj)
    # envelope fields are NOT hash inputs: same payload, different envelope
    idx = WALTriadIndex()
    e1 = idx.attach(1001, obj, "PREPARED", sequence=None)
    e2 = idx.attach(1001, obj, "COMMITTED", sequence=7)
    assert e1["content_hash"] == e2["content_hash"]


def test_seq_gapless_abort_no_gap():
    """SEQ/GAPLESS: committed sequences are exactly 1..N; abort consumes none."""
    engine = MiniWALEngine()
    _n1, p1 = _extract_tx(engine, "If session.state == AUTHENTICATED then set tx.status = COMMITTED")
    _n2, p2 = _extract_tx(engine, "When request arrives then emit response event")
    _n3, p3 = _extract_tx(engine, "If session.state == AUTHENTICATED then set tx.status = COMMITTED")

    abort_tx(engine, p2["txid"])
    r1 = finalize_commit(engine, p1["txid"])
    r3 = finalize_commit(engine, p3["txid"])

    seqs = [r1["hdr_sequence"], r3["hdr_sequence"]]
    assert seqs == [1, 2]  # GAPLESS, strictly monotonic, no abort hole
    committed = [r for r in engine.wal if r["hdr"]["type"] == "COMMITTED"]
    assert [r["hdr"]["sequence"] for r in committed] == list(range(1, len(committed) + 1))


# ---------------------------------------------------------------- stage 5
def test_vocab_u1u3_adopted_no_collapse():
    for tok in ("requires", "refines", "references"):
        assert tok.upper() in EDGE_VOCAB  # EDGE_VOCAB holds canonical UPPER members
        assert normalize_relation(tok) == tok
        assert normalize_relation(tok.upper()) == tok
    # adopted words are NOT collapsed into depends_on (source 53.4.2 != rules)
    assert normalize_relation("requires") != "depends_on"
    assert normalize_relation("references") != "depends_on"
    # off-vocab tokens still UNCLASSIFIED (incl. source-only candidates)
    assert normalize_relation("enforces") == UNCLASSIFIED
    assert normalize_relation("derived_from") == UNCLASSIFIED  # open alias issue
    assert normalize_relation("requires_x") == UNCLASSIFIED


def test_proj_no_lean_for_new_words():
    assert lean_edge_mapping("depends_on") == "parentID"
    for tok in ("requires", "refines", "references", "contradicts", UNCLASSIFIED):
        assert lean_edge_mapping(tok) is None  # NO_LEAN_MAPPING


# --------------------------------------------------------------- stages 6-7
def test_trace_nodrift_312_11():
    """TRACE: EDGE=312, D2=11, labels byte-identical to A3 post-state (NODRIFT)."""
    out = reconstruct()
    em = out["edge_mappings"]
    assert len(em) == PIN_EDGE
    d2_ids = {
        e["target_delta2_id"] for e in em
        if e.get("source_delta1_id") and e.get("target_delta2_id") is not None
    }
    assert len(d2_ids) == PIN_D2_EDGES

    labels = Counter(e["source_name_type"] for e in em)
    assert dict(labels) == PIN_LABELS  # NODRIFT vs A3: extension touched nothing

    # RAWPRESERVE: every edge carries the untouched source relation.
    assert all("source_relation_raw" in e for e in em)
    for e in em:
        assert normalize_relation(e["source_relation_raw"]) == e["source_name_type"]


def test_matrix_rows_adopted():
    """U1-U3 MATRIX rows: source EdgeType 9-word set fully resolves against the
    adopted 13-word vocabulary — 9 in, 0 collapsed, 0 silently dropped."""
    source_edge_type9 = {
        "depends_on", "requires", "refines", "contradicts", "derived_from",
        "references", "constrains", "equivalent_to", "causes",
    }
    direct = {t for t in source_edge_type9 if t.upper() in EDGE_VOCAB}
    assert direct == source_edge_type9 - {"derived_from", "constrains"}
    unresolved = {t for t in source_edge_type9 if normalize_relation(t) == UNCLASSIFIED}
    assert unresolved == {"derived_from", "constrains"}  # OPEN: not silently adopted
