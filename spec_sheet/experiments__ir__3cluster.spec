import "chron-llm-spec-v0.2.spec" as SOT;

// Test Fixture: Concrete 3-Cluster Topology Instance & Regression Assertions

G = SOT.make-3cluster-graph()

G.nodes = [
  {id: a1, role: :reply, ts: 0},
  {id: a2, role: :reply, ts: 1},
  {id: a3, role: :reply, ts: 2},
  {id: b1, role: :temporal, ts: 0},
  {id: b2, role: :temporal, ts: 1},
  {id: b3, role: :temporal, ts: 2},
  {id: c1, role: :bridge, ts: 0},
  {id: c2, role: :bridge, ts: 1}
]

G.edges = [
  {from: a1, to: a2, rel: :reply, str: 0.9, cnt: 1},
  {from: a2, to: a3, rel: :reply, str: 0.9, cnt: 1},
  {from: a3, to: a1, rel: :reply, str: 0.9, cnt: 1},
  {from: b1, to: b2, rel: :temporal, str: 0.3, cnt: 1},
  {from: b2, to: b3, rel: :temporal, str: 0.3, cnt: 1},
  {from: b3, to: b1, rel: :temporal, str: 0.3, cnt: 1},
  {from: c1, to: a1, rel: :reply, str: 0.6, cnt: 1},
  {from: c1, to: b1, rel: :temporal, str: 0.4, cnt: 1},
  {from: c2, to: a2, rel: :reply, str: 0.4, cnt: 1},
  {from: c2, to: b2, rel: :temporal, str: 0.6, cnt: 1}
]

INV |G.nodes| = 8
INV |G.edges| = 10
INV SCCs(G) = [{a1, a2, a3}, {b1, b2, b3}, {c1}, {c2}]
INV Attractors(G) = [{a1, a2, a3}, {b1, b2, b3}]
INV Deterministic(G) = True
