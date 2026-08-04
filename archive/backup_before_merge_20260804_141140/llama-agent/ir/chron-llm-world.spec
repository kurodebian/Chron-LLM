SPEC WorldService
TYPES
  WorldID = Int
  NodeID = Int
  BranchEvent = { kind: :branch, causal_id: WorldID, payload: { parent_node: NodeID, parent_world: WorldID } }
  CausalNode = { id: NodeID, causal_id: WorldID, class: :fault | :valid }
STATE
  wal_world_counter: WorldID
  graph: [CausalNode]
  wal: [Event]
OPS
  stage_branch_world(parent_world_id: WorldID) -> (WorldID, BranchEvent)
  get_latest_node_in_world(world_id: WorldID) -> CausalNode | NIL
PRE_POST
  stage_branch_world:
    PRE: parent_world_id valid
    POST: wal_world_counter incremented
    POST: BranchEvent staged in wal
    POST: returned WorldID unique
  get_latest_node_in_world:
    PRE: world_id valid
    POST: result.class != :fault
    POST: result.id == max([n.id for n in graph if n.causal_id == world_id])
ALGORITHMS
  stage_branch_world(p_wid):
    n_wid = wal_world_counter + 1
    wal_world_counter = n_wid
    p_node = get_latest_node_in_world(p_wid)
    p_nid = if p_node == NIL then 0 else p_node.id
    evt = { kind: :branch, causal_id: n_wid, payload: { parent_node: p_nid, parent_world: p_wid } }
    wal = wal + [evt]
    return (n_wid, evt)
  get_latest_node_in_world(wid):
    cands = [n for n in graph if n.causal_id == wid && n.class != :fault]
    return if cands == [] then NIL else max(cands, key=n.id)
INVARIANTS
  INV: wal_world_counter monotonic
  INV: BranchEvent.kind == :branch
  INV: RootParent == 0
  INV: Query excludes :fault nodes
  INV: Query returns single latest node per WorldID
CONSTRAINTS
  Phase1: Implemented=[stage_branch_world, get_latest_node_in_world]
  Phase1: Omitted=[commit, merge, replay, validation]