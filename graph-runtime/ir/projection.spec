TYPE context-node = { id: ID, type: Keyword, content: String, feedbacks: [String] }
OP associated-evaluations(g: Graph, nid: ID) -> [ID]: collect(e.to FOR e IN g.edges IF e.type==`:eval` && e.from==nid) ORDER BY insertion
OP project-context(g: Graph, s: Store, tid: ID, inc_evals: Bool=false) -> [context-node]:
  ancestry = causal-subgraph(g, tid)
  RETURN map(n IN ancestry -> {
    id: n.id, type: n.type, content: load-payload(s, n.payload-ref)||"",
    feedbacks: IF inc_evals THEN [load-payload(s, g.nodes[eid].payload-ref) FOR eid IN associated-evaluations(g, n.id)] ELSE nil
  })
INV project-context -> !mutate(g), !mutate(s), deterministic(inputs)
INV context-node.content == materialized(payload-ref)