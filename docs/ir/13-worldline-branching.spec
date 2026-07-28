TYPE CausalID
TYPE Worldline = {id: CausalID, state: Any}
TYPE Event = {type: {discontinuity, abort, drift, stagnation}, count: Int}
STATE S = {current_id: CausalID, canonical_id: CausalID, drift_cnt: Int, stag_cnt: Int, history: Map<CausalID, Worldline>}
PRED branch(E) = (E.type in {discontinuity, abort}) | (E.type == drift & E.count >= 3) | (E.type == stagnation & E.count >= 5)
OP Branch(S, E) -> S':
  PRE: branch(E)
  S'.current_id = gen_id()
  KV_Cache = null
  path = Traverse(Graph, causal_edges)
  Prefill = Construct(path)
  S'.history[S'.current_id] = {id: S'.current_id, state: Prefill}
  S'.drift_cnt = 0
  S'.stag_cnt = 0
OP Commit(id, S) -> S':
  S'.canonical_id = id
INV: Branch deterministic
INV: history replayable
INV: w in S.history & w.id != S.current_id => w immutable
INV: S.canonical_id mutable iff op == Commit