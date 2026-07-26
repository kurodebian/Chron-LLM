Type WorldID = Int
Type NodeID = Int
Type EventKind = :branch
Type BranchEvent = {Kind: EventKind, CausalID: WorldID, Payload: {ParentNodeID: NodeID, ParentWorldID: WorldID}}
Type ImmuneStatus = :ok | :degraded

State wal-world-counter: Int
State Graph: {WorldID: Node}
State WAL: Event[]

Op stage-branch-world(Graph, WAL, ParentWorldID: WorldID) -> (NewWorldID: WorldID, BranchEvent)
Op check-immune-status(Graph, WorldID: WorldID) -> ImmuneStatus
Op get-latest-node-in-world(Graph, WorldID: WorldID) -> Node | Null
Op stage-event(Kind: EventKind, CausalID: WorldID, Payload: Any) -> Event
Op clean-history(Graph, WorldID: WorldID) -> History | Null

stage-branch-world(Graph, WAL, ParentWorldID):
  Pre: ParentWorldID valid
  new-id = wal-world-counter++
  latest = get-latest-node-in-world(Graph, ParentWorldID)
  parent-node-id = (latest != Null) ? latest.event.node-id : 0
  evt = stage-event(Kind=:branch, CausalID=new-id, Payload={ParentNodeID: parent-node-id, ParentWorldID: ParentWorldID})
  Post: wal-world-counter = new-id
  Post: evt.Status = Staged
  return (new-id, evt)

check-immune-status(Graph, WorldID):
  h = clean-history(Graph, WorldID)
  return (h != Null) ? :ok : :degraded

INV(WorldID): Unique
INV(BranchEvent): ParentWorldID = Immutable
INV(BranchEvent): ParentNodeID -> CommittedNode
INV(BranchEvent): Status = Staged
INV(Immune): HistoryExists -> Status = :ok