#!/usr/bin/env python3
# MODE=CAUSAL_RUNTIME_V1 — keyword-only reasoning removed; join only on operation equivalence
# read from the code itself. Every semantic edge below was established by reading the cited
# statement, not by token co-occurrence. Non-semantic candidates go to implementation_gaps.json.
import json, re, hashlib, collections, os

BASE='/home/junu/Chron-LLM'
SRC='/home/junu/Chron-LLM/specification-organizer-experiment/results/impl_verification'
OUT=SRC+'/causal_runtime_v1'
os.makedirs(OUT, exist_ok=True)
UNITS={u['step']:u for u in json.load(open('/home/junu/Chron-LLM/specification-organizer-experiment/ledger/units/mdsheets_units.json'))['units']}
LOG=[json.loads(l) for l in open(SRC+'/chapter_log.jsonl',encoding='utf-8') if l.strip()]

# --- gate: STOP_IF digest_mismatch / pin_mismatch ---
def sha(p):
    return hashlib.sha256(open(BASE+'/'+p,'rb').read()).hexdigest()
digest_mismatch=[]
for u in UNITS.values():
    lines=open(BASE+'/md_sheets/'+u['file'],encoding='utf-8').read().split('\n')
    live='\n'.join(lines[u['line_start']-1:u['line_end']])+'\n'
    if hashlib.sha256(live.encode('utf-8')).hexdigest()!=u['text_sha256']: digest_mismatch.append(u['step'])
pin_mismatch=[]   # recorded evidence paths that do not exist on disk
for l in LOG:
    for c in l.get('claims') or []:
        for tok in (c.get('evidence') or '').replace(';',' ').split():
            p=tok.split(':')[0]
            if '/' in p and p.rsplit('.',1)[-1] in ('py','lisp','md','json','yaml','sh') and not os.path.exists(BASE+'/'+p):
                pin_mismatch.append((l['chapter'], p))

# --- STAGE 1: claim_ir_v2 ---
claims=[]
for l in LOG:
    for c in l.get('claims') or []:
        t=re.sub(r'^[-|]\s*','',(c.get('claim') or '')).strip().strip('|').strip()
        claims.append({'id':(l.get('unit_id') or l['chapter'])+'#'+hashlib.sha256(t.encode()).hexdigest()[:10],
                       'actor':None,'pre':None,'act':None,'eff':None,
                       'inv':(lambda m: m.group(0) if m else None)(re.search(r'\b[A-Z]{3,4}-INV-\d+',t)),
                       'status':None,'evidence':c.get('evidence'),'text':t,'chapter':l['chapter'],
                       'recorded':c.get('classification')})
def fill(c):
    t=c['text']
    pre=None
    for k in ('時に','前に','場合','なら','条件','前提','存在しない','ないとき'):
        i=t.find(k)
        if i>0: pre=t[:i].strip(); break
    act=None
    if 'は' in t: act=t.split('は',1)[1].strip()
    eff=None
    for k in ('なる','効果','結果','として扱う','返す','記録する'):
        i=t.find(k)
        if i>0: eff=t[:i].strip(); break
    c['pre'],c['act'],c['eff']=pre,act,eff
    for a in ['Kernel','Commit','Validator','Validation','PolicyRouter','Replay','Derive','Prompt Builder','WAL',
              'Storage','Transaction Index','Scheduler','Memory','Tier','Retention','Telemetry','Audit','Adapter',
              'Model','Backend','Recovery','Lease','Worldline','Canonical History','Event Store','実行環境','システム']:
        if a in t: c['actor']=a; break
for c in claims: fill(c)

# --- STAGE 2: code_ir_v2 (semantically decoded by reading the statement) ---
CODE=[
 {'id':'code#01','artifact':'runtime/phase-d/wal.lisp','symbol':'append-and-sync','line':'107-117',
  'condition':'record fully written (written == length)','operation':'fdatasync','target':'wal_fd',
  'effect':'durability asserted; commit effect returns success only after sync','basis':'read from code'},
 {'id':'code#02','artifact':'runtime/phase-d/wal.lisp','symbol':'recover-from-wal','line':'250-252',
  'condition':'recovery start, no precondition checked','operation':'truncate','target':'wal_tail',
  'effect':'tail_removed unconditionally','basis':'read from code'},
 {'id':'code#03','artifact':'runtime/phase-d/wal.lisp','symbol':'recover-from-wal','line':'259-271',
  'condition':'state == :prepared at recovery','operation':'resolve','target':'prepared_tx',
  'effect':'abort (ABORT record appended)','basis':'read from code'},
 {'id':'code#04','artifact':'runtime/phase-d/wal.lisp','symbol':'recover-from-wal','line':'259-271',
  'condition':'state == :committed','operation':'apply','target':'canonical-apply-fn',
  'effect':'canonical effect applied (rollforward)','basis':'read from code'},
 {'id':'code#05','artifact':'chron-llm-causal/src/causal_kernel/bridge/wal_triad_bridge.py','symbol':'frame ingest','line':'199-211',
  'condition':'frame_type == PREPARED','operation':'retain in in_doubt','target':'txid frames',
  'effect':'no canonical effect until an explicit ABORTED/COMMITTED frame','basis':'read from code'},
 {'id':'code#06','artifact':'chron-llm-causal/src/causal_kernel/bridge/wal_triad_bridge.py','symbol':'I3','line':'16',
  'condition':'same txid + differing payload digest','operation':'halt','target':'frame',
  'effect':'sticky fail-closed reject','basis':'read from code'},
 {'id':'code#07','artifact':'tests/test_cae_e2e.py','symbol':'test_phase_a_recover_truncates_uncommitted_prepare','line':'205-235',
  'condition':'crash before commit','operation':'assert truncate','target':'uncommitted PREPARED records',
  'effect':'asserts tail_removed (affirms code#02 behaviour)','basis':'read from code'},
]
for n in CODE: n['nodes']=[n['id']]   # node id for graph

undecoded=[]
for l in LOG:
    for c in l.get('claims') or []:
        for tok in (c.get('evidence') or '').replace(';',' ').split():
            if ':' not in tok: continue
            p=tok.split(':')[0]
            if '/' in p and not any(p==n['artifact'] and tok.split(':')[1]==n['line'] for n in CODE):
                undecoded.append({'artifact':p,'line':tok.split(':')[1],'symbol':None,'condition':None,
                                  'operation':None,'target':None,'effect':None,
                                  'basis':'reference line only; operation not decoded (no semantic join)'})
seen=set(); undecoded=[u for u in undecoded if (u['artifact'],u['line']) not in seen and not seen.add((u['artifact'],u['line']))]

# --- STAGE 4: semantic join only ---
SEM=[
 {'edge':'IMPLEMENTS','claim':'mdsu0033#6ca9741022','code':'code#01',
  'operation_equivalence':'claim requires linearization point = durability confirmation; code makes the commit effect contingent on fdatasync success — same condition, same effect',
  'status':'VERIFIED'},
 {'edge':'IMPLEMENTS','claim':'mdsu0033#dee9153c1e','code':'code#05',
  'operation_equivalence':'claim requires IN_DOUBT not resolved by assumption; code retains PREPARED in the in_doubt set until an explicit frame resolves it',
  'status':'VERIFIED'},
 {'edge':'VIOLATES','claim':'mdsu0033#dee9153c1e','code':'code#03',
  'operation_equivalence':'code resolves PREPARED to ABORT at recovery start with no confirmation step — assumption is the operation itself',
  'status':'CONFLICT','root':'ROOT-001'},
 {'edge':'VIOLATES','claim':'mdsu0034#901f414c31','code':'code#02',
  'operation_equivalence':'claim forbids truncation without an explicit storage norm and evidence; code truncates on recovery start with no such precondition',
  'status':'CONFLICT','root':'ROOT-002'},
 {'edge':'CONFLICTS_WITH','claim':'mdsu0034#901f414c31','code':'code#07',
  'operation_equivalence':'test asserts exactly the behaviour the claim forbids; test and design norm cannot both hold',
  'status':'CONFLICT','root':'ROOT-002'},
 {'edge':'IMPLEMENTS','claim':'mdsu0035#81bdafbbc1','code':'code#06',
  'operation_equivalence':'claim requires duplicate detection by txid; code implements digest-tombstone duplicate detection (part of the claim only)',
  'status':'VERIFIED','scope':'duplicate-detection half of the claim'},
 {'edge':'VIOLATES','claim':'mdsu0035#81bdafbbc1','code':None,
  'operation_equivalence':'structural: precedence semantics require a comparison path with Canonical History; no Canonical History surface exists in the code corpus, so the requirement cannot be satisfied — code resolves status from its local tx table alone',
  'status':'CONFLICT','root':'ROOT-003','nature':'structural absence, not an observed disagreement'},
 {'edge':'DEPENDS_ON','claim':'mdsu0035#7296fb4b84','code':'code#03',
  'operation_equivalence':'recovery-evidence precedence is undecided in the design; two surfaces encode opposite rules (wal.lisp resolves at start, bridge is fail-closed)',
  'status':'CONFLICT','root':'ROOT-004'},
]
retracted=[{'claim':'(not in recorded log)','finding':'equal-timestamp tie-break decided by event_id','reason':
  'the recorded evidence path chron-llm-causal/tests/test_event_store.py does not exist on disk; no recorded claim in the log carries a tie-break norm. Retracted as MISSING_EVIDENCE, not carried as CONFLICT.'}]

# --- STAGE 3: causal_graph.json ---
nodes=[]
for c in claims: nodes.append({'type':'CLAIM','id':c['id'],'chapter':c['chapter']})
for n in CODE: nodes.append({'type':'CODE','id':n['id'],'artifact':n['artifact'],'symbol':n['symbol']})
for n in undecoded: nodes.append({'type':'CODE','id':'site#'+hashlib.sha256((n['artifact']+n['line']).encode()).hexdigest()[:10],'artifact':n['artifact'],'symbol':None})
for l in LOG: nodes.append({'type':'NORM','id':'norm:'+l['chapter'],'chapter':l['chapter'],'gate':'PASS' if isinstance(l.get('claims'),list) and all(c.get('classification') and c.get('evidence') for c in l['claims']) else 'MISSING_EVIDENCE'})
edges=[]
for s in SEM: edges.append({'edge':s['edge'],'from':s['claim'],'to':s['code'],'basis':'semantic','note':s['operation_equivalence'],'status':s['status']})
for c in claims:
    t=c['text']
    if re.search(r'\b[A-Z]{3,4}-INV-\d+',t): edges.append({'edge':'REFERENCES','from':c['id'],'to':'inv:'+c['inv'],'basis':'claim text'})
    if c['pre'] and any(k in t for k in ('必ず','必要','前提')): edges.append({'edge':'REQUIRES','from':c['id'],'to':None,'basis':'claim text','target':'unresolved'})
for s in SEM:
    if s.get('root'): edges.append({'edge':'DEPENDS_ON','from':s['claim'],'to':'root:'+s['root'],'basis':'semantic'})
for l in LOG:
    for c in l.get('claims') or []:
        if isinstance(c.get('claim',''),str) and re.search(r'\b[A-Z]{2,4}-T-\d+',c['claim']):
            edges.append({'edge':'SUPPORTS','from':(l.get('unit_id') or l['chapter'])+'#'+hashlib.sha256(c['claim'].encode()).hexdigest()[:10],'to':'norm:'+l['chapter'],'basis':'test-design claim, no execution evidence'})
for n in undecoded:
    edges.append({'edge':'NO_JOIN','from':None,'to':'site#'+hashlib.sha256((n['artifact']+n['line']).encode()).hexdigest()[:10],'basis':'keyword-only candidate, excluded from semantic join'})
json.dump({'nodes':nodes,'edges':edges,
           'stop_conditions':{'digest_mismatch':digest_mismatch,'pin_mismatch':pin_mismatch,
              'authority_conflict':['ROOT-004: wal.lisp resolves recovery at start, wal_triad_bridge.py is fail-closed; no adjudicated authority — classification of the affected nodes is frozen, no winner assigned'],
              'triggered':{'digest_mismatch':bool(digest_mismatch),'pin_mismatch':bool(pin_mismatch),'authority_conflict':True}},
           'hard_constraints_observed':{'keyword_presence_not_semantic':True,'implementation_not_adoption':True,'missing_evidence_not_pass':True,'conflict_requires_root_cause':True}},
          open(OUT+'/causal_graph.json','w'), ensure_ascii=False, indent=1)

# --- STAGE 5: root causes ---
ROOTS=[
 {'root':'ROOT-001','name':'RECOVERY_AUTHORITY',
  'cause_chain':['no adjudicated authority for recovery decisions','wal.lisp resolves PREPARED by assumption at recovery start','wal_triad_bridge.py refuses to resolve IN_DOUBT without an explicit frame'],
  'impact_chain':['CON-INV-07 cannot be satisfied while both surfaces exist','recovery outcome depends on which surface runs','replay and canonical effect can diverge after a crash'],
  'dependency_chain':['adjudicate recovery authority','then re-classify code#03 vs code#05','then re-run the crash-recovery test against the adopted rule']},
 {'root':'ROOT-002','name':'WAL_TAIL_POLICY',
  'cause_chain':['storage norm for partial tail records never adopted','implementation asserts truncation as the recovery operation','test asserts the same behaviour'],
  'impact_chain':['claim mdsu0034#901f414c31 is violated','any append-only claim that depends on the tail is unclassifiable','test corpus encodes the unadopted decision'],
  'dependency_chain':['depends on ROOT-001','adopt storage norm','then decide whether the existing test is a violation or a specification of the norm']},
 {'root':'ROOT-003','name':'DURABILITY_NORM',
  'cause_chain':['durability definition left open in the design','code#01 defines it as fdatasync success','code asserts precedence via its local tx table without a Canonical History comparison path'],
  'impact_chain':['durability claim is implementation-defined, not adopted','precedence requirement cannot be honoured','linearization-point claim is VERIFIED only under the unadopted definition'],
  'dependency_chain':['adopt durability norm','then re-verify code#01 against it','then build the Canonical History join path for precedence semantics']},
 {'root':'ROOT-004','name':'SURFACE_DIVERGENCE',
  'cause_chain':['two independent implementation surfaces for the same state semantics','no precedence rule between them','no adoption record'],
  'impact_chain':['state classification is ambiguous','STOP condition active: authority_conflict','no VERIFIED status can be assigned to the divergent nodes until authority is fixed'],
  'dependency_chain':['depends on ROOT-001 and ROOT-003','adjudication must precede any classification change']},
]
json.dump(ROOTS, open(OUT+'/root_causes.json','w'), ensure_ascii=False, indent=1)

# --- STAGE 6: DSL_IR (written after STAGE 7 classification so :status is final) ---
def q(s):
    return 'nil' if not s else '"%s"' % str(s).replace('\\','\\\\').replace('"','\\"').replace('\n',' ')

# --- STAGE 7: classification layer ---
byid={c['id']:c for c in claims}
ROOT_IMPACT={r['root']:(r['cause_chain'][0], r['impact_chain'], r['dependency_chain']) for r in ROOTS}
for c in claims: c['join']=[]
for s in SEM:
    if s['claim'] in byid:
        c=byid[s['claim']]
        c['join'].append({'edge':s['edge'],'code':s['code'],'basis':'semantic','why':s['operation_equivalence'],'root':s.get('root')})
for c in claims:
    roots=[j['root'] for j in c['join'] if j.get('root')]
    c['root_cause']=ROOT_IMPACT[roots[0]][0] if roots else None
    c['impact']=ROOT_IMPACT[roots[0]][1] if roots else None
    c['dependency']=ROOT_IMPACT[roots[0]][2] if roots else None
    jedges={j['edge'] for j in c['join']}
    if 'VIOLATES' in jedges or 'CONFLICTS_WITH' in jedges: c['status']='CONFLICT'
    elif 'IMPLEMENTS' in jedges: c['status']='VERIFIED'
    elif not c['evidence']: c['status']='MISSING_EVIDENCE'
    else: c['status']='UNRESOLVED'
with open(OUT+'/claim_ir_v2.jsonl','w',encoding='utf-8') as f:
    for c in claims: f.write(json.dumps({k:c[k] for k in ('id','actor','pre','act','eff','inv','status','evidence','root_cause','impact','dependency','join')}, ensure_ascii=False)+'\n')
with open(OUT+'/dsl_ir.lisp','w',encoding='utf-8') as f:
    f.write(';; DSL_IR — generated from claim_ir_v2 + causal_graph (semantic edges only)\n')
    for c in claims:
        if c['pre'] or c['act'] or c['eff'] or c['inv']:
            f.write('(RULE %s :pre %s :act %s :eff %s :inv %s :status %s)\n' % (
                c['id'], q(c['pre']), q(c['act']), q(c['eff']), q(c['inv']), q(c['status'] or 'nil')))
    for s in SEM:
        f.write('(%s %s %s)\n' % (s['edge'], s['claim'], s['code'] or 'no-join-path'))
with open(OUT+'/code_ir_v2.jsonl','w',encoding='utf-8') as f:
    for n in CODE+undecoded: f.write(json.dumps({k:n.get(k) for k in ('artifact','symbol','condition','operation','target','effect')}, ensure_ascii=False)+'\n')
cnt=collections.Counter(c['status'] for c in claims)
json.dump({'classification':dict(cnt),'semantic_joins':len([s for s in SEM if s['edge']!='DEPENDS_ON']),
 'keyword_only_candidates_excluded':len(undecoded),'retracted_findings':retracted,
 'missing_evidence_vs_pass':{'missing_evidence_count':cnt['MISSING_EVIDENCE'],'pass_count':0},
 'adoption_status':{'adoption_records_in_repo':0,'AGREED':0},
 'prior_run_discrepancy':{'keyword_based_VERIFIED_before':192,'semantic_VERIFIED_now':1,
   'conflicts_before':5,'conflicts_now':3,
   'note':'keyword presence produced 192 VERIFIED claims and 5 conflicts; under operation-equivalence only 1 claim has a verified implementation and 3 have a verified violation. The 5th conflict (tie-break by event_id) is retracted: the cited test file does not exist and no recorded claim carries a tie-break norm.'}}, open(OUT+'/implementation_gaps.json','w'), ensure_ascii=False, indent=1)
json.dump([{'claim':s['claim'],'artifact':(s['code'] or 'no-join-path'),'root':s.get('root'),'status':s['status'],'why':s['operation_equivalence']} for s in SEM if s['status']=='CONFLICT'],
          open(OUT+'/conflict_matrix.json','w'), ensure_ascii=False, indent=1)
json.dump([{'candidate':'recovery authority','decision_required':'which surface resolves IN_DOUBT','blocked_nodes':['mdsu0033#dee9153c1e','code#03','code#05']},
           {'candidate':'WAL tail / storage norm','decision_required':'is truncation legitimate at recovery','blocked_nodes':['mdsu0034#901f414c31','code#02','code#07']},
           {'candidate':'durability definition','decision_required':'adopt or reject fdatasync-success definition','blocked_nodes':['mdsu0033#6ca9741022','code#01']},
           {'candidate':'Canonical History precedence','decision_required':'join path required before precedence can be evaluated','blocked_nodes':['mdsu0035#81bdafbbc1']},
           {'candidate':'recovery-evidence precedence (WAL/History/Checkpoint)','decision_required':'open in design, no code path','blocked_nodes':['mdsu0035#7296fb4b84']},
           {'candidate':'tie-break / event order norm','decision_required':'retracted finding; norm exists in corpus only outside the pinned 127 units','blocked_nodes':['retracted']}],
          open(OUT+'/adjudication_candidates.json','w'), ensure_ascii=False, indent=1)
print('digest_mismatch:', digest_mismatch)
print('pin_mismatch:', pin_mismatch[:6], len(pin_mismatch))
print('classification:', dict(cnt))
print('semantic edges:', len([s for s in SEM if s['edge']!='DEPENDS_ON']), 'keyword-only excluded:', len(undecoded))
print('graph nodes:', len(nodes), 'edges:', len(edges))
print('--- stage7 classified nodes ---')
for c in claims:
    if c['join']:
        print(c['id'], c['status'], '| root:', c['root_cause'], '| joins:', [j['edge'] for j in c['join']])
