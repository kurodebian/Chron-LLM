Type Event = { kind: Kind, index: U64, clock: U64, causal-id: UUID, timestamp: U64, stream_id: UUID, payload: Any }
Type Kind = :gen-token | :structural-fault | :tool-fault | :tool-call-start | :tool-call-timeout | :tool-call-abort | :tool-call-commit
Type Edge = { src: Event, dst: Event, type: :temporal | :causal }
Type SystemState = { wal: [Event], active-causal-id: UUID, clock: U64, kv-cache: Bytes, stream_fault: Bool, active_stream_id: UUID }

Op init() -> SystemState = { wal: [], active-causal-id: UUID(), clock: 0, kv-cache: NULL, stream_fault: False, active_stream_id: NULL }

Op emit(e: Event) -> SystemState:
    e.clock = state.clock + 1
    state.wal.append(e)
    state.clock = e.clock

Op handle_fault() -> SystemState:
    new_id = UUID()
    emit({ kind: :structural-fault, causal-id: new_id })
    state.kv-cache = NULL
    state.active-causal-id = new_id
    state.stream_fault = True

Op prefill() -> SystemState:
    path = traverse_causal(state.wal, state.active-causal-id)
    state.kv-cache = load(path)

Op commit_stream(tokens: [Token]) -> SystemState:
    PRE: !state.stream_fault
    for t in tokens: emit({ kind: :gen-token, stream_id: state.active_stream_id, payload: t })

Op tool_event(kind: Kind) -> SystemState:
    emit({ kind: kind })

INV1: forall e1, e2 in wal: e1.index < e2.index -> e1.clock <= e2.clock
INV2: state.stream_fault -> !exists e in wal: e.kind == :gen-token && e.stream_id == state.active_stream_id
INV3: state.kv-cache != NULL -> is_healthy(state.kv-cache)