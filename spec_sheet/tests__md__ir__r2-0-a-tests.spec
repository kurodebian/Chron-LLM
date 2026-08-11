PKG chron-r2-0-a

TYPE Node = {id: Str, role: :sys | :user | :eval}
TYPE Edge = {src: Str, dst: Str, type: :causal | :eval}
TYPE Graph = {nodes: [Node], edges: [Edge]}
TYPE Store = Map<Ref, Payload>

FUNC run-r2-0-a-tests() -> Bool
  POST: res == T iff t1..t6 pass

FUNC %assert(cond: Bool, msg: Str) -> Bool | Error
  INV: !cond -> error("R2.0-A invariant failed: ~A", msg)

FUNC %fixture(with-eval: Bool = T) -> (Graph, Store)
  BODY:
    g := {nodes:[], edges:[]}; s := {}
    add_node(g, "s", :sys); add_node(g, "p", :user)
    add_edge(g, "s", "p", :causal)
    IF with-eval: add_node(g, "e", :eval); add_edge(g, "p", "e", :eval)
    RETURN (g, s)

FUNC t1-memory-determinism() -> Bool
  INV: store(s, x).ref == store(s, y).ref where x==y
  INV: load(s, ref) == original_payload
  INV: payload_immutable(ref)

FUNC t2-graph-replay() -> Bool
  INV: causal_subgraph(g, "p") order == ["s", "p"]
  INV: causal_subgraph(g, n) deterministic

FUNC t3-view-separation() -> Bool
  INV: view(g, "p").nodes excludes :eval unless flag(:include-evals)

FUNC t4-context-projection() -> Bool
  PRE: include-evaluations == T
  INV: project(g).order == [SysFact, UserFact]
  INV: feedbacks linked to nodes

FUNC t5-prefill-hash-stability() -> Bool
  INV: build_prefill(g, s).hash constant for identical inputs

FUNC t6-evaluation-independence() -> Bool
  INV: hash(build_prefill(g_eval)) == hash(build_prefill(g_no_eval))