TYPE Role = reply | temporal | bridge
TYPE Node = { id: ID, role: Role }
TYPE Edge = { from: ID, to: ID, rel: Role, strength: Float }
TYPE Graph = { nodes: [Node], edges: [Edge] }
TYPE Basin = { attractor: ID, nodes: [ID], mass: Int, ratio: Float }
TYPE Path = [ID]

OP next-event(g: Graph, u: ID) -> v: ID
  PRE: exists e in g.edges : e.from == u
  POST: v == argmax(e.to for e in g.edges where e.from == u by e.strength)

OP rollout*(g: Graph, start: ID, steps: Int) -> p: Path
  POST: len(p) == steps + 1
  POST: p[0] == start
  POST: forall i < steps : p[i+1] == next-event(g, p[i])

OP find-attractor(g: Graph, start: ID, steps: Int) -> a: ID
  POST: a == rollout*(g, start, steps)[-1]

OP find-cycle(p: Path) -> c: Path
  POST: c is subsequence of p
  POST: c[0] == c[-1]
  POST: len(c) > 1

OP find-recurrent-cycle(g: Graph, start: ID, steps: Int) -> c: Path
  POST: c == find-cycle(rollout*(g, start, steps))

OP build-basin-map(g: Graph, nodes: [ID], steps: Int) -> m: Map<ID, Basin>
  POST: forall n in nodes : m[find-attractor(g, n, steps)].nodes contains n
  POST: forall b in m.values : b.mass == len(b.nodes)
  POST: forall b in m.values : b.ratio == b.mass / len(nodes)

OP compute-sccs(g: Graph, nodes: [ID]) -> sccs: [[ID]]
  POST: partition(nodes) == sccs
  POST: forall s in sccs : strongly_connected(g, s)

INV Graph: forall e in g.edges : e.from in g.nodes AND e.to in g.nodes
INV Basin: forall b in basins : forall n in b.nodes : find-attractor(g, n, steps) == b.attractor