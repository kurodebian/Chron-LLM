TYPE IR_Event = {pos:int, phase:int, token:int, score:float}
TYPE DSL_Op = {type:sym, payload:any, meta:{}}
TYPE Candidate = {ops:[DSL_Op], status:"pending"}

OP emit(t,p,c) -> DSL_Op{type:"emit", payload:t, meta:{pos:p, conf:c}}
OP observe(type,s) -> DSL_Op{type:"observe", payload:type, meta:{score:s}}
OP propose(i,d) -> DSL_Op{type:"propose", payload:d, meta:{intent:i}}
OP branch(id,p) -> DSL_Op{type:"branch", payload:id, meta:{parent:p}}

STATE PhaseE = {buf:[IR_Event], out:[DSL_Op]}

TRANS translate(ir:IR_Event) -> DSL_Op:
  return emit(ir.token, ir.pos, ir.score)

TRANS process(e:IR_Event):
  State.out += [translate(e)]
  IF len(State.out) > N -> yield Candidate{ops:State.out}

INV Determinism: translate(IR_A) == translate(IR_A)
INV NonAuth: PhaseE.output != Canonical_State
INV NoCommit: NOT EXISTS(op in PhaseE.output | op.type=="commit")
INV Lossless: IR_Event.fields subset DSL_Op.meta