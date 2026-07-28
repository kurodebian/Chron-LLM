NodeID
Edge = {from: NodeID, to: NodeID, rel: Any, strength: Float}
Graph = {nodes: [NodeID], edges: [Edge]}
Path = [NodeID]

next-event(G: Graph, n: NodeID) -> Edge | NIL
  Pre: n in G.nodes
  cands = [e | e in G.edges, e.from == n]
  if cands == [] return NIL
  return argmax(cands, e.strength)
  Post: result.from == n

rollout*(G: Graph, start: NodeID, steps: Int) -> Path
  Pre: start in G.nodes
  path = [start]
  curr = start
  for _ in range(steps):
    e = next-event(G, curr)
    if e == NIL break
    curr = e.to
    path += [curr]
  return path
  Post: len(path) <= steps + 1

find-attractor(G: Graph, start: NodeID, steps: Int) -> NodeID
  return last(rollout*(G, start, steps))

INV Determinism: Pure functions
INV NonMutating: G is read-only
INV Greedy: next-event selects max strength
INV Finite: len(rollout*) <= steps + 1