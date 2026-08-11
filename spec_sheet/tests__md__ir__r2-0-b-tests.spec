// ============================================================================
// CHRON-LLM R2.0-B WORLD RUNTIME TEST & CONTRACT SPECIFICATION
// Version: v1.0 (SSOT Harmonized)
// Target File: tests/md/ir/r2-0-b-tests.spec
// Single Source of Truth Alignment: chron-llm-r2-world-runtime-obs-v1.0
// ============================================================================

PKG chron-r2-0-b

TYPES:
  PayloadRef = { hash:SHA256, size:U64, storage:Enum{:memory, :disk, :remote} }
  MemStore = HashTable<Str, PayloadRef>
  Node = { id:ID, type:Kw, payload_ref:PayloadRef, causal_depth:U64, meta:Map }
  Edge = { from:ID, to:ID, type:Enum{:causal, :eval} }
  Graph = { nodes:Map<ID, Node>, edges:[Edge] }
  
  World = { id:ID, graph:Ref<Graph>, mem:Ref<MemStore>, root:ID, head:ID, policy:Map, meta:Map, lifecycle:Enum{:created, :active, :inactive, :archived} }
  Registry = { worlds:[World], ancestry:Map<ID, ID>, active:ID|NIL, graph:Ref<Graph>, mem:Ref<MemStore> }

UTILS:
  %b-assert(cond:Bool, desc:Str) -> Bool | Error("R2.0-B invariant failed: ~A")
  %b-fixture() -> (g:Ref<Graph>, m:Ref<MemStore>, w:World, r:Registry)
    INIT g.nodes = {"root": {id:"root", type::root, payload_ref:{hash:"0", size:0, storage::memory}, causal_depth:0, meta:{}}};
         g.edges = [];
         m = make-memory-store();
         w = make-world("w-0", g, m, "root", "root", {}, {});
         r = register-world(new-registry(g, m), w)

OPS:
  make-world(id:ID, g:Ref<Graph>, m:Ref<MemStore>, root:ID, head:ID, policy:Map, meta:Map) -> World
  fork-world(parent:World, child_id:ID) -> World
  replace-world-metadata!(w:World, new_meta:Map) -> World
  kernel-commit-world!(w:World, node:Node) -> World
  register-world(r:Registry, w:World) -> Registry
  set-active-world(r:Registry, id:ID) -> Registry
  archive-world(r:Registry, id:ID) -> Registry
  replay-world(w:World) -> { id:ID, head_id:ID, policy:Map, meta:Map, hash:SHA256 }

TESTS (Public API Validation):
  b1-world-creation() -> Bool
    POST: unique(make-world().id); register-world(r, dup_w) -> Error

  b2-world-fork() -> Bool
    POST: child.root == parent.root; child.head == parent.head; child.graph == parent.graph; r'.ancestry[child.id] == parent.id

  b3-root-stability() -> Bool
    POST: kernel-commit-world!(w, n) => w'.root == w.root

  b4-head-independence() -> Bool
    POST: kernel-commit-world!(child, n) => parent.head unchanged

  b5-projection-isolation() -> Bool
    POST: build-prefill-state(w.graph, w.mem, target_id).context contains ONLY :causal nodes

  b6-metadata-cow() -> Bool
    POST: replace-world-metadata!(child, new_meta) => parent.meta unchanged AND child.graph == parent.graph

  b7-graph-sharing() -> Bool
    POST: fork-world(p, c_id) => c.graph eq p.graph AND c.mem eq p.mem

  b8-replay-independence() -> Bool
    POST: replay-world(w1).hash == replay-world(w2).hash IF (w1.graph == w2.graph AND w1.mem == w2.mem AND w1.policy == w2.policy)

  b9-world-isolation() -> Bool
    POST: replace-world-metadata!(w1, meta1) => w2.meta unchanged

  b10-commit-visibility() -> Bool
    POST: kernel-commit-world!(w, n) => exists_key(w'.graph.nodes, n.id) AND w'.head == n.id

  b11-registry-persistence() -> Bool
    POST: archive-world(r, w.id) => r'.active != w.id AND set-active-world(r', w.id) -> Error

INVARIANTS (System Contract Mapping):
  INV-1 (Graph-Unique-Node)   : Unique(keys(Graph.nodes))
  INV-2 (Mem-Content-Addr)    : ContentAddr(PayloadRef.hash == SHA256(content))
  INV-3 (World-Head-Valid)    : World.head in keys(World.graph.nodes)
  INV-4 (Commit-Atomic)       : Atomic(GraphAppend, HeadAdvance)
  INV-6 (Head-Commit-Truth)   : kernel-commit-world! == ONLY(head_advance)
  INV-7 (Replay-Determinism)  : Hash(Graph + MemStore + Policy) == PrefillHash
  INV-8 (Causal-Eval-Isolated): Evaluation edges (:eval) MUST NOT enter PrefillState or prompt context sequence
  INV-9 (Obs-Read-Only)       : Snapshot & Observation operations MUST NOT mutate World or Registry state
  INV_FORK_SHARE              : fork-world(p, c_id) -> c.graph eq p.graph AND c.mem eq p.mem
  INV_META_COW                : replace-world-metadata!(w, meta) -> Copy-on-Write metadata mutation; graph/mem shared