#!/usr/bin/env python3
"""MODE=RATIFY_ADOPTION — upgrade adoption tier ADOPTED_LLM_PROVISIONAL -> RATIFIED_HUMAN.

Human ratification is the authorization act itself; this script records it. It:
  1. snapshots digests of the immutable layers (claim_ir_v2.jsonl, graph.jsonl,
     conflict_matrix.json, causal_resolution.json) before and after, asserting
     byte-identity (this run must not touch them),
  2. flips status on every adoption record and attaches a ratification block
     carrying the verbatim human adjudication,
  3. validates every record against adoption_record.schema.json,
  4. reports what changed. Nothing outside adoption/ is written.
"""
import hashlib, json, os, sys
from datetime import datetime, timezone

import jsonschema

BASE = '/home/junu/Chron-LLM'
SRC = BASE + '/specification-organizer-experiment/results/impl_verification'
ADR = SRC + '/adoption'
RT = SRC + '/causal_runtime_v1'

IMMUTABLE = ['claim_ir_v2.jsonl', 'causal_graph.json', 'conflict_matrix.json',
             'causal_resolution.json']

ADJUDICATION_VERBATIM = '全て批准 (8件 → RATIFIED_HUMAN)'
RATIFIER = 'junu (user, session adjudication form, single-select)'

def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()

before = {f: sha(os.path.join(RT, f)) for f in IMMUTABLE}

schema = json.load(open(ADR + '/adoption_record.schema.json', encoding='utf-8'))
records = json.load(open(ADR + '/adoption_records.json', encoding='utf-8'))
assert len(records) == 8, f'expected 8 records, got {len(records)}'

now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
flipped = []
for r in records:
    if r['status'] != 'ADOPTED_LLM_PROVISIONAL':
        print(f'RATIFY SKIP: {r["adr_id"]} status={r["status"]} (not provisional)',
              file=sys.stderr)
        continue
    r['status'] = 'RATIFIED_HUMAN'
    r['ratification'] = {
        'method': 'HUMAN_RATIFICATION',
        'ratifier': RATIFIER,
        'date': now,
        'adjudication_verbatim': ADJUDICATION_VERBATIM,
        'upgraded_from': 'ADOPTED_LLM_PROVISIONAL',
    }
    flipped.append(r['adr_id'])

for r in records:
    jsonschema.validate(r, schema)

json.dump(records, open(ADR + '/adoption_records.json', 'w', encoding='utf-8'),
          indent=1, ensure_ascii=False)

after = {f: sha(os.path.join(RT, f)) for f in IMMUTABLE}
drift = sorted(f for f in IMMUTABLE if before[f] != after[f])
if drift:
    print('GATE FAIL: immutable layer drift', drift, file=sys.stderr)
    sys.exit(1)

print('RATIFY OK')
print('flipped:', flipped)
print('tiers:', sorted({r['status'] for r in records}))
print('immutable layers byte-identical:')
for f in IMMUTABLE:
    print(' ', f, before[f][:16], 'unchanged')
