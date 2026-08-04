// ============================================================================
// [DEPRECATED / SUPERSEDED]
// This file is no longer active. Logic has been migrated to:
//   graph-runtime/ir/chron-llm-r2-graph-runtime-causal-context-spec-v1.0.spec
// ============================================================================

TYPE Node = {id: ID, type: Enum, content: String, feedback: Any}
TYPE PrefillState = {context: [Node], target-id: ID, hash: String} : immutable

FN project-context(graph: Graph, store: Store, target-id: ID) -> [Node]
   PRE: graph.valid AND store.readable
   POST: returns ordered causal context list for target-id

FN canonical-prompt(context: [Node]) -> String
   ALGO: concat(map(n->"(prompt (:node {n.id} :type {n.type} :content {n.content} :feedback {n.feedback}))", context))
   INV: preserves_node_order AND deterministic

FN build-prefill-state(graph, store, target-id, include-evals=false, builder=canonical-prompt) -> PrefillState
   ctx = project-context(graph, store, target-id)
   prompt = builder(ctx)
   ASSERT type(prompt) == String
   hash = sha256-string(prompt)
   RETURN {context: ctx, target-id: target-id, hash: hash}

INV Determinism: build-prefill-state(g,s,t,b) -> same(PrefillState) given identical inputs
INV Immutability: PrefillState.fields are read-only post-construction
INV Identity: hash == sha256(builder(context))
INV Boundary: PrefillState != KVCache AND PrefillState != Generation