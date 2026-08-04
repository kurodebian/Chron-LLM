TYPES:
Symbol = :user-message | :assistant-reply | :branch | :ok | :degraded
HistoryEntry = {kind: Symbol, text: String, clock: Integer}
ContextObject = {system_prompt: String?, history: [HistoryEntry], memory_context: Any?, metadata: Any?}
KernelState = {world_id: Integer, health: Symbol, context: ContextObject}
Kernel = {wal: WAL, graph: Graph?, current_world: Integer}

INIT:
make-chron-kernel() -> Kernel
  wal = init_wal()
  graph = nil
  current_world = 100
  return {wal, graph, current_world}

OPS:
kernel-submit-user-input(k: Kernel, text: String) -> KernelState
  return %kernel-commit-event(k, :user-message, {text})

kernel-submit-assistant-reply(k: Kernel, text: String) -> KernelState
  return %kernel-commit-event(k, :assistant-reply, {text})

kernel-create-world(k: Kernel) -> Integer
  parent = k.current_world
  new_world = k.wal.world_counter++
  %kernel-commit-event(k, :branch, {parent_world: parent})
  k.current_world = new_world
  return new_world

kernel-current-state(k: Kernel) -> KernelState
  health = kernel-health(k)
  ctx = kernel-build-context-view(k)
  return {world_id: k.current_world, health, context: ctx}

kernel-health(k: Kernel) -> Symbol
  if k.graph == nil return :ok
  return check-immune-status(k.graph)

%kernel-commit-event(k: Kernel, kind: Symbol, payload: Map) -> KernelState
  stage-event(k.wal, kind, payload)
  commit-staged(k.wal)
  refresh-projections(k)
  return kernel-current-state(k)

refresh-projections(k: Kernel)
  k.graph = rebuild-graph-from-wal(k.wal)

%history->dto(g: Graph) -> [HistoryEntry]
  nodes = graph-history(g)
  return map(n -> {kind: n.kind, text: n.payload.text | "", clock: n.clock})

kernel-build-context-view(k: Kernel) -> ContextObject
  hist = %history->dto(k.graph)
  return {system_prompt: nil, history: hist, memory_context: nil, metadata: nil}

INVARIANTS:
INV: Runtime -> Kernel API only
INV: Kernel -> Sole State Mutator
INV: Graph = f(WAL)
INV: Post-Commit: WAL.persisted AND Graph.updated

COMPLEXITY:
Commit: O(1)
Projection: O(n)
History: O(depth)