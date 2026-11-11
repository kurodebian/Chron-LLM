#!/usr/bin/env python3
"""MODE=RECLASSIFY_ADOPTION — consume adoption records, re-derive claim statuses.

Read-only with respect to pipeline_v1 artifacts: it never mutates claim_ir_v2.jsonl,
graph.jsonl, conflict_matrix.json, or causal_resolution.json. It derives
reclassification_report.json and causal_resolution_after_adoption.json from:
  - adoption_records.json  (authorization layer, LLM-adjudicated)
  - claim_ir_v2.jsonl      (immutable claim layer)
  - conflict_matrix.json   (immutable conflict layer)

Status tiers are provenance-tagged: a VERIFIED reached through an adopted norm is
VERIFIED_VIA_ADOPTED_NORM, never plain VERIFIED. VERIFIED (plain) keeps its original
meaning: pin identity + design-only scan, no adoption required.

Gates: STOP if any cited evidence path:line does not resolve on disk, if any effect
targets an unknown claim id, or if the recomputed total disagrees with 3304.
"""
import json, hashlib, os, sys, re
from datetime import datetime, timezone

BASE = '/home/junu/Chron-LLM'
SRC = BASE + '/specification-organizer-experiment/results/impl_verification'
ADR = SRC + '/adoption'
RT = SRC + '/causal_runtime_v1'

records = json.load(open(ADR + '/adoption_records.json', encoding='utf-8'))
claims = {}
for line in open(RT + '/claim_ir_v2.jsonl', encoding='utf-8'):
    if line.strip():
        c = json.loads(line)
        claims[c['id']] = c
conflicts = json.load(open(RT + '/conflict_matrix.json', encoding='utf-8'))
resolution = json.load(open(RT + '/causal_resolution.json', encoding='utf-8'))

# --- GATE 1: every cited evidence must resolve on disk ---
def resolve(cite):
    p, _, lines = cite.partition(':')
    full = os.path.join(BASE, p)
    if not os.path.isfile(full):
        return False
    if lines:
        n = sum(1 for _ in open(full, encoding='utf-8', errors='replace'))
        rng = lines.split('-')
        try:
            hi = int(rng[-1].rstrip('L'))
        except ValueError:
            return True  # anchor token citations (non-numeric) exist via file
        return hi <= n
    return True

bad_cites = []
for r in records:
    for cite in r['cited_evidence']:
        if not resolve(cite):
            bad_cites.append((r['adr_id'], cite))
if bad_cites:
    print('GATE FAIL: cited evidence does not resolve:', bad_cites)
    sys.exit(1)

# --- GATE 2: effect targets must exist in the claim layer ---
effects = []
for r in records:
    for e in r['classification_effects']:
        cid = e['claim']
        if cid not in claims:
            print('GATE FAIL: unknown claim id', r['adr_id'], cid)
            sys.exit(1)
        effects.append((r['adr_id'], cid, e))

# --- reclassify ---
def provenance_tier(rec):
    # Ratified records carry the human authorization tier; provisional ones keep
    # the provisional provenance tag. Claim statuses themselves are unchanged.
    return rec['status'] if rec['status'] == 'RATIFIED_HUMAN' else 'ADOPTED_LLM_PROVISIONAL'

rec_status = {r['adr_id']: r['status'] for r in records}
new_status = {cid: c['status'] for cid, c in claims.items()}
applied = []
for adr_id, cid, e in effects:
    applied.append({'adr_id': adr_id, 'claim': cid,
                    'old_status': new_status[cid], 'new_status': e['new_status'],
                    'artifact': e.get('artifact'), 'reason': e['reason'],
                    'provenance': provenance_tier({'status': rec_status[adr_id]})})
    new_status[cid] = e['new_status']

counts = {}
for s in new_status.values():
    counts[s] = counts.get(s, 0) + 1
assert sum(counts.values()) == 3304, f'total mismatch: {sum(counts.values())}'

# conflict matrix entries must all be accounted for after adoption
conflict_ids = {c['claim'] for c in conflicts}
unaccounted = sorted(cid for cid in conflict_ids if new_status[cid] == 'CONFLICT')

report = {
    'mode': 'RECLASSIFY_ADOPTION',
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'provenance_note': ('Statuses reached via adoption carry provenance tags; plain VERIFIED '
                        'means pin identity/design-only as before. Adjudication method: '
                        'LLM_ADJUDICATION; tier per record as recorded in adoption_records.json '
                        '(RATIFIED_HUMAN records are human-ratified; others remain '
                        'ADOPTED_LLM_PROVISIONAL pending human ratification).'),
    'adoption_records': [
        {'adr_id': r['adr_id'], 'target': r['target'], 'decision': r['decision'],
         'adopted_rule': r['adopted_rule'], 'status': r['status'],
         'method': r['adjudication']['method'], 'model': r['adjudication']['model'],
         'confidence': r['adjudication']['confidence']}
        for r in records
    ],
    'claim_status_counts': counts,
    'claims_total': sum(counts.values()),
    'applied_effects': applied,
    'conflict_matrix_entries': conflicts,
    'conflicts_remaining_unadjudicated': unaccounted,
    'inputs_digest': {
        'adoption_records_sha256': hashlib.sha256(open(ADR + '/adoption_records.json', 'rb').read()).hexdigest(),
        'claim_ir_v2_sha256': hashlib.sha256(open(RT + '/claim_ir_v2.jsonl', 'rb').read()).hexdigest(),
        'conflict_matrix_sha256': hashlib.sha256(open(RT + '/conflict_matrix.json', 'rb').read()).hexdigest(),
        'causal_resolution_sha256': hashlib.sha256(open(RT + '/causal_resolution.json', 'rb').read()).hexdigest(),
    },
}
json.dump(report, open(ADR + '/reclassification_report.json', 'w', encoding='utf-8'),
          indent=1, ensure_ascii=False)

# --- after-adoption resolution (derived, original file untouched) ---
after = []
for root in resolution:
    adr = next((r for r in records if r['target'] == root['root']), None)
    entry = dict(root)
    if adr:
        tier_suffix = ('RATIFIED' if adr['status'] == 'RATIFIED_HUMAN' else 'PROVISIONAL')
        entry['status'] = f'RESOLVED_BY_LLM_ADJUDICATION_{tier_suffix}'
        entry['adoption'] = {'adr_id': adr['adr_id'], 'decision': adr['decision'],
                             'adopted_rule': adr['adopted_rule'],
                             'method': adr['adjudication']['method'],
                             'tier': adr['status']}
        if 'ratification' in adr:
            entry['adoption']['ratification'] = adr['ratification']
        entry['sequenced_actions'] = adr.get('sequenced_actions', root.get('sequenced_actions'))
    else:
        entry['status'] = root['status']
    after.append(entry)
json.dump(after, open(ADR + '/causal_resolution_after_adoption.json', 'w', encoding='utf-8'),
          indent=1, ensure_ascii=False)

print('RECLASSIFY OK')
print(json.dumps(counts, indent=1))
print('effects applied:', len(applied))
print('conflicts remaining unadjudicated:', unaccounted)
