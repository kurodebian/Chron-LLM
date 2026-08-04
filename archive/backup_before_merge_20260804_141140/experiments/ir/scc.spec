TYPE Node = ID
TYPE Edge = {from: Node, to: Node}
TYPE Graph = {nodes: [Node], edges: [Edge]}
TYPE SCC = [Node]
TYPE SCCList = [SCC]

OP successors(G: Graph, n: Node) -> [Node]
  = [e.to | e in G.edges if e.from == n]

OP predecessors(G: Graph, n: Node) -> [Node]
  = [e.from | e in G.edges if e.to == n]

OP dfs-order(G: Graph, roots: [Node]) -> [Node]
  STATE: visited: Set<Node>, order: [Node]
  INIT: visited={}, order=[]
  FOR r IN roots: IF r not in visited: visit(r)
  RETURN order
  SUB visit(u):
    visited.add(u)
    FOR v IN successors(G, u): IF v not in visited: visit(v)
    order.push(u)

OP dfs-component(G: Graph, start: Node, visited: Set<Node>) -> SCC
  STATE: comp: [Node]
  INIT: comp=[]
  rev_visit(start)
  RETURN comp
  SUB rev_visit(u):
    visited.add(u)
    comp.push(u)
    FOR v IN predecessors(G, u): IF v not in visited: rev_visit(v)

OP compute-sccs(G: Graph, nodes: [Node]) -> SCCList
  PRE: nodes subset G.nodes
  ALGO:
    order = dfs-order(G, nodes)
    visited = {}
    sccs = []
    FOR n IN reverse(order):
      IF n not in visited:
        sccs.push(dfs-component(G, n, visited))
    RETURN sccs

INV-PARTITION: union(compute-sccs(G, nodes)) == nodes
INV-DISJOINT: forall i!=j: sccs[i] intersect sccs[j] == {}
INV-MUTUAL: forall c in sccs, forall u,v in c: reachable(G, u, v) AND reachable(G, v, u)
INV-PURE: G_before == G_after
INV-DET: same(G, nodes) -> same(sccs)
INV-COMP: O(V+E)