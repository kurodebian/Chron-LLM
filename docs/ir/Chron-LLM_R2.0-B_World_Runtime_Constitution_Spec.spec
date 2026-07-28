DOC_ID: CHRON-R2.0-B-WORLD-CONSTITUTION
STATUS: FROZEN
DEPS: Chron-LLM_R2.0-A_Graph_Runtime_Core_Constitution_Spec.md

TYPE GlobalState := { canonical-graph: Graph, memory-store: Memory }
TYPE World := {
    id: UUID,
    graph-ref: Graph,
    memory-ref: Memory,
    root-node: Node,
    head-node: Node,
    projection-policy: Policy,
    metadata: Map,
    lifecycle: LifecycleState
}
TYPE LifecycleState := CREATED | ACTIVE | INACTIVE | ARCHIVED
TYPE Registry := {
    worlds: Map<UUID, World>,
    active-world: UUID,
    ancestry: Map<UUID, UUID>
}

ROLE Kernel := Authority
ROLE Graph := Truth
ROLE World := ExecutionView

INV World.id UNIQUE & STABLE
INV World.graph-ref == GlobalState.canonical-graph
INV World.memory-ref == GlobalState.memory-store
INV World.root-node IMMUTABLE after creation
INV World.head-node REACHABLE(World.root-node, World.head-node, :causal)
INV World.head-node COMMITTED
INV World.projection-policy IMMUTABLE
INV World.metadata COPY_ON_WRITE
INV World ISOLATED (no direct mutation)
INV Replay DETERMINISTIC(Graph, Memory, WorldState)
INV Registry NON_AUTHORITATIVE

OP make-world(inputs) -> World
    PRE: inputs valid
    POST: World.id UNIQUE
    POST: World.root-node EXISTS(Graph)
    POST: World.lifecycle == CREATED

OP fork-world(parent: World) -> World
    PRE: parent EXISTS
    POST: child.root-node == parent.root-node
    POST: child.head-node == parent.head-node
    POST: child.projection-policy == parent.projection-policy
    POST: child.metadata == CoW(parent.metadata)
    POST: child.id != parent.id
    POST: child.lifecycle == CREATED

OP commit(node: Node) -> Void
    SEQ: Update(Graph) -> Update(World.head-node)
    PRE: node REACHABLE(World.root-node, node, :causal)
    POST: World.head-node == node

OP register-world(w: World) -> Void
OP find-world(id: UUID) -> World
OP active-world() -> World
OP set-active-world(id: UUID) -> Void
OP list-worlds() -> [World]

TRANS LifecycleState:
    CREATED -> ACTIVE
    ACTIVE -> INACTIVE
    INACTIVE -> ARCHIVED
    ARCHIVED !-> ACTIVE

TEST B1: make-world creates UNIQUE World
TEST B2: fork-world preserves ancestry
TEST B3: root-node IMMUTABLE
TEST B3.1: head-node REACHABLE(root-node, :causal)
TEST B4: child head updates !-> parent
TEST B5: projection-policy ISOLATED
TEST B6: metadata CoW
TEST B7: Graph/Memory SHARED
TEST B8: Replay DETERMINISTIC
TEST B9: Worlds ISOLATED
TEST B10: commit SEQ Graph -> World
TEST B11: Registry persists ID/ancestry
TEST B12: Kernel rejects unreachable head