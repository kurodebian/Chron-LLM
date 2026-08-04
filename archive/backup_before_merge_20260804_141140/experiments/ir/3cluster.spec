Role = :reply | :temporal | :bridge
Relation = :reply | :temporal
Node = { id: Symbol, role: Role }
Edge = { from: Node, to: Node, relation: Relation, strength: Float[0.0, 1.0] }
Graph = { nodes: Node[], edges: Edge[] }
Basin = { attractor: Node[], nodes: Node[] }

make-3cluster-graph() -> Graph
compute-sccs(g: Graph) -> Node[][]
find-cycle(g: Graph) -> Node[]
find-attractor(g: Graph) -> Node[]
build-basin-map(g: Graph) -> Basin[]
rollout*(g: Graph, start: Node) -> Node[]
next-event(g: Graph, n: Node) -> Node

G = make-3cluster-graph()
G.nodes = [
  {id:a1, role: :reply}, {id:a2, role: :reply}, {id:a3, role: :reply},
  {id:b1, role: :temporal}, {id:b2, role: :temporal}, {id:b3, role: :temporal},
  {id:c1, role: :bridge}, {id:c2, role: :bridge}
]

G.edges = [
  {from:a1, to:a2, relation: :reply, strength: 0.9},
  {from:a2, to:a3, relation: :reply, strength: 0.9},
  {from:a3, to:a1, relation: :reply, strength: 0.9},
  {from:b1, to:b2, relation: :temporal, strength: 0.3},
  {from:b2, to:b3, relation: :temporal, strength: 0.3},
  {from:b3, to:b1, relation: :temporal, strength: 0.3},
  {from:c1, to:a1, relation: :reply, strength: 0.6},
  {from:c1, to:b1, relation: :temporal, strength: 0.4},
  {from:c2, to:a2, relation: :reply, strength: 0.4},
  {from:c2, to:b2, relation: :temporal, strength: 0.6}
]

INV |G.nodes| = 8
INV |G.edges| = 10
INV SCCs(G) = [{a1,a2,a3}, {b1,b2,b3}, {c1}, {c2}]
INV Attractors(G) = [{a1,a2,a3}, {b1,b2,b3}]
INV Deterministic(G) = True