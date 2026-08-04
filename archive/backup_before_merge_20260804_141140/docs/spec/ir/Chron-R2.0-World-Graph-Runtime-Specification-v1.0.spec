TYPES:
PayloadRef = {hash:Str, type:Kw, size:Int, storage:Kw}
MemStore = Map<Str, Bytes>
CausalNode = {id:Str, type:Kw, payload-ref:PayloadRef, meta:Any}
CausalEdge = {from:Str, to:Str, type:Kw}
CausalGraph = {nodes:Set<CausalNode>, edges:Set<CausalEdge>}
ContextNode = {id:Str, type:Kw, content:Str, feedbacks:List<Str>}
PrefillState = {context:List<ContextNode>, target-id:Str, hash:Str}
World = {id:Str, root:Str, head:Str, policy:Kw, meta:Any, lifecycle:Kw}
Registry = {worlds:Map<Str,World>, ancestry:Map<Str,Str>, active-id:Str?, graph:CausalGraph, memory:MemStore}
ObsWorld = {id:Str, root:Str, head:Str, policy:Kw, meta:Any, lifecycle:Kw, parent:Str?}
ObsRegistry = {ids:List<Str>, active:Str?, archived:List<Str>}
ObsAncestry = {child:Str, parent:Str, path:List<Str>}
ObsDiff = {changed:Bool, fields:List<Kw>}

OPS:
store-payload(store:MemStore, content:Str) -> PayloadRef:
  h = SHA256(content)
  store[h] = content
  return {hash:h, type:infer(content), size:len(content), storage:default}

load-payload(store:MemStore, ref:PayloadRef) -> Str:
  return store[ref.hash]

add-node!(graph:CausalGraph, node:CausalNode) -> Void:
  PRE: node.id not in graph.nodes
  graph.nodes += node

add-edge!(graph:CausalGraph, edge:CausalEdge) -> Void:
  PRE: edge.from in graph.nodes AND edge.to in graph.nodes
  graph.edges += edge

causal-subgraph(graph:CausalGraph, target:Str) -> List<CausalNode>:
  return DFS(graph, target, filter=:causal) | sort(root-first)

project-context(graph:CausalGraph, store:MemStore, target:Str, evals:Bool) -> List<ContextNode>:
  nodes = causal-subgraph(graph, target)
  return map(n -> {id:n.id, type:n.type, content:load-payload(store, n.payload-ref), feedbacks:if(evals) get-evals(n) else []})

canonical-prompt(ctx:List<ContextNode>) -> Str:
  return format(ctx)

build-prefill-state(graph:CausalGraph, store:MemStore, target:Str) -> PrefillState:
  ctx = project-context(graph, store, target, false)
  return {context:ctx, target-id:target, hash:SHA256(canonical-prompt(ctx))}

register-world(reg:Registry, world:World) -> Void:
  PRE: world.id not in reg.worlds
  reg.worlds[world.id] = world

set-active-world(reg:Registry, id:Str) -> Void:
  PRE: id in reg.worlds
  reg.active-id = id

archive-world(reg:Registry, id:Str) -> Void:
  w = reg.worlds[id]
  w.lifecycle = :archived
  if(reg.active-id == id) reg.active-id = nil

INVS:
INV: forall(w in Registry.worlds): w.graph == Registry.graph
INV: forall(w in Registry.worlds): w.memory == Registry.memory
INV: count(w in Registry.worlds where w.lifecycle == :active) <= 1
INV: Observation types subset {Str, Num, Kw, Char, List}