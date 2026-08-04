IMPORT ir::01-domain-model AS Schema

TYPES
  Event | Canonical | Candidate | Config | ValidationReport | Projection | Graph | Summary | Derived | Analysis | MemoryRef | Prompt | RuntimeCommand | KernelState | KernelAction | causal-id

PIPELINE_FLOW
  Input -> Candidate -> Validation -> ValidationReport -> PolicyRouter -> KernelAction -> KernelTransition -> Commit -> Replay -> [Projection, Graph, Summary] -> PromptBuilder -> Backend -> Candidate

OPERATIONS

OP Commit(evt: Event, c: Canonical) -> Canonical'
  PRE: Candidate.validated == true & PolicyRouter(ValidationReport) == accept
  POST: Canonical'.history = Canonical.history + [evt] & Canonical'.clock++ & MemoryRef updated
  INV: Atomic | !Partial | Sole Canonical Mutator

OP Replay(c: Canonical) -> {Projection, Graph, Summary}
  POST: derive(c)
  PROP: Pure | Deterministic | SideEffectFree

OP Derive(c: Canonical) -> Derived
  PROP: Pure | Deterministic

OP PromptBuilder(summary: Summary, graph: Graph, m: MemoryRef, cfg: Config) -> Prompt
  PRE: Inputs subset {Canonical, Memory, Config}
  PROP: Pure | Deterministic

OP Backend(p: Prompt) -> Candidate
  PROP: NonDeterministic
  INV: Authoritative(Backend.output) == false

OP Validation(cand: Candidate, c: Canonical, cfg: Config) -> ValidationReport
  PROP: Pure | Deterministic | NoRouting | NoMutation

OP PolicyRouter(rpt: ValidationReport) -> KernelAction
  PROP: Pure | Deterministic | NoMutation
  RULE: Priority: Syntax > Semantics > FatalInv > RecovInv > Obs > Accept

OP KernelTransition(ks: KernelState, act: KernelAction) -> {KernelState', cmd: RuntimeCommand?}
  AGENT: Kernel ONLY
  POST: Mutate(KernelState)
  INV: Deterministic | Sole Runtime State Mutator

OP Recover(c: Canonical, m: MemoryRef) -> Context
  PROP: Pure
  INV: Canonical immutable

OP Branch(c: Canonical, cond: Condition) -> causal-id'
  INV: Canonical immutable | Authoritative post-Commit | Standard Candidate->Validation->Commit path

CANDIDATE_LIFECYCLE
  Generated -> Validated -> PolicyRouter -> KernelAction -> KernelTransition -> Commit

INV_GLOBAL
  Deterministic({Replay, Derive, PromptBuilder, Validation, PolicyRouter, KernelTransition})
  NonDeterministic(Backend)
  CanonicalMutator == Commit
  Derived == NonAuthoritative
  CanonicalWriteAccess: Mutate(Canonical) => Stage == Commit
