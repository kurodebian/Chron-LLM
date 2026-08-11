# Architecture Specification v2.0 (Unified Core SOT)

## 1. TYPES & STRUCTS

Type CausalID = HashString
Type EventID  = HashString
Type WorldID  = HashString
Type StreamID = HashString

Type Kind = :gen-token | :structural-fault | :tool-fault | :tool-call-start | :tool-call-timeout | :tool-call-abort | :tool-call-commit | :branch

Type CandidateEvent = {
    event_id: EventID,
    parent_id: CausalID,
    world_id: WorldID,
    stream_id: StreamID,
    kind: Kind,
    payload: Any
}

Type CanonicalEvent = {
    causal_id: CausalID,
    event: CandidateEvent,
    causal_hash: HashString
}

Type Edge = { src: CausalID, dst: CausalID, type: :temporal | :causal }

Type StagingBuffer = {
    staged_events: [CandidateEvent]
}

Type SystemState = {
    wal: [CanonicalEvent],
    world_heads: Map<WorldID, CausalID>,
    active_causal_id: CausalID,
    kv_cache: Pointer,
    stream_fault: Bool,
    active_stream_id: StreamID,
    staging: StagingBuffer
}


## 2. INVARIANTS

INV1 (APPEND_ONLY_WAL): forall e1, e2 in wal: e1.causal_id != e2.causal_id
INV2 (STAGING_ISOLATION): state.stream_fault -> !exists e in state.staging.staged_events: e.kind == :gen-token && e.stream_id == state.active_stream_id
INV3 (KV_CACHE_HEALTH): state.kv_cache != NULL -> is_healthy(state.kv_cache)
INV4 (DETERMINISTIC_CAUSAL_HASH): forall e in wal: e.causal_hash == Hash(e.event.parent_id || e.event.world_id || e.event.kind || e.event.payload)


## 3. OPERATIONS

Op init() -> SystemState = {
    wal: [],
    world_heads: {},
    active_causal_id: HashString("GENESIS"),
    kv_cache: NULL,
    stream_fault: False,
    active_stream_id: NULL,
    staging: { staged_events: [] }
}

Op StageEvent(state: SystemState, e: CandidateEvent) -> SystemState:
    state.staging.staged_events.append(e)
    RETURN state

Op DiscardStaging(state: SystemState) -> SystemState:
    state.staging.staged_events = []
    RETURN state

Op handle_fault(state: SystemState) -> SystemState:
    new_id = Hash(state.active_causal_id || "FAULT")
    e = { event_id: Hash(new_id), parent_id: state.active_causal_id, world_id: state.world_heads[state.active_stream_id], stream_id: state.active_stream_id, kind: :structural-fault, payload: NULL }
    state.staging.staged_events.append(e)
    state.kv_cache = NULL
    state.active_causal_id = new_id
    state.stream_fault = True
    RETURN state

Op prefill(state: SystemState) -> SystemState:
    path = traverse_causal(state.wal, state.active_causal_id)
    state.kv_cache = load(path)
    RETURN state

Op commit_stream(state: SystemState, tokens: [Any]) -> SystemState:
    PRE: !state.stream_fault
    for t in tokens:
        e = { event_id: Hash(t), parent_id: state.active_causal_id, world_id: state.world_heads[state.active_stream_id], stream_id: state.active_stream_id, kind: :gen-token, payload: t }
        state = StageEvent(state, e)
    RETURN state


## 4. MODULE: GraphOptimization (Absorbed from chron-llm-graph)

Func LiftToGraph(wal: [CanonicalEvent]) -> TransientCausalGraph:
    // WALからメモリ上に因果グラフを動的再構築する (Stateless Graph)

Func FindParentNode(healthy_table: HealthyTable, target_id: CausalID) -> Option<CausalID>:
    // 高速トラバーサル用インデックス参照
