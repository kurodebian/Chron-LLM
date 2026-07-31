Type Event = { kind: Kind, index: U64, clock: U64, causal-id: UUID, timestamp: U64, payload: Any }
Type Kind = :dialogue | :tool | :meta | :structural-fault | :tool-fault
Type FaultRef = :echo | :stagnation | :drift | :discontinuity
Type Action = :commit | :discard | :retry | :retry-with-penalty | :abort
Type NodeClass = :dialogue | :tool | :meta | :fault
Type EdgeType = :temporal | :causal

State System = { wal: []Event, graph: Graph, global_clock: U64, llm_state: LLM_State }
State Graph = { nodes: Map<UUID, Node>, edges: Map<UUID, []Edge> }
State Node = { id: UUID, class: NodeClass, event: Event }
State Edge = { src: UUID, dst: UUID, type: EdgeType }
State LLM_State = { kv_cache: Bytes, retry_count: U32 }

Op Append_WAL(sys: System, e: Event) -> System
  Pre: e.clock > sys.global_clock
  Post: sys.wal.append(e); sys.global_clock = e.clock

Op Classify(kind: Kind) -> NodeClass
  :dialogue -> :dialogue
  :tool | :tool-fault -> :tool
  :meta -> :meta
  :structural-fault -> :fault

Op Lift_Graph(wal: []Event) -> Graph
  g = Graph{}
  last_node = NULL
  last_healthy = NULL
  For e in wal:
    n = Node{id: e.causal-id, class: Classify(e.kind), event: e}
    g.nodes[e.causal-id] = n
    If last_node != NULL: g.edges.append({src: last_node.id, dst: n.id, type: :temporal})
    If n.class != :fault:
      last_healthy = n
      If last_healthy_prev != NULL: g.edges.append({src: last_healthy_prev.id, dst: n.id, type: :causal})
    last_node = n
  Return g

Op Control_Decide(obs: Obs, state: State) -> Action
  If obs.ref in FaultRef: Return :abort
  If obs.ref == :tool-fault: Return :retry
  If obs.valid: Return :commit
  If state.retry_count < MAX: Return :retry | :retry-with-penalty
  Return :abort

Op Handle_Abort(sys: System) -> System
  sys.llm_state.kv_cache = NULL
  clean_history = Trace_Causal(sys.graph)
  sys.llm_state = Inject(clean_history)
  fault_event = {kind: :structural-fault, clock: sys.global_clock + 1, ...}
  Return Append_WAL(sys, fault_event)

Op Trace_Causal(graph: Graph) -> []Event
  Path = Backtrack(Root, :causal)
  Return Filter(Path, n.class != :fault)

INV Global_Clock_Monotonicity: Forall e1, e2 in WAL: e1.index < e2.index -> e1.clock < e2.clock
INV No_Partial_Commit: If Action in [:discard, :abort]: Tokens not in WAL
INV Retry_Idempotency: WAL contains only Final_Success OR Final_Fault
INV Fault_Isolation: Node.class == :fault -> No outgoing :causal edges
INV Tool_Fault_Independence: Event.kind == :tool-fault -> LLM_State.retry_count unchanged