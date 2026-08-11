TYPE PhysicalEvent = { causal-id: ID, token-id: Int, kv-pos: Int, entropy: Float, ts: Time }
TYPE IRStream = [PhysicalEvent]
TYPE EventNode = { causal-id: ID, tokens: [Int], kv-range: [Int], parent: EventNode | Null }
TYPE CausalGraph = { nodes: [EventNode], timelines: [EventNode], worldlines: [Timeline] }
TYPE RouterConfig = { gen-roles: [Role], critic: Role, max-gens: Int, max-latency: Int, risk-thresh: Float }
TYPE RuntimeCommand = { op: Commit | Retry | Rollback, interventions: [Intervention], truncate-at: Int | Null, delta-prefill: Str | Null, payload: Any, metadata: Opaque }
TYPE Intervention = GrammarMask | TempDown | SemBias
TYPE OmegaScore = { E: Float, S: Float, T: Float, total: Float }
TYPE KernelState = { ir-stream: IRStream, graph: CausalGraph, kv-pos: Int, omega: OmegaScore }
TYPE BackendState = { kv-cache: [Float], cursor: Int }

OP normalize(pe: PhysicalEvent) -> IRStream
OP observe(stream: IRStream) -> OmegaScore
OP evaluate(score: OmegaScore) -> Decision
OP decide(dec: Decision, cfg: RouterConfig) -> RuntimeCommand
OP execute(cmd: RuntimeCommand) -> BackendState

PRE normalize: pe != Null
POST normalize: IRStream.append(pe)
PRE execute: cmd.op in {Commit, Retry, Rollback}
POST execute: BackendState.update(cmd)

INV IRStream == SourceOfTruth(KernelState)
INV RuntimeCommand == ControlBoundary(Kernel, Backend)
INV Metadata == Opaque
INV Omega.total == w_e*E^2 + w_s*S^2 + w_t*T^2
INV BackendControl == { KV_Truncate, Delta_Prefill, Steering }
INV ABI == Frozen(RuntimeCommand, IRStream, PhaseBoundary)

LOOP: Generate -> Observe -> Evaluate -> Decide -> Intervene -> Generate