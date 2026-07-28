TYPES
Node: ID
Graph: Map[Node, Node]
Attractor: Node
Basin: { attractor: Attractor, nodes: [Node], mass: Int, ratio: Float }

STATE
Graph: Immutable
Basin: Derived

OPERATIONS
find-attractor(g: Graph, n: Node, steps: Int) -> Attractor
build-basin-map(g: Graph, nodes: [Node], steps: Int) -> Map[Attractor, [Node]]:
  m = {}
  FOR n IN nodes:
    a = find-attractor(g, n, steps)
    m[a] += [n]
  RETURN m
build-basin-structure(map: Map[Attractor, [Node]], total: Int) -> [Basin]:
  RETURN [Basin(a, ns, LEN(ns), LEN(ns)/total) FOR (a, ns) IN map]

PRE_POST_CONDITIONS
build-basin-structure: PRE total > 0
build-basin-structure: POST SUM(b.ratio FOR b IN result) == 1.0

INVARIANTS
INV-PARTITION: FORALL n IN nodes, EXISTS! b IN basins s.t. n IN b.nodes
INV-MASS: FORALL b IN basins, b.mass == LEN(b.nodes)
INV-RATIO: SUM(b.ratio FOR b IN basins) == 1.0
INV-OBS: POST(g) == PRE(g)