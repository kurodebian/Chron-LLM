#!/usr/bin/env python3
"""
CIR Extraction Pipeline v1.0 - Causal Intermediate Representation.

Deterministic IDs, EXPLICIT evidence, FAIL_CLOSED.
"""
import os, sys, json, re, hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Set

BASE = Path(__file__).parent
OUT_DIR = BASE / "output" / "causal_intermediate"
CP_DIR = OUT_DIR / "checkpoints"
MANIFEST_PATH = OUT_DIR / "manifest.json"
CIR_PATH = OUT_DIR / "cir.jsonl"
ERROR_PATH = OUT_DIR / "errors.jsonl"

TASK_ID = "CIR-POC-001"
SCHEMA_VERSION = "1.0"
JOB_ID = "JOB_001"

ALLOWED_NODE_TYPES = {"ENTITY","STATE","OPERATION","EVENT","DATA","PROPERTY",
                      "AUTHORITY","CONSTRAINT","BOUNDARY","PROJECTION","PROPOSAL",
                      "CONTAINER","UNKNOWN"}
ALLOWED_CAUSAL_CLASSES = {"CAUSAL_FLOW","DATA_DEPENDENCY","CONTROL_FLOW",
                          "AUTHORITY_FLOW","STATE_TRANSITION","DERIVATION",
                          "CONSTRAINT","INVARIANT","PERSISTENCE","OBSERVABILITY",
                          "BOUNDARY","UNKNOWN"}
ALLOWED_EVIDENCE = {"EXPLICIT","DERIVED","UNRESOLVED"}
ALLOWED_STATUS = {"ESTABLISHED","CANDIDATE","UNRESOLVED"}
ALLOWED_SEMANTIC = set([
  "DEFINITION","ENTITY","PROPERTY","STATE","TRANSITION","INVARIANT","PRECONDITION",
  "POSTCONDITION","CONTRACT","AUTHORITY","DEPENDENCY","CAUSAL_RELATION","DATA_FLOW",
  "CONTROL_FLOW","INPUT","OUTPUT","ERROR","REJECTION_RULE","COMMIT_RULE","PROJECTION_RULE",
  "RECOVERY_RULE","PERSISTENCE_RULE","OBSERVABILITY_RULE","CONFIGURATION","OPEN_QUESTION","OTHER"])
ALLOWED_MODALITY = {"MUST","MUST_NOT","SHOULD","SHOULD_NOT","MAY","CAN","DESCRIPTIVE","UNKNOWN"}

class Fail(Exception):
    def __init__(self, code, msg):
        super().__init__(msg); self.code = code

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()

def doc_id_from_path(p: str) -> str:
    s = p.replace("\\","/").strip()
    parts = [x for x in s.split("/") if x]
    key = "-".join(parts[-2:]) if len(parts) >= 2 else s
    return "DOC-" + sha256_bytes(key.encode())[:16]

def local_node_key(name: str) -> str:
    return sha256_bytes(name.encode())[:16]

def write_atomic(path, data):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    if isinstance(data, str):
        payload = data.encode()
        f = open(tmp, "wb"); f.write(payload); f.flush()
    else:
        f = open(tmp, "w"); f.write(json.dumps(data, separators=(",",":"), sort_keys=False)); f.flush()
    try: os.fsync(f.fileno())
    except Exception: pass
    f.close(); os.replace(tmp, p)

def write_jsonl(path, records):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w") as f:
        for r in records:
            f.write(json.dumps(r, separators=(",",":"), sort_keys=False) + "\n")
    os.replace(tmp, p)

def atomic_checkpoint(cp, seq=None):
    CP_DIR.mkdir(parents=True, exist_ok=True)
    target = (CP_DIR / f"CHECKPOINT-{seq}.json") if seq else (CP_DIR / "LATEST.json")
    write_atomic(target, cp)
    write_atomic(CP_DIR / "CURRENT.json", cp)

def classify_doc(text):
    t = text.lower()
    kind = "CONTRACT" if "constitution" in t else (
        "ARCHITECTURE" if "architecture" in t else
        "SPEC" if any(k in t for k in ["spec","requirements","constraint"]) else
        "EVIDENCE" if any(k in t for k in ["evidence","test","proof"]) else "UNKNOWN")
    status = "CURRENT" if re.search(r"baseline|current|v1\.0", t) else (
        "HISTORICAL" if "deprecated" in t or "obsolete" in t else
        "FROZEN" if "frozen" in t else
        "EXPERIMENTAL" if "experimental" in t else
        "DERIVED" if "derived" in t else "UNKNOWN")
    relevance = "HIGH" if any(k in t for k in ["causal","authoritative","state","commit","invariant","evidence"]) else (
        "MEDIUM" if any(k in t for k in ["implementation","detail"]) else "UNKNOWN")
    return kind, status, relevance

def find_section(lines, start, end):
    for j in range(start-1, -1, -1):
        l = lines[j].strip()
        if re.match(r"^#{1,6}\s+", l):
            return l.lstrip("#").strip()
    return ""

def extract_claims(lines, path, doc_id):
    claims, i, n = [], 0, 0
    while i < len(lines):
        l = lines[i].strip()
        if not l or l.startswith("#") or re.match(r"^-{3,}$", l):
            i += 1; continue
        block, j = [], i
        while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith("#"):
            block.append(lines[j].rstrip()); j += 1
        n += 1
        src_text = "\n".join(block)
        sem, mod = classify_claim(src_text)
        claims.append({
            "record_type":"CLAIM","claim_id":f"CLM-{doc_id}-{n:04d}",
            "document_id":doc_id,"source.path":path,
            "source.section":find_section(lines,i,j),"source.start_line":i+1,
            "source.end_line":j,"source_text":src_text,
            "semantic_type":sem,"modality":mod,"evidence_level":"EXPLICIT",
        })
        i = j
    return claims

def classify_claim(t):
    T = t.lower()
    if re.search(r"shall not|must not|should not|cannot", T):
        mod = "MUST_NOT"
    elif "shall" in T: mod = "MUST"
    elif "must" in T: mod = "MUST"
    elif "should" in T: mod = "SHOULD"
    elif re.search(r"\bmay\b", T): mod = "MAY"
    elif "can" in T and "cannot" not in T: mod = "CAN"
    else: mod = "DESCRIPTIVE"
    if re.search(r"shall not|must not|should not|cannot|does not|does not possess", T):
        sem = "REJECTION_RULE"
    elif "invariant" in T: sem = "INVARIANT"
    elif "authoritative" in T and "sole" in T: sem = "AUTHORITY"
    elif re.search(r"consist.{0,3}of|consists", T) and "event" in T: sem = "DEPENDENCY"
    elif "deterministic" in T or "reproduc" in T or "side-effect-free" in T or "side effect free" in T:
        sem = "PROPERTY"
    elif "causal" in T or "causally" in T: sem = "CAUSAL_RELATION"
    elif "mutat" in T or "modify" in T: sem = "TRANSITION"
    elif re.search(r"(event|candidate|commit|canonical|working|derived|external|evidence|session|derive|proposal)", T):
        sem = "ENTITY"
    elif re.search(r"\b(may|shall|must|should)\b", T): sem = "CONTRACT"
    else: sem = "OTHER"
    return sem, mod

def extract_nodes(claims, doc_id):
    node_map = {}
    concepts = {
        "Canonical":"STATE","Working":"STATE","Derived":"STATE","External":"STATE",
        "Commit":"OPERATION","Event":"ENTITY","Evidence":"ENTITY",
        "Candidate":"PROPOSAL","Derive":"OPERATION","Session":"CONTAINER",
        "Authoritative":"AUTHORITY",
    }
    for c in claims:
        t = c["source_text"].lower()
        for name, ntype in concepts.items():
            if name.lower() in t and name not in node_map:
                node_map[name] = {
                    "record_type":"NODE","node_id":f"NODE-{doc_id}-{local_node_key(name)}",
                    "document_id":doc_id,"canonical_name":name,"node_type":ntype,
                    "source_claims":[c["claim_id"]],
                    "evidence_level":"EXPLICIT",
                    "status":"ESTABLISHED",
                }
    return list(node_map.values())

def extract_edges(claims, doc_id):
    edges, n = [], 0
    rules = [
        (lambda t: "canonical" in t and "authoritative" in t and "sole" in t,
         "Authoritative","Canonical","IS_STATE_OF","AUTHORITY_FLOW"),
        (lambda t: "commit" in t and "mutat" in t and "canonical" in t and "any authoritative" in t,
         "Commit","Canonical","MUTATES","AUTHORITY_FLOW"),
        (lambda t: "evidence" in t and re.search(r"consist.{0,3}of|consists", t) and "event" in t,
         "Event","Evidence","CONSTITUTES","DATA_DEPENDENCY"),
        (lambda t: "commit" in t and "evidence" in t and "incorporat" in t and "canonical" in t,
         "Evidence","Canonical","INCORPORATED_BY","CAUSAL_FLOW"),
        (lambda t: "commit" in t and "establis" in t and "canonical" in t,
         "Commit","Canonical","ESTABLISHES","STATE_TRANSITION"),
        (lambda t: "derived" in t and "canonical" in t and ("apply" in t or "derivation" in t or "obtained" in t),
         "Derive","Canonical","APPLIES_TO","DERIVATION"),
    ]
    for c in claims:
        t = c["source_text"].lower()
        for pred, fr, to, rel, ccls in rules:
            n += 1
            if pred(t):
                edges.append({
                    "record_type":"EDGE","edge_id":f"EDGE-{doc_id}-{n:04d}",
                    "from":fr,"to":to,"relation":rel,"causal_class":ccls,
                    "source_claims":[c["claim_id"]],
                    "evidence_level":"EXPLICIT","status":"ESTABLISHED",
                })
                break
    return edges

def validate(records):
    errs, seen = [], set()
    for r in records:
        rt = r.get("record_type")
        rid = (r.get("document_id") if rt=="DOCUMENT" else
               r.get("claim_id") if rt=="CLAIM" else
               r.get("node_id") if rt=="NODE" else
               r.get("edge_id") if rt=="EDGE" else "")
        if not rid:
            errs.append(f"MISSING_ID: {rt}")
            continue
        if rid in seen: errs.append(f"DUPLICATE_ID: {rid}")
        seen.add(rid)
        if rt == "NODE" and r.get("node_type") not in ALLOWED_NODE_TYPES:
            errs.append(f"BAD_NODE_TYPE: {r.get('node_type')} in {rid}")
        if rt == "EDGE" and r.get("causal_class") not in ALLOWED_CAUSAL_CLASSES:
            errs.append(f"BAD_CAUSAL_CLASS: {r.get('causal_class')} in {rid}")
        if rt == "CLAIM" and r.get("semantic_type") not in ALLOWED_SEMANTIC:
            errs.append(f"BAD_SEMANTIC: {r.get('semantic_type')} in {rid}")
        if rt == "CLAIM" and r.get("modality") not in ALLOWED_MODALITY:
            errs.append(f"BAD_MODALITY: {r.get('modality')} in {rid}")
    return errs

def build_cp(doc_id, src, h, lines, claims, nodes, edges, records, out_h, phase, status, next_action):
    return {
        "task_id": TASK_ID, "job_id": JOB_ID, "source_path": str(src),
        "source_hash": h, "phase": phase, "last_completed_line": len(lines),
        "last_completed_claim": len(claims), "last_completed_node": len(nodes),
        "last_completed_edge": len(edges), "records_written": len(records),
        "output_file": str(CIR_PATH), "output_sha256": out_h,
        "next_action": next_action,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
    }

def main():
    if len(sys.argv) < 2:
        print("usage: extract_cir.py <source_md>", file=sys.stderr); sys.exit(2)
    src = Path(sys.argv[1])
    if not src.exists(): src = BASE / src
    if not src.exists():
        print(f"FAIL_CLOSED: MISSING_SOURCE path={src}", file=sys.stderr); sys.exit(1)
    raw = src.read_text()
    lines = raw.splitlines()
    h = sha256_bytes(raw.encode())
    doc_id = doc_id_from_path(str(src))
    kind, status, relevance = classify_doc(raw)
    doc_rec = {
        "record_type":"DOCUMENT","document_id":doc_id,
        "source.path":str(src),"source.format":"markdown","source.hash":h,
        "source.line_count":len(lines),"source.section":"","source.start_line":1,
        "source.end_line":len(lines),"source_text":raw,
        "classification":{"kind":kind,"status":status},"causal_relevance":relevance,
    }
    claims = extract_claims(lines, str(src), doc_id)
    nodes = extract_nodes(claims, doc_id)
    edges = extract_edges(claims, doc_id)
    records = [doc_rec] + claims + nodes + edges
    errs = validate(records)
    if errs:
        write_atomic(ERROR_PATH, json.dumps({"task_id":TASK_ID,"errors":errs}, separators=(",",":")) + "\n")
        cp = build_cp(doc_id, src, h, lines, claims, nodes, edges, records, "", "VALIDATE", "BLOCKED", "REPAIR " + "; ".join(errs[:3]))
        atomic_checkpoint(cp, seq=1)
        print(f"JOB_STATUS=BLOCKED ERRORS={len(errs)}", file=sys.stderr)
        for e in errs[:5]: print(f"  - {e}", file=sys.stderr)
        sys.exit(1)
    write_jsonl(CIR_PATH, records)
    out_h = sha256_bytes(CIR_PATH.read_bytes())
    manifest = {
        "task_id":TASK_ID,"schema_version":SCHEMA_VERSION,
        "created_at":datetime.now(timezone.utc).isoformat(),
        "source_root":str(src),"documents_processed":1,"records_generated":len(records),
        "source_hashes":{str(src):h},"processing_status":"PASS","checkpoint_status":"PASS",
    }
    write_atomic(MANIFEST_PATH, manifest)
    cp = build_cp(doc_id, src, h, lines, claims, nodes, edges, records, out_h, "DONE", "PASS", "STOP")
    atomic_checkpoint(cp, seq=2)
    print(f"JOB_STATUS=PASS doc={doc_id} hash={h} records={len(records)} doc=1 claim={len(claims)} node={len(nodes)} edge={len(edges)}")
    print(f"manifest={MANIFEST_PATH} cir={CIR_PATH} cp={CP_DIR / 'CURRENT.json'} cp2={CP_DIR / 'CHECKPOINT-2.json'}")

if __name__ == "__main__":
    main()
