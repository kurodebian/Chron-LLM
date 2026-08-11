// ============================================================================
// Chron-LLM R2.0 Graph Runtime: Causal Context Specification v1.0
// Single Source of Truth (SSOT) - Consolidated from prefill & projection specs
// ============================================================================

// ----------------------------------------------------------------------------
// 1. Domain Types & Data Structures (01-domain-model.spec Aligned)
// ----------------------------------------------------------------------------

TYPE PayloadRef = {
  hash: String,               // SHA-256 Hex string
  size: U64,                  // Size in bytes
  storage: Enum(:memory | :disk | :remote)
} : immutable

TYPE NodeID = String          // UUID v4 format
TYPE Keyword = String

TYPE Node = {
  id: NodeID,
  type: Keyword,
  payload_ref: PayloadRef,
  causal_depth: U64,
  metadata: Map<String, Any>
} : immutable

TYPE Edge = {
  from: NodeID,
  to: NodeID,
  type: Enum(:causal | :eval)
} : immutable

TYPE Graph = {
  nodes: Map<NodeID, Node>,
  edges: [Edge]
} : immutable

TYPE Eval = {
  id: NodeID,
  score: Float,
  eval_type: Keyword,
  content: String
} : immutable

TYPE ContextNode = {
  id: NodeID,
  type: Keyword,
  content: String
} : immutable

TYPE FeedbackContext = {
  target_id: NodeID,
  feedbacks: Map<NodeID, [Eval]>
} : immutable

TYPE PrefillState = {
  context: [ContextNode],
  target_id: NodeID,
  hash: String                // SHA256 of materialized canonical prompt
} : immutable


// ----------------------------------------------------------------------------
// 2. Fundamental Graph Primitives & Kernel Authority
// ----------------------------------------------------------------------------

OP get-node(g: Graph, id: NodeID) -> Node | nil
  : POST(RETURN g.nodes[id])

OP add-node!(g: Graph, n: Node) -> Graph
  : PRE(!exists_key(g.nodes, n.id))
  : RESTRICTED(CommitKernel)
  : INV(INV-GRAPH-APPEND)

OP add-edge!(g: Graph, e: Edge) -> Graph
  : PRE(get-node(g, e.from) != nil && get-node(g, e.to) != nil)
  : RESTRICTED(CommitKernel)
  : INV(INV-GRAPH-APPEND)

OP causal-subgraph(g: Graph, target: NodeID) -> [Node]
  : ALGO(topological_sort(traverse_incoming(:causal, target)))
  : INV(INV-DETERMINISTIC-ORDER, INV-CYCLE-SAFE)

OP associated-evals(g: Graph, id: NodeID) -> [Eval]
  : ALGO(traverse_outgoing(:eval, id))
  : INV(INV-INSERTION-ORDER-PRESERVED)


// ----------------------------------------------------------------------------
// 3. Context Projection & Evaluation Isolation
// ----------------------------------------------------------------------------

[INVARIANT: INV-CAUSAL-INTEGRITY]
"PrefillState.context MUST be derived exclusively from :causal edges via DAG traversal."

[INVARIANT: INV-EVAL-ISOLATION]
"Evaluation attachments (:eval edges) MUST NOT enter the causal ancestry traversal
 or affect the ordering and content of PrefillState."

[INVARIANT: INV-READ-ONLY]
"Operations project-context, project-feedback-context, and build-prefill-state
 MUST NOT mutate Graph or Store."

OP project-context(g: Graph, store: Store, target: NodeID) -> [ContextNode]
  PRE: exists_key(g.nodes, target) && store.readable
  POST: 
    nodes = causal-subgraph(g, target)
    RETURN map(n -> {
      id: n.id,
      type: n.type,
      content: store.load(n.payload_ref) || ""
    }, nodes)

OP project-feedback-context(g: Graph, target: NodeID) -> FeedbackContext
  PRE: exists_key(g.nodes, target)
  POST:
    nodes = causal-subgraph(g, target)
    RETURN {
      target_id: target,
      feedbacks: reduce(acc, n -> acc.put(n.id, associated-evals(g, n.id)), {}, nodes)
    }


// ----------------------------------------------------------------------------
// 4. Prefill State Construction & Determinism
// ----------------------------------------------------------------------------

[INVARIANT: INV-PREFILL-DET]
"Given identical Graph, Store, target NodeID, and custom builder, build-prefill-state
 MUST produce identical PrefillState output and state hash across all executions."

[INVARIANT: INV-HASH-IDENTITY]
"PrefillState.hash MUST exactly equal SHA256(materialized_prompt_string)."

[INVARIANT: INV-BOUNDARY-ISOLATION]
"PrefillState represents context topology and prompt materialization ONLY.
 It MUST NOT contain KV-Cache pointers or LLM generation runtime token buffers."

OP canonical-prompt(ctx: [ContextNode]) -> String
  : ALGO(concat(map(n -> format("(prompt (:node {n.id} :type {n.type} :content {n.content}))"), ctx)))
  : INV(INV-PRESERVES-NODE-ORDER, INV-DETERMINISTIC-SERIALIZATION)

OP build-prefill-state(
  g: Graph, 
  store: Store, 
  target: NodeID, 
  opts: { builder: Option<Function> } = { builder: nil }
) -> PrefillState
  PRE: exists_key(g.nodes, target) && (opts.builder == nil || returns_string(opts.builder))
  POST:
    ctx = project-context(g, store, target)
    prompt_builder = opts.builder || canonical-prompt
    prompt = prompt_builder(ctx)
    hash_digest = SHA256(prompt)
    RETURN {
      context: ctx,
      target_id: target,
      hash: hash_digest
    }