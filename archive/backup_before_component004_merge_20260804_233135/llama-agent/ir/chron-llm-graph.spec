TYPES
Event = {id, clock, causal_id, payload}
Node = {id, clock, class, event, causal_id}
Edge = {kind: :temporal | :causal, from: NodeID, to: NodeID}
Graph = {nodes: Hash<NodeID, Node>, edges: Vector<Edge>, parents: Hash<NodeID, NodeID>, latest_healthy: Hash<WorldID, NodeID>}
HealthyTable = Hash<CausalID, NodeID>
History = Vector<Node>

STATE
last_temporal_id: NodeID | nil
global_last_healthy_id: NodeID | nil
ht: HealthyTable

OPERATIONS
rebuild-graph-from-wal(wal: Vector<Event>) -> Graph
lift-to-graph(wal: Vector<Event>) -> Graph
add-node-to-graph(g: Graph, e: Event) -> Node
determine-node-class(e: Event) -> Class
find-parent-node-id(causal_id: ID, ht: HealthyTable, fallback: NodeID) -> NodeID
add-edge(g: Graph, kind: Kind, from: NodeID, to: NodeID)
graph-history(g: Graph, world_id: ID) -> History
clean-history() -> History

ALGORITHMS
lift-to-graph(wal):
  g = Graph{}
  last_temporal_id = nil
  ht = HealthyTable{}
  global_last_healthy_id = nil
  for e in wal:
    n = add-node-to-graph(g, e)
    if last_temporal_id != nil: add-edge(g, :temporal, last_temporal_id, n.id)
    parent_id = find-parent-node-id(n.causal_id, ht, global_last_healthy_id)
    if parent_id != nil: add-edge(g, :causal, parent_id, n.id)
    if n.class != :fault:
      ht[n.causal_id] = n.id
      global_last_healthy_id = n.id
    last_temporal_id = n.id
  return g

add-node-to-graph(g, e):
  n = Node{id=e.id, clock=e.clock, class=determine-node-class(e), event=e, causal_id=e.causal_id}
  g.nodes[n.id] = n
  return n

find-parent-node-id(causal_id, ht, fallback):
  if causal_id in ht: return ht[causal_id]
  return fallback

add-edge(g, kind, from, to):
  g.edges.append(Edge{kind, from, to})
  if kind == :causal: g.parents[to] = from

graph-history(g, world_id):
  curr = g.latest_healthy[world_id]
  hist = []
  while curr != nil:
    if curr.class == :dialogue: hist.prepend(curr)
    curr = g.parents[curr.id]
  return hist

INVARIANTS
INV: forall e in WAL, exists n in Graph.nodes where n.event == e
INV: Temporal edges form linear chain matching WAL order
INV: forall n in Graph.nodes where n.class == :fault, n.id not in HealthyTable.values
INV: Graph = f(WAL)