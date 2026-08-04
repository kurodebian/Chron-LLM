// ============================================================================
// Chron-LLM R2.0 Graph Runtime: Causal Context Specification v1.0
// Single Source of Truth (SSOT) - Consolidated from prefill & projection specs
// ============================================================================

// ----------------------------------------------------------------------------
// 1. Domain Types & Data Structures
// ----------------------------------------------------------------------------

TYPE Node = {
  id: ID,
  type: Keyword,
  payload_ref: Ref,
  metadata: Any
} : immutable

TYPE Edge = {
  from: ID,
  to: ID,
  type: Enum(:causal | :eval)
}

TYPE Graph = {
  nodes: [Node],
  edges: [Edge]
}

TYPE Eval = {
  id: ID,
  score: Float,
  eval_type: Keyword,
  content: String
}

TYPE ContextNode = {
  id: ID,
  type: Keyword,
  content: String,
  feedbacks: [Eval]
}

TYPE PrefillState = {
  context: [ContextNode],
  target_id: ID,
  hash: String
} : immutable


// ----------------------------------------------------------------------------
// 2. Fundamental Graph Primitive Operations
// ----------------------------------------------------------------------------

OP get-node(g: Graph, id: ID) -> Node | nil

OP add-node!(g: Graph, n: Node) 
  : PRE(!exists(n' in g.nodes | n'.id == n.id))
  : RESTRICTED(CommitKernel)

OP add-edge!(g: Graph, e: Edge) 
  : PRE(get-node(g, e.from) != nil && get-node(g, e.to) != nil)
  : RESTRICTED(CommitKernel)

OP causal-subgraph(g: Graph, target: ID) -> [Node]
  : traverse_incoming(:causal, target)
  : INV(deterministic_order, cycle_safe)

OP associated-evals(g: Graph, id: ID) -> [Eval]
  : traverse_outgoing(:eval, id)
  : INV(insertion_order_preserved)


// ----------------------------------------------------------------------------
// 3. Context Projection & Evaluation Isolation
// ----------------------------------------------------------------------------

[INVARIANT: INV-CAUSAL-INTEGRITY]
"PrefillState.context MUST be derived exclusively from :causal edges and DAG traversal."

[INVARIANT: INV-EVAL-ISOLATION]
"Evaluation attachments (:eval edges) are optional metadata and MUST be kept completely
 disjoint from the causal ancestry graph structure and prefill prompt sequence ordering."

[INVARIANT: INV-READ-ONLY]
"Operations project-context and build-prefill-state MUST NOT mutate Graph or Store."

OP project-context(g: Graph, store: Store, target: ID, inc_evals: Boolean = false) -> [ContextNode]
  PRE: exists(n in g.nodes | n.id == target) && store.readable
  POST: 
    nodes = causal-subgraph(g, target)
    RETURN map(n -> {
      id: n.id,
      type: n.type,
      content: store.load(n.payload_ref) || "",
      feedbacks: IF inc_evals THEN associated-evals(g, n.id) ELSE []
    }, nodes)


// ----------------------------------------------------------------------------
// 4. Prefill State Construction & Determinism
// ----------------------------------------------------------------------------

[INVARIANT: INV-DETERMINISM]
"Given identical Graph, Store, target ID, and builder, build-prefill-state MUST produce
 an identical PrefillState output and state hash."

[INVARIANT: INV-HASH-IDENTITY]
"PrefillState.hash MUST exactly equal SHA256(prompt)."

[INVARIANT: INV-BOUNDARY-ISOLATION]
"PrefillState represents context topology and prompt materialization ONLY.
 It MUST NOT be confused with KV-Cache or LLM Generation Runtime tokens."

OP canonical-prompt(ctx: [ContextNode]) -> String
  : ALGO(concat(map(n -> format("(prompt (:node {n.id} :type {n.type} :content {n.content}))", ctx))))
  : INV(preserves_node_order, deterministic_serialization)

OP build-prefill-state(
  g: Graph, 
  store: Store, 
  target: ID, 
  opts: { inc_evals: Boolean, builder: Option<Function> }
) -> PrefillState
  PRE: opts.builder == nil || returns_string(opts.builder)
  POST:
    ctx = project-context(g, store, target, opts.inc_evals)
    prompt_builder = opts.builder || canonical-prompt
    prompt = prompt_builder(ctx)
    hash_digest = SHA256(prompt)
    RETURN {
      context: ctx,
      target-id: target,
      hash: hash_digest
    }