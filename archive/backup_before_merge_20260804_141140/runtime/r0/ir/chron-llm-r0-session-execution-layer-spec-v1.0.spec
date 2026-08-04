ARCH: Chron-LLM-R1-v1.0
LAYERS = [User, R0_SessionExec, R1_IRObs, CausalKernel, Backend]
PRINCIPLE = LLM_as_GenerationEngine; Process_as_ObservableStateTransition

TYPE Session = { model: ModelRef, history: History }
TYPE HistoryEvent = { role: Role, content: Text }
TYPE History = [HistoryEvent]
INV(History) = ordered ^ append_only ^ snapshot_capable

TYPE R0Trace = { user_text: Text, prompt: Text, raw: RawData, parsed: ParsedData, history_before: History, history_after: History, prompt_len: Int, response_len: Int }
PROP(R0Trace) = reconstructive_state; !deterministic_replay

TYPE PhysicalEvent = { causal_id: ID, token_id: TokenID, kv_pos: Pos, entropy: Float, timestamp: Time }
SOURCE(PhysicalEvent) = Backend

TYPE IR = { ctx_id: ID, pos: Pos, phase: Phase, token: Token, score: Score }
INV(IR) = immutable ^ ordered ^ semantic_free ^ non_authoritative
PIPELINE(R1) = PhysicalEvent -> Normalize -> IR_Stream -> [Replay | Analysis]

TYPE RuntimeCommand = { op: OpType, interventions: [Intervention], truncate_at: Pos?, delta_prefill: Prefill?, payload: Any, metadata: Meta }
ENUM OpType = [:commit, :retry, :rollback]
INTERFACE(Kernel->Backend) = RuntimeCommand ONLY

OPS(R0) = { start-chat -> Session; chat(input) -> R0Trace }
SCOPE(R0) = +[SessionMgmt, HistoryMgmt, PromptGen, BackendCall, TraceGen]; -[TokenObs, CausalJudgment, Rollback, KV_Ops]

OPS(Kernel) = { decide(trace: R0Trace, stream: IR_Stream) -> RuntimeCommand }
SCOPE(Kernel) = [CausalGraph, Worldline, Rollback, PolicyDecision]

ANALYSIS(R1) = { extract-actions(phase=gen); divergence-profile(step, all_same, p_same) }

FROZEN = { R0: [SessionStruct, HistoryEvent, TraceContract]; R1: [PhysicalEventFlow, IRFormat, ObsBoundary]; Kernel: [RuntimeCommandABI, PhaseBoundary] }
FLEXIBLE = { PromptTemplate, BackendImpl, SensorAlgo, OmegaCalc, Visualization }