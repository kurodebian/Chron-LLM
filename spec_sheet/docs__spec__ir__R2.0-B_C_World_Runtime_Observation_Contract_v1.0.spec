// ============================================================================
// CHRON-LLM R2.0-B/C WORLD RUNTIME & OBSERVATION CONTRACT SPECIFICATION
// Version: v1.0 (SSOT Standardization)
// Single Source of Truth (SSOT) - Consolidated with Causal Context Spec v1.0
// Domain: World Runtime, Registry, and Read-Only Observation Layers
// ============================================================================

PKG: chron-llm-r2-world-runtime-obs-v1.0

TYPES:
  PayloadRef = { hash:SHA256, size:U64, storage:Enum{:memory, :disk, :remote} }
  MemStore = HashTable<Str, PayloadRef>
  Node = { id:ID, type:Kw, payload_ref:PayloadRef, causal_depth:U64, meta:Map }
  Edge = { from:ID, to:ID, type:Enum{:causal, :eval} }
  Graph = { nodes:Map<ID, Node>, edges:[Edge] }
  
  Eval = { id:ID, score:Float, eval_type:Kw, content:Str }
  ContextNode = { id:ID, type:Kw, content:Str }
  FeedbackContext = { target_id:ID, feedbacks:Map<ID, [Eval]> }
  PrefillState = { context:[ContextNode], target_id:ID, hash:SHA256 }
  
  World = { id:ID, graph:Ref<Graph>, mem:Ref<MemStore>, root:ID, head:ID, policy:Map, meta:Map, lifecycle:Enum{:created, :active, :inactive, :archived} }
  Registry = { worlds:[World], ancestry:Map<ID, ID>, active:ID|NIL, graph:Ref<Graph>, mem:Ref<MemStore> }
  
  WorldObs = { ver:U16, world_id:ID, root_id:ID, head_id:ID, policy:Map, meta:Map, lifecycle:Enum, parent_id:ID|NIL }
  RegistryObs = { ver:U16, world_ids:[ID], active_id:ID|NIL, archived_ids:[ID] }
  AncestryObs = { world_id:ID, parent_id:ID|NIL, path:[ID] }
  DiffObs = { changed:Bool, fields:[Str] }

INVARIANTS:
  INV-1 (Graph-Unique-Node)   : Unique(keys(Graph.nodes))
  INV-2 (Mem-Content-Addr)    : ContentAddr(PayloadRef.hash == SHA256(content))
  INV-3 (World-Head-Valid)    : World.head in keys(World.graph.nodes)
  INV-4 (Commit-Atomic)       : Atomic(GraphAppend, HeadAdvance)
  INV-5 (Obs-Primitive)       : Type(x) in {null, bool, str, num, char, kw, list}
  INV-6 (Head-Commit-Truth)   : kernel-commit-world! == ONLY(head_advance)
  INV-7 (Replay-Determinism)  : Hash(Graph + MemStore + Policy) == PrefillHash
  INV-8 (Causal-Eval-Isolated): Evaluation edges (:eval) MUST NOT enter PrefillState or prompt context sequence
  INV-9 (Obs-Read-Only)       : Snapshot & Observation operations MUST NOT mutate World, Registry, or Graph state

OPERATIONS:
  make-memory-store() -> MemStore

  add-node!(g:Ref<Graph>, n:Node) -> Ref<Graph>
    PRE: !exists_key(g.nodes, n.id)
    RESTRICTED(CommitKernel)
    POST: g'.nodes == put(g.nodes, n.id, n)

  add-edge!(g:Ref<Graph>, e:Edge) -> Ref<Graph>
    PRE: exists_key(g.nodes, e.from) AND exists_key(g.nodes, e.to)
    RESTRICTED(CommitKernel)
    POST: g'.edges == append(g.edges, e)

  causal-subgraph(g:Ref<Graph>, target_id:ID) -> [Node]
    PURE
    FILTER: edge.type == :causal
    ORDER: Topological (Root -> Target)

  project-context(g:Ref<Graph>, m:Ref<MemStore>, target_id:ID) -> [ContextNode]
    PURE
    PRE: exists_key(g.nodes, target_id)
    LOGIC: Traverse causal ancestry -> Load content from MemStore -> Materialize ContextNode list

  project-feedback-context(g:Ref<Graph>, target_id:ID) -> FeedbackContext
    PURE
    PRE: exists_key(g.nodes, target_id)
    LOGIC: Traverse causal ancestors -> Query outgoing :eval edges for each ancestor -> Map NodeID to [Eval]

  canonical-prompt(ctx:[ContextNode]) -> Str
    PURE
    RULE: Deterministic string serialization maintaining node order

  build-prefill-state(g:Ref<Graph>, m:Ref<MemStore>, target_id:ID) -> PrefillState
    PURE
    PRE: exists_key(g.nodes, target_id)
    POST: context == project-context(g, m, target_id) AND hash == SHA256(canonical-prompt(context)) AND target_id == target_id

  make-world(id:ID, g:Ref<Graph>, m:Ref<MemStore>, root:ID, head:ID, policy:Map, meta:Map) -> World
    PRE: exists_key(g.nodes, root) AND exists_key(g.nodes, head)
    POST: w.graph == g AND w.mem == m AND w.lifecycle == :created

  fork-world(parent:World, child_id:ID) -> World
    PRE: parent.id != child_id
    POST: child.graph == parent.graph AND child.mem == parent.mem AND child.root == parent.root AND child.head == parent.head

  replace-world-metadata!(w:World, new_meta:Map) -> World
    POST: w'.meta == new_meta AND w'.graph == w.graph (CoW)

  kernel-commit-world!(w:World, node:Node) -> World
    PRE: !exists_key(w.graph.nodes, node.id)
    RESTRICTED(CommitKernel)
    SEQ: add-node!(w.graph, node); w.head = node.id
    POST: w'.head == node.id

  replay-world(w:World) -> { id:ID, head_id:ID, policy:Map, meta:Map, hash:SHA256 }
    PURE
    POST: hash == SHA256(w.graph + w.mem + w.policy)

  register-world(r:Registry, w:World) -> Registry
    PRE: unique(w.id) AND (r.ancestry[w.id] != NIL -> exists(r.worlds, r.ancestry[w.id]))
    POST: r'.worlds == append(r.worlds, w)

  set-active-world(r:Registry, id:ID) -> Registry
    PRE: exists(r.worlds, id) AND find-world(r, id).lifecycle != :archived
    POST: r'.active == id AND find-world(r', id).lifecycle == :active

  archive-world(r:Registry, id:ID) -> Registry
    PRE: exists(r.worlds, id)
    POST: find-world(r', id).lifecycle == :archived AND (r.active == id -> r'.active == NIL)

  snapshot-world(w:World) -> WorldObs
    PURE
    RULE: Data-only snapshot, No mutation

  snapshot-registry(r:Registry) -> RegistryObs
    PURE
    RULE: Data-only snapshot, No mutation

  snapshot-ancestry(w:World) -> AncestryObs
    PURE
    RULE: Data-only snapshot, No mutation

  snapshot-diff(w1:World, w2:World) -> DiffObs
    PURE
    RULE: Data-only snapshot, No mutation
