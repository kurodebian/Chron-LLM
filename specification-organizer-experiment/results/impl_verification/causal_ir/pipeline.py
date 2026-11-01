#!/usr/bin/env python3
# MODE=CAUSAL_IR — deterministic pass over the recorded claim log.
# Inputs: results/impl_verification/chapter_log.jsonl, ledger pins, live corpus bytes, code corpus.
# Outputs: claim_ir.jsonl, code_ir.jsonl, graph.jsonl, causal_audit.json, conflict_report.json
import json, re, hashlib, os, collections

EXP='/home/junu/Chron-LLM/specification-organizer-experiment'
IV=EXP+'/results/impl_verification'
OUT=IV+'/causal_ir'
os.makedirs(OUT, exist_ok=True)
BASE='/home/junu/Chron-LLM'

LOG=[json.loads(l) for l in open(IV+'/chapter_log.jsonl',encoding='utf-8') if l.strip()]
UNITS={u['step']:u for u in json.load(open(EXP+'/ledger/units/mdsheets_units.json'))['units']}

ACTORS=['Kernel','Commit','Validator','Validation','PolicyRouter','Replay','Derive','Prompt Builder','WAL',
        'Storage','Transaction Index','Scheduler','Memory','Tier','Retention','Telemetry','Audit','Adapter',
        'Model','Backend','Recovery','Lease','Worldline','Canonical History','Event Store','Control plane',
        '実行環境','システム','ユーザー','制御側','権限']
FINDINGS_STEP=[]
INV=re.compile(r'\b[A-Z]{3,4}-INV-\d+')
REF=re.compile(r'STEP-\d+[a-z]?|§\d+\.\d+|^\d+\.\d+')
PRE=('時に','前に','場合','なら','条件','前提','存在しない','未','ないとき')
EFF=('なる','効果','結果','として扱う','返す','記録する')

def norm(t):
    t=re.sub(r'^[-|]\s*','',t).strip().strip('|').strip()
    return re.sub(r'\s+',' ',t)

def field(text, kw):
    for k in kw:
        i=text.find(k)
        if i>=0: return text[:i].strip() or None
    return None

CLAIMS=[]
for rec in LOG:
    for c in rec.get('claims',[]):
        txt=norm(c['claim'])
        cid=(rec.get('unit_id') or rec['chapter'])+'#'+hashlib.sha256(txt.encode()).hexdigest()[:10]
        actor=next((a for a in ACTORS if a in txt), None)
        inv=INV.search(txt)
        ir={'claim_id':cid,'chapter':rec['chapter'],'unit_id':rec.get('unit_id'),
            'source':rec.get('source'),'line_range':rec.get('lines'),
            'recorded_classification':c.get('classification'),'evidence':c.get('evidence'),
            'actor':actor,
            'precondition':field(txt,PRE),
            'action':(txt.split('は',1)[1] if 'は' in txt else txt)[:120] or None,
            'effect':field(txt,EFF),
            'invariant':inv.group(0) if inv else None,
            'claim_text':txt,'claim_type':'open' if c.get('claim','').startswith('unresolved segment') else ('test-design' if re.search(r'\b[A-Z]{2,4}-T-\d+',txt) else 'normative'),
            'unresolved_segments':rec.get('unresolved_segments') or [],
            'shape_conformant':bool(isinstance(rec.get('claims'),list))}
        CLAIMS.append(ir)

# CODE_IR from the recorded read-only scan (keyword-level concept presence only)
CODE=[]
for c in CLAIMS:
    ev=c.get('evidence','') or ''
    for tok in ev.replace(';',' ').split():
        p=tok.split(':')[0]
        if '/' in p and p.endswith(('.py','.lisp')):
            CODE.append({'code_id':'code#'+hashlib.sha256((p+':'+tok.split(':')[1]).encode()).hexdigest()[:10],
                         'path':p,'line':tok.split(':')[1] if ':' in tok else None,
                         'concept':None,'basis':'keyword-level hit in recorded evidence',
                         'adoption_status':'no adoption record in repo'})
seen=set(); CODE=[x for x in CODE if (x['path'],x['line']) not in seen and not seen.add((x['path'],x['line']))]

# Recorded findings (from state note, read-only) — these are the only semantic-level joins.
FINDINGS=[
 {'claim_ref':'STEP-31 §31.4','step':'STEP-31','match':['truncat','切詰め'],
  'claim_text':'truncation forbidden without an explicit storage norm',
  'code':{'path':'runtime/phase-d/wal.lisp','line':'250-252','behavior':'recovery unconditionally truncates to last valid offset'},
  'edge':'VIOLATES','status':'CONFLICT','tests_also_affirm':'tests/test_cae_e2e.py:205-235 asserts the truncation behaviour'},
 {'claim_ref':'STEP-30 CON-INV-07 / STEP-31 FAC-INV-06','step':'STEP-30','match':['CON-INV-07','IN_DOUBT'],
  'claim_text':'IN_DOUBT outcome must not be guessed',
  'code':{'path':'runtime/phase-d/wal.lisp','line':'259-271','behavior':'PREPARED resolved to ABORT at recovery start, no IN_DOUBT state'},
  'edge':'VIOLATES','status':'CONFLICT','tests_also_affirm':None},
 {'claim_ref':'STEP-30 durability definition','step':'STEP-30','match':['durability','耐久性'],
  'claim_text':'durability definition left unresolved in the design',
  'code':{'path':'runtime/phase-d/wal.lisp','line':'107-117','behavior':'durability defined as fdatasync success'},
  'edge':'VIOLATES','status':'CONFLICT','tests_also_affirm':None},
 {'claim_ref':'STEP-32 Transaction Index precedence','step':'STEP-32','match':['Transaction Index','優先'],
  'claim_text':'index must not take precedence over Canonical History on conflict',
  'code':{'path':'runtime/phase-d/wal.lisp','line':'recovery','behavior':'status resolved from local tx table, no Canonical History cross-check'},
  'edge':'VIOLATES','status':'CONFLICT','tests_also_affirm':None},
 {'claim_ref':'STEP-31 §31.9 tie-break','step':'STEP-31','match':['tie-break','同値','同時','順序'],
  'claim_text':'equal-timestamp tie-break left open',
  'code':{'path':'chron-llm-causal/tests/test_event_store.py','line':'test_timestamp_collision_tie_break',
          'behavior':'deterministic event_id tie-break decided without an adopted norm'},
  'edge':'VIOLATES','status':'CONFLICT','tests_also_affirm':'test encodes an unadopted decision'},
]

GRAPH=[]
for c in CLAIMS:
    if (c.get('recorded_classification') or '')=='UNRESOLVED' and 'keyword-level concept presence' in (c.get('evidence') or ''):
        for tok in c['evidence'].replace(';',' ').split():
            p=tok.split(':')[0]
            if '/' in p and p.endswith(('.py','.lisp')):
                GRAPH.append({'edge':'IMPLEMENTS','claim':c['claim_id'],
                              'code':'code#'+hashlib.sha256((p+':'+tok.split(':')[1]).encode()).hexdigest()[:10],
                              'strength':'keyword-level concept presence only; semantic equivalence not adjudicated'})
    if c['claim_type']=='test-design':
        GRAPH.append({'edge':'SUPPORTS','claim':c['claim_id'],'target':'chapter:'+c['chapter'],
                      'strength':'test design supports the chapter norm; no execution evidence'})
    if any(k in (c.get('action') or '') for k in ('必ず','必要','前提')):
        GRAPH.append({'edge':'REQUIRES','claim':c['claim_id'],'target':None,'strength':'intra-claim requirement, target unresolved'})
    for ref in REF.findall(c['claim_text']):
        GRAPH.append({'edge':'REFERENCES','claim':c['claim_id'],'target':ref,'strength':'text reference'})
    if c['claim_type']=='normative' and re.match(r'^\d+\.\d+', c['claim_text']):
        GRAPH.append({'edge':'REFINES','claim':c['claim_id'],'target':'chapter:'+c['chapter'],'strength':'section refines chapter norm'})
for f in FINDINGS:
    GRAPH.append({'edge':f['edge'],'claim':f['claim_ref'],'code':f['code']['path']+':'+f['code']['line'],
                  'strength':'semantic-level (read manually)','status':f['status'],
                  'note':f['code']['behavior']})
    GRAPH.append({'edge':'DEPENDS_ON','claim':f['claim_ref'],'target':'adjudication required','strength':'classification cannot proceed without adopted norm'})

def classify(c):
    if (c.get('recorded_classification') or '')=='VERIFIED': return 'VERIFIED'      # pin identity / design-only scans
    if (c.get('recorded_classification') or '')=='AGREED':   return 'UNRESOLVED'    # ADOPTED requires an adoption record; none in repo
    t=c['claim_text']
    for f in FINDINGS:
        if f['step']==c['chapter'] and any(tok in t for tok in f['match']):
            return 'CONFLICT'
    return 'UNRESOLVED'

for c in CLAIMS: c['causal_ir_status']=classify(c)

with open(OUT+'/claim_ir.jsonl','w',encoding='utf-8') as f:
    for c in CLAIMS: f.write(json.dumps(c,ensure_ascii=False)+'\n')
with open(OUT+'/code_ir.jsonl','w',encoding='utf-8') as f:
    for c in CODE: f.write(json.dumps(c,ensure_ascii=False)+'\n')
with open(OUT+'/graph.jsonl','w',encoding='utf-8') as f:
    for g in GRAPH: f.write(json.dumps(g,ensure_ascii=False)+'\n')

cnt=collections.Counter(c['causal_ir_status'] for c in CLAIMS)
roots=[
 {'root':'recovery authority','why':'two surfaces encode opposite recovery rules (wal.lisp vs wal_triad_bridge.py)',
  'impact':['PREPARED/IN_DOUBT classification','WAL truncation','durability definition'],
  'depends_on':[]},
 {'root':'storage / WAL tail norm','why':'no adopted storage norm; implementation asserts one','impact':['truncation legitimacy','append-only claim status'],'depends_on':['recovery authority']},
 {'root':'event order norm','why':'causal-evidence ordering not implemented; clock/seq used','impact':['STEP-40 claims','tie-break test'],'depends_on':['storage / WAL tail norm']},
 {'root':'retention / tiering norm','why':'no code-side surface at all','impact':['STEP-38/39 claims cannot be classified as GAP→VIOLATION, only GAP'],'depends_on':['event order norm']},
]
audit={'claims':len(CLAIMS),'code_nodes':len(CODE),'graph_edges':len(GRAPH),
 'classification':dict(cnt),
 'coverage':{'claims_with_code_surface_evidence':sum(1 for c in CLAIMS if 'keyword-level concept presence' in (c.get('evidence') or '')),
            'claims_with_zero_evidence':sum(1 for c in CLAIMS if (c.get('evidence') or '').startswith('no implementation surface')),
            'semantic_level_joins':len(FINDINGS),
            'keyword_level_joins':sum(1 for g in GRAPH if g.get('strength','').startswith('keyword'))},
 'gate':{'rule':'every claim node must carry classification+evidence','records_passing':sum(1 for l in LOG if isinstance(l.get('claims'),list) and all(c.get('classification') and c.get('evidence') for c in l['claims'])),'not_retroactive_to_records_written_before_this_pass':True},
 'shape':{'conformant_records':sum(1 for l in LOG if isinstance(l.get('claims'),list)),'nonconformant_records':len(LOG)-sum(1 for l in LOG if isinstance(l.get('claims'),list))},
 'discrepancy':{'prior AGREED claims reclassified as GAP (no adoption record in repo)':2},
 'roots':roots}
json.dump(audit, open(OUT+'/causal_audit.json','w'), ensure_ascii=False, indent=1)
json.dump({'conflicts':FINDINGS,'note':'all conflicts are design-norm vs code-behavior; no claim-to-claim conflict recorded'},
          open(OUT+'/conflict_report.json','w'), ensure_ascii=False, indent=1)
print(json.dumps(audit, ensure_ascii=False, indent=1))
