SPEC causal-subgraph v1.0
TYPE Node = {id: ID}
TYPE Edge = {from: ID, to: ID, type: Symbol}
TYPE Graph = {nodes: [Node], edges: [Edge]}
CONST CAUSAL = :CAUSAL

OP causal-subgraph(graph: Graph, target-id: ID) -> [Node]

PRE:
  exists(n in graph.nodes | n.id == target-id) -> OK
  else -> ERROR("Unknown target node")

STATE:
  seen: Set<ID> = {}
  ordered: [Node] = []

ALGO:
  visit(id: ID):
    if id in seen: return
    seen.add(id)
    for e in graph.edges:
      if e.type == CAUSAL and e.to == id:
        visit(e.from)
    ordered.append(get-node(graph, id))

  visit(target-id)
  return reverse(ordered)

INV:
  1. CausalPurity: forall(i < len(result)-1): exists(e in graph.edges | e.from == result[i].id AND e.to == result[i+1].id AND e.type == CAUSAL)
  2. TargetInclusion: result[-1].id == target-id
  3. RootFirst: result[0] has no incoming CAUSAL edges in result
  4. NonMutation: graph == graph_initial
  5. Determinism: output stable for fixed input

COMP: O(V*E)