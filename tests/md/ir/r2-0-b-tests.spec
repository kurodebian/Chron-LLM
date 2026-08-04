PKG chron-r2-0-b

TYPES:
  World = { id: UUID, root: NodeRef, head: NodeRef, meta: Map, policy: Policy }
  Graph = { nodes: Set<Node>, edges: Set<Edge> }
  Store = InMemMap
  Registry = { worlds: Map<UUID, World>, active: UUID?, ancestry: Map<UUID, UUID> }
  Policy = { include-evaluations: Bool }
  Node = { id: String, payload: Any }

UTILS:
  %b-assert(cond: Bool, desc: Str) -> t | Error("R2.0-B invariant failed: ~A")
  %b-fixture() -> (graph: Graph, store: Store, policy: Policy, registry: Registry)
    INIT graph.nodes = {"root", "head"}; graph.edges = {(root->head)}
    INIT policy = (:include-evaluations nil); registry = new(graph, store)

OPS:
  make-world(registry, ...) -> World
  fork-world(parent: World) -> ChildWorld
  kernel-commit-world!(world: World, node: Node) -> Void
  register-world(registry: Registry, world: World) -> Void | Error
  list-worlds(registry: Registry) -> [World]
  archive-world(registry: Registry, id: UUID) -> Void

TESTS (Public API):
  b1-world-creation() -> t
    POST: make-world().id unique; register(dup_id) -> Error
  b2-world-fork() -> t
    POST: child.root == parent.root; child.head == parent.head; registry.ancestry[child.id] == parent.id
  b3-root-stability() -> t
    POST: kernel-commit-world!(w, n) => w.root unchanged
  b4-head-independence() -> t
    POST: kernel-commit-world!(child, n) => parent.head unchanged
  b5-projection-isolation() -> t
    POST: w1.policy != w2.policy => state disjoint
  b6-metadata-cow() -> t
    POST: update_meta(child, k, v) => parent.meta[k] == old_val
  b7-graph-sharing() -> t
    POST: child.graph eq parent.graph; child.store eq parent.store
  b8-replay-independence() -> t
    POST: replay(w1) == replay(w2) IF constitutional_input(w1) == constitutional_input(w2)
  b9-world-isolation() -> t
    POST: update_meta(w1, ...) => w2.meta unchanged
  b10-commit-visibility() -> t
    POST: kernel-commit-world!(w, n) => graph.nodes contains n; w.head == n
  b11-registry-persistence() -> t
    POST: list-worlds deterministic order; archive(w) => !active; set-active(archived) -> Error

INVARIANTS (System Rules):
  INV_ID_UNIQUE: forall w1,w2 in Registry.worlds: w1.id != w2.id
  INV_ID_NO_REUSE: deleted_ids intersect active_ids == empty
  INV_FORK_SHARE: fork(p) -> c.graph eq p.graph AND c.store eq p.store
  INV_ROOT_IMMUTABLE: commit(w, n) -> w.root constant
  INV_HEAD_LOCAL: commit(c, n) => parent.head unchanged
  INV_META_COW: mutate_meta(c) => parent.meta structurally shared; logical isolation
  INV_COMMIT_ATOMIC: kernel-commit-world!(w, n) -> (graph.add(n), w.head = n)
  INV_REPLAY_PURE: replay(w) == f(constitutional_input(w))
