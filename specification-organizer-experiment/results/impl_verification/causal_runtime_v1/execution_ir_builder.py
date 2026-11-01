#!/usr/bin/env python3
# EXECUTION_IR_BUILDER — consumes the CAUSAL_RUNTIME_V1 outputs only.
# Phase 1: CLAIM -> RULE (:when :require :do :verify)
# Phase 2: ROOT  -> causal_resolution.json (:cause :impact :dependency :resolution)
# Phase 3: RULE  -> EXEC (:when :require :do :verify + status/adoption)
# Phase 4: implementation_gaps.json / adjudication_candidates.json from UNRESOLVED + CONFLICT
#
# Rules enforced: implementation != adoption; semantic match only (keyword match forbidden);
# MISSING_EVIDENCE != PASS; no guessed adjudication (authority conflict stays unresolved).
import json, collections, hashlib

OUT = '/home/junu/Chron-LLM/specification-organizer-experiment/results/impl_verification/causal_runtime_v1'

claims = [json.loads(l) for l in open(OUT+'/claim_ir_v2.jsonl', encoding='utf-8')]
code_rows = [json.loads(l) for l in open(OUT+'/code_ir_v2.jsonl', encoding='utf-8')]
graph = json.load(open(OUT+'/causal_graph.json', encoding='utf-8'))
roots = json.load(open(OUT+'/root_causes.json', encoding='utf-8'))

# code ids come from the graph CODE nodes (same order as code_ir_v2 rows)
code_nodes = [n for n in graph['nodes'] if n['type'] == 'CODE']
assert len(code_nodes) == len(code_rows)
for n, r in zip(code_nodes, code_rows):
    assert n['artifact'] == r['artifact'] and n['symbol'] == r['symbol']
CODE = {n['id']: dict(r, id=n['id']) for n, r in zip(code_nodes, code_rows)}

# semantic edges only (basis == 'semantic'); keyword-based edges are not proof
sem = [e for e in graph['edges'] if e.get('basis') == 'semantic' and e['edge'] != 'DEPENDS_ON']
by_claim = collections.defaultdict(list)
for e in sem:
    if e['from']:
        by_claim[e['from']].append(e)

def q(s):
    return 'nil' if not s else '"%s"' % str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')

def ref(cid):
    c = CODE.get(cid)
    if not c:
        return 'no-join-path'
    line = c.get('line') or ''
    return '%s:%s' % (c['artifact'], line) if line else c['artifact']

def verify_slot(c):
    """Executable check for a rule. Only semantic equivalence may produce a proof term;
    a missing join is recorded as a check requirement, never as a pass."""
    es = by_claim.get(c['id'], [])
    if not es:
        if c['status'] == 'MISSING_EVIDENCE':
            return 'MISSING_EVIDENCE; check cannot be executed'
        return 'no semantic join; keyword match not admissible'
    parts = []
    for e in es:
        cid = e['to']
        if cid and cid.startswith('code#'):
            cc = CODE[cid]
            parts.append('%s %s: operation_equivalence %s -> %s' % (e['edge'], cid, c['act'] or 'nil', cc['operation'] or 'nil'))
        else:
            parts.append('%s %s' % (e['edge'], e.get('note', '')))
    return '; '.join(parts)

# rule -> ROOT id via cause_chain membership (mechanical, no guessed attribution)
ROOT_INDEX = {}
for r in roots:
    for c in r['cause_chain']:
        ROOT_INDEX[c] = r['root']

STATUS = {'VERIFIED': 'VERIFIED', 'CONFLICT': 'CONFLICT', 'MISSING_EVIDENCE': 'MISSING_EVIDENCE',
          'UNRESOLVED': 'UNRESOLVED', 'AGREED': 'AGREED'}

rules = []
promoted = set()
for c in claims:
    has_slot = c['pre'] or c['act'] or c['eff'] or c['inv']
    classified = c['status'] in ('VERIFIED', 'CONFLICT', 'MISSING_EVIDENCE', 'AGREED')
    if not (has_slot or classified):
        continue  # UNRESOLVED with no normalised content stays a claim, not a rule
    promoted.add(c['id'])
    rules.append({
        'id': c['id'],
        'when': c['pre'],
        'require': c['inv'] or c['eff'],
        'do': c['act'],
        'verify': verify_slot(c),
        'status': STATUS.get(c['status'], 'UNRESOLVED'),
        'adoption': 'NOT_ADOPTED',  # no adoption record exists in the corpus
        'root': c.get('root_cause'),
        'root_id': ROOT_INDEX.get(c.get('root_cause')),
        'join': c.get('join') or [e['edge'] for e in by_claim.get(c['id'], [])],
        'evidence': c['evidence'],
    })

# --- PHASE 1 ---
with open(OUT + '/dsl_ir.lisp', 'w', encoding='utf-8') as f:
    f.write(';; DSL_IR (EXECUTION_IR_BUILDER phase 1) — CLAIM -> RULE (:when :require :do :verify)\n')
    f.write(';; trace: SPEC -> CLAIM_IR -> CODE_IR -> CAUSAL_GRAPH -> DSL_IR -> EXECUTION_IR\n')
    for r in rules:
        f.write('(RULE %s :when %s :require %s :do %s :verify %s)\n' % (
            r['id'], q(r['when']), q(r['require']), q(r['do']), q(r['verify'])))

# --- PHASE 2 ---
RESOLUTION = {
    'ROOT-001': {
        'resolution': 'adjudicate which surface holds recovery authority; no winner can be assigned from the corpus',
        'type': 'AUTHORITY_DECISION_REQUIRED',
        'blocked_by': 'authority_conflict (wal.lisp resolves at recovery start, bridge is fail-closed)',
        'then': ['re-classify code#03 vs code#05', 're-run tests/test_cae_e2e.py:205-235 against the adopted rule',
                 'the test currently asserts wal.lisp behaviour, which is not an adoption of it'],
    },
    'ROOT-002': {
        'resolution': 'adopt an explicit storage norm for incomplete records at recovery, or retract the test expectation',
        'type': 'NORM_ADOPTION_REQUIRED',
        'blocked_by': 'norm exists as a design claim only; implementation (code#02) contradicts it; implementation != adoption',
        'then': ['define tail-policy: preserve | truncate-on-adopted-norm | quarantine',
                 'make code#02 conditional on the adopted norm',
                 'the existing test asserting truncation is evidence of divergence, not of adoption'],
    },
    'ROOT-003': {
        'resolution': 'define durability precedence against Canonical History; code#06 satisfies only the txid/duplicate half of the claim',
        'type': 'DEFINITION_REQUIRED',
        'blocked_by': 'no Canonical History surface exists in the code corpus; the structural half of the claim has no join path',
        'then': ['decide local-durability vs history-precedence',
                 'implement the comparison path or restrict the claim to local scope'],
    },
    'ROOT-004': {
        'resolution': 'cannot be resolved here: no adjudicated authority; classification stays frozen (no win/lose)',
        'type': 'AUTHORITY_CONFLICT',
        'blocked_by': 'hard constraint authority_conflict — two surfaces encode opposite rules for the same state semantics',
        'then': ['adjudication by authority is the only path', 'then re-run phase 3 for the affected rules'],
    },
}
resolution = []
for r in roots:
    res = RESOLUTION[r['root']]
    resolution.append({'root': r['root'], 'name': r['name'],
                       'cause': r['cause_chain'], 'impact': r['impact_chain'], 'dependency': r['dependency_chain'],
                       'resolution': res['resolution'], 'resolution_type': res['type'],
                       'blocked_by': res['blocked_by'], 'sequenced_actions': res['then'],
                       'status': 'UNRESOLVED_ADJUDICATION_REQUIRED'})
json.dump(resolution, open(OUT + '/causal_resolution.json', 'w'), ensure_ascii=False, indent=1)

# --- PHASE 3 ---
with open(OUT + '/execution_ir.lisp', 'w', encoding='utf-8') as f:
    f.write(';; EXECUTION_IR (phase 3) — RULE -> EXEC (:when :require :do :verify)\n')
    f.write(';; promotion rule: only a semantic join yields an executable check; keyword match is forbidden;\n')
    f.write(';; MISSING_EVIDENCE is never treated as PASS; implementation is never treated as adoption.\n')
    for r in rules:
        f.write('(EXEC %s :when %s :require %s :do %s :verify %s :status %s :adoption %s :root %s :cause %s :evidence %s)\n' % (
            r['id'], q(r['when']), q(r['require']), q(r['do']), q(r['verify']),
            r['status'], r['adoption'], q(r['root_id']), q(r['root']), q(r['evidence'])))

# --- PHASE 4 ---
cnt = collections.Counter(r['status'] for r in rules)
keyword_excluded = [e['to'] for e in graph['edges'] if e.get('basis') == 'keyword-only candidate, excluded from semantic join']
executable = [r for r in rules if r['status'] == 'VERIFIED']
gaps = {
    'classification': dict(cnt),
    'executable_now': [],
    'executable_now_note': 'nothing is executable: a rule needs semantic proof AND an adoption record; the corpus has semantic proof for one rule but no adoption record for any rule',
    'promotable_pending_adoption': [r['id'] for r in executable],
    'claims_total': len(claims),
    'claims_promoted_to_rules': len(promoted),
    'claims_not_promoted_no_normalized_content': len(claims) - len(promoted),
    'executable_rules': [r['id'] for r in executable],
    'rules_with_no_semantic_join': sum(1 for r in rules if 'no semantic join' in r['verify'] or 'MISSING_EVIDENCE' in r['verify']),
    'keyword_match_forbidden_excluded': len(keyword_excluded),
    'adoption_gap': {'implementation_without_adoption_record': len(rules), 'adoption_records_found': 0,
                     'note': 'code implements a behaviour; no norm-adoption record exists in the corpus, so no rule can be marked adopted'},
    'joined_code_nodes': sorted(set(e['to'] for e in sem if e['to'] in CODE)),
    'code_nodes_without_semantic_join': sorted(set(CODE) - set(e['to'] for e in sem if e['to'] in CODE)),
    'rules_without_root_mapping': sum(1 for r in rules if r['root_id'] is None and r['status'] in ('VERIFIED','CONFLICT','MISSING_EVIDENCE')),
    'root_mapping_note': 'rules keep root nil when CLAIM_IR recorded no root_cause; attribution by domain (e.g. the single VERIFIED rule concerns durability, which ROOT-003 governs) is not asserted here because the claim record does not state it',
    'retracted_findings': [{
        'finding': 'tie-break by event_id conflict',
        'reason': 'the cited artifact chron-llm-causal/tests/test_event_store.py does not exist; no norm claim with that semantics was recorded in the ledger — treated as MISSING_EVIDENCE, not as a conflict',
        'status': 'RETRACTED',
    }],
    'structural_gap': [{
        'claim': 'mdsu0035#81bdafbbc1',
        'gap': 'duplicate detection is implemented for txid (code#06) but the Canonical-History precedence half has no implementation surface',
        'kind': 'NO_JOIN_PATH',
    }],
}
json.dump(gaps, open(OUT + '/implementation_gaps.json', 'w'), ensure_ascii=False, indent=1)

conflict_rules = [r for r in rules if r['status'] == 'CONFLICT']
adjudication = []
for r in conflict_rules:
    es = by_claim.get(r['id'], [])
    adjudication.append({
        'claim': r['id'],
        'rule_do': r['do'],
        'rule_require': r['require'],
        'code_side': [{'code': e['to'], 'edge': e['edge'], 'artifact': CODE[e['to']]['artifact'] if e['to'] in CODE else None,
                       'operation': CODE[e['to']]['operation'] if e['to'] in CODE else None, 'note': e.get('note')}
                      for e in es],
        'root_cause': r['root'],
        'root_id': r['root_id'],
        'decision_needed': 'authority must choose norm, implementation, or a reconciling definition',
        'status': 'REQUIRES_ADJUDICATION',
        'authority_conflict_frozen': r['root'] == 'ROOT-004',
    })
json.dump(adjudication, open(OUT + '/adjudication_candidates.json', 'w'), ensure_ascii=False, indent=1)

print('rules:', len(rules), 'counts:', dict(cnt))
print('executable (semantic join + no conflict):', [r['id'] for r in executable])
print('adjudication candidates:', [a['claim'] for a in adjudication])
for k in ('claim_ir_v2.jsonl', 'code_ir_v2.jsonl', 'causal_graph.json', 'root_causes.json',
          'dsl_ir.lisp', 'causal_resolution.json', 'execution_ir.lisp',
          'implementation_gaps.json', 'adjudication_candidates.json'):
    print('sha256 %s %s' % (k, hashlib.sha256(open(OUT + '/' + k, 'rb').read()).hexdigest()))
