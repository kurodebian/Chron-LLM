TYPES:
Event = {idx: Int, clk: Int, wld: Int, kind: Sym, pay: {txt: Str, tgt: Str?, meta: Map}}
WAL = {store: [Event], clk: Int, stage: [Event]}
NodeCls = Dialogue | Tool | Fault | Meta
Node = {id: Int, ev: Event, cls: NodeCls, clk: Int, wld: Int}
Edge = {src: Int, dst: Int, typ: Temporal | Causal}
Graph = {nodes: Map<Int, Node>, edges: [Edge], par: Map<Int, Int>}
HTable = Map<Int, Int>
Kernel = {wal: WAL, cur-wld: Int}

OPS:
append(k, kind, pay) -> Event:
  k.wal.clk++
  e = {idx: len(k.wal.store), clk: k.wal.clk, wld: k.cur-wld, kind: kind, pay: pay}
  k.wal.store.append(e)
  return e

stage(k, kind, pay) -> Event:
  e = {idx: len(k.wal.store)+len(k.wal.stage), clk: k.wal.clk+1, wld: k.cur-wld, kind: kind, pay: pay}
  k.wal.stage.append(e)
  return e

discard(k) -> Void:
  k.wal.stage = []

commit(k) -> Void:
  for e in reverse(k.wal.stage):
    k.wal.clk++
    e.clk = k.wal.clk
    e.idx = len(k.wal.store)
    k.wal.store.append(e)
  k.wal.stage = []

branch(k, new-wld) -> Void:
  k.cur-wld = new-wld

classify(kind) -> NodeCls:
  if kind in [:user-msg, :asst-reply] -> Dialogue
  if kind in [:tool-start, :tool-timeout, :tool-abort, :tool-commit] -> Tool
  if kind in [:struct-fault, :tool-fault] -> Fault
  else -> Meta

lift(k) -> Graph:
  g = {nodes: {}, edges: [], par: {}}
  ht = {}
  last = null
  for e in k.wal.store:
    n = {id: e.idx, ev: e, cls: classify(e.kind), clk: e.clk, wld: e.wld}
    g.nodes[n.id] = n
    if last != null:
      g.edges.append({src: last.id, dst: n.id, typ: Temporal})
      g.par[n.id] = last.id
    if n.cls != Fault:
      if ht[e.wld] != null:
        g.edges.append({src: ht[e.wld], dst: n.id, typ: Causal})
      ht[e.wld] = n.id
    last = n
  return g

clean(g, wld) -> [Event]:
  curr = argmax n in g.nodes where n.wld == wld
  hist = []
  while curr != null:
    if curr.cls == Dialogue: hist.prepend(curr.ev)
    curr = g.par[curr.id]
  return hist

INV:
monotonic-clk: forall e1,e2 in WAL.store: e1.idx < e2.idx -> e1.clk < e2.clk
fault-isolation: forall n in Graph.nodes: n.cls == Fault -> n not in clean(Graph, n.wld)
causal-scope: forall e in Graph.edges: e.typ == Causal -> g.nodes[e.src].wld == g.nodes[e.dst].wld
history-recon: forall g in Graph: clean(g, wld) is deterministic