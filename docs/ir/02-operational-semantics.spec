Event | Canonical | Candidate | Config | ValidationReport | Projection | Graph | Summary | Derived | Analysis | MemoryRef | causal-id | KernelState
RuntimeRequest = commit-request | reject-request | defer-request | retry-request | retry-penalty-request | abort-request

Commit(Event, Canonical) -> Canonical'
  PRE: Candidate.validated & PolicyRouter(Candidate)==commit-request
  POST: Canonical'.History=Canonical.History+[Event] & Canonical'.Clock++ & MemoryRef updated
  INV: Atomic; !Partial

Replay(Canonical) -> {Projection, Graph, Summary}
  PROP: Pure | Deterministic | SideEffectFree

Derive(Canonical) -> Derived
  PROP: Pure | Deterministic

Validation(Candidate, Canonical, Config) -> ValidationReport
  PROP: Pure | Deterministic | NoRouting | NoMutation

Lifecycle(Candidate): Generated->Validated->PolicyRouter->RuntimeRequest
  commit-request -> Commit

Recover(Canonical, MemoryRef) -> Context
  INV: Canonical immutable

Branch(Canonical, Condition) -> causal-id'
  INV: Canonical immutable; Authoritative post-Commit

Transition(KernelState x RuntimeRequest) -> KernelState'
  AGENT: Kernel ONLY

INV_Global:
  Deterministic({Replay, Derive, Validation, PolicyRouter, Transition})
  NonDeterministic(Backend)
  CanonicalMutator == Commit
  Derived == NonAuthoritative