SPEC WorldService

TYPES
  WorldID      = Int
  NodeID       = Int
  NodeClass    = :valid | :fault
  WorldHealth  = :healthy | :degraded
  IdentityError = :identity_allocation_failed

  BranchPayload =
    { parent_node_id: NodeID,
      parent_world_id: WorldID }

  BranchProposal =
    { kind: :branch,
      causal_id: WorldID,
      payload: BranchPayload }

  CausalNode =
    { id: NodeID,
      causal_id: WorldID,
      class: NodeClass }

CANONICAL
  Canonical EventLog   -- SSOT managed by EventStore / Kernel

PROJECTIONS
  graph : [CausalNode]

REQUIRES
  allocate_world_id() -> WorldID | IdentityError

COMMANDS
  stage_branch_world(parent_world_id: WorldID)
    -> BranchProposal | IdentityError

QUERIES
  get_latest_node(world_id: WorldID) -> CausalNode | NIL
  get_latest_valid_node(world_id: WorldID) -> CausalNode | NIL
  get_world_health(world_id: WorldID) -> WorldHealth

PRE_POST
  stage_branch_world:
    PRE: parent_world_id == 0
         OR get_latest_valid_node(parent_world_id) != NIL
    POST: returns BranchProposal OR IdentityError

  get_latest_node:
    PRE: world_id valid
    POST: result is latest node in Projection

  get_latest_valid_node:
    PRE: world_id valid
    POST: result.class == :valid

  get_world_health:
    PRE: world_id valid
    POST: result == :healthy
          iff get_latest_valid_node(world_id) != NIL
          AND no fault node exists in world_id

ERROR CONTRACT
  stage_branch_world:
    IF allocate_world_id() returns IdentityError
    THEN returns IdentityError
         AND Canonical EventLog unchanged
         AND Projection unchanged

ALGORITHMS
  stage_branch_world(parent_world_id):
    parent = get_latest_valid_node(parent_world_id)
    wid_res = allocate_world_id()
    if wid_res is IdentityError: return IdentityError
    proposal =
      { kind: :branch,
        causal_id: wid_res,
        payload:
          { parent_node_id: (parent == NIL ? 0 : parent.id),
            parent_world_id: parent_world_id } }
    return proposal

  get_latest_node(world_id):
    candidates = graph where causal_id == world_id
    return latest(candidates)

  get_latest_valid_node(world_id):
    candidates = graph where causal_id == world_id AND class == :valid
    return latest(candidates)

  get_world_health(world_id):
    latest = get_latest_valid_node(world_id)
    if latest == NIL: return :degraded
    if exists fault node in graph where causal_id == world_id: return :degraded
    return :healthy

PROJECTION CONTRACT
  graph == Project(Canonical EventLog)

ORDER CONTRACT
  Projection Order == Canonical EventLog sequence number
  Canonical EventLog sequence number MUST be monotonic
  latest(candidates) == element with maximum Projection Order
  Replay MUST preserve identical Projection Order

QUERY CONTRACT
  Queries MUST NOT mutate Canonical or Projection
  Queries MUST observe a single Projection snapshot

INVARIANTS
  INV: WorldID unique
  INV: NodeID unique
  INV: Root World ⇔ parent_world_id == 0 AND parent_node_id == 0
  INV: parent_node_id == 0 OR parent node exists
  INV: Graph is acyclic
  INV: Project(Canonical EventLog) produces identical graph

PROPOSAL CONTRACT   -- ★補強ブロック①
  BranchProposal MUST satisfy:
    kind == :branch
    causal_id MUST be unique
    payload.parent_world_id == requested parent_world_id
    payload.parent_node_id == 0 OR referenced node exists

WORLD ID CONTRACT   -- ★補強ブロック②
  valid WorldID means:
    WorldID exists
    OR WorldID == 0 (Root World)

  Unknown WorldID:
    MUST return error
    MUST NOT synthesize node

CONSTRAINTS
  Phase1:
    [stage_branch_world, get_latest_node,
     get_latest_valid_node, get_world_health]

  Phase2:
    [commit, merge, replay, validation,
     extended_health_states]

  Phase3:
    [snapshot, garbage_collection, archival]
