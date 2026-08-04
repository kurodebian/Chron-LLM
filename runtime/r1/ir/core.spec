IMPORT ir::01-domain-model AS Schema

MODULE chronos-r1

// --- Reference SSOT Types from Schema ---
TYPES
  Source = Schema::Source
  Intent = Schema::Intent
  Event = Schema::Event
  Candidate = Schema::Candidate
  Canonical = Schema::Canonical
  ValidationReport = Schema::ValidationReport
  RuntimeRequest = Schema::RuntimeRequest
  KernelAction = Schema::KernelAction
  RuntimeCommand = Schema::RuntimeCommand
  CmdKind = Schema::CmdKind
  ReqKind = Schema::ReqKind

// --- Runtime Specific State Definitions ---
TYPES
  Fault = {id, clock, origin, cause, detector, candidate-id}
  KernelState = {canonical: Schema::Ref<Canonical>, deferred: [Candidate], working: Candidate?, faults: [Fault]}
  Runtime = {ks: KernelState, next-cand-id: UUID, last-cmd: RuntimeCommand?}

INVARIANTS
  INV1: Canonical immutable; new instance only via commit().
  INV2: validate(), policy-route() side-effect free.
  INV3: kernel-transition() sole Runtime state mutator.
  INV4: commit() sole Canonical updater.
  INV5: wake-deferred() trigger == CommitSuccess (no time-based).
  INV6: build-prompt() inputs subset {Canonical, Memory, Config}; excludes Obs/Fault/Metrics.
  INV7: Backend non-authoritative; output -> Candidate -> Validation pipeline mandatory.
  INV8: Worldline Branch uses standard Candidate->Validation->Commit path.

OPS domain-api
  cand-to-event(cand: Candidate) -> Event // metadata += {candidate-id, intent}

OPS pure-ops
  derive(c: Canonical) -> {proj, graph, summary: [Event]} // |summary| <= limit; Pure
  replay(c: Canonical) -> {proj, graph, summary: [Event]} // derive(c)
  build-prompt(d: Derived, m: Memory, cfg: Config) -> Prompt // Det; Inputs subset {Canonical, Memory, Config}
  validate(cand: Candidate) -> ValidationReport // Pure. Checks Syntax/Sem/Inv/Obs(Echo/Stagnation/Disc). Recs:{Retry,Penalty,Abort}
  policy-route(rpt: ValidationReport) -> RuntimeRequest // Priority: Syntax > Sem > FatalInv > RecovInv > Obs(Abort>Penalty>Retry) > Accept
  recover(canonical: Canonical) -> {derived, memory, prefill} // Pure.

OPS kernel-boundary
  commit(evt: Event) -> {new-canonical, committed} // Updates Clock++, Lamport, History+, Memory+. Only Canonical writer.
  kernel-transition(req: RuntimeRequest, cand: Candidate?, state: KernelState) -> {next-state: KernelState, cmd: RuntimeCommand?}
    commit-request: commit(cand->event()) -> remove working; Proceed
    reject-request: remove working; Discard
    defer-request: add deferred; Sleep
    retry-request: Regenerate (no change)
    retry-penalty-request: policy(temp+0.2, top-p-0.1); RegenPenalty
    abort-request: create Fault; Terminate
  wake-deferred(state: KernelState) -> KernelState // Triggered by CommitSuccess only. Re-eval deferred via Validate->Policy->Kernel.
  branch-worldline() -> Candidate // Standard path (metadata={causal-id}).

OPS runtime-facade
  runtime-run-candidate(cand: Candidate) -> {Runtime, ValidationReport, RuntimeRequest, RuntimeCommand}
  runtime-submit(inp: Any) -> {Runtime, ValidationReport, RuntimeRequest, RuntimeCommand}
  runtime-run-backend() -> {Runtime, ValidationReport, RuntimeRequest, RuntimeCommand}

OPS inspection
  runtime-state(rt: Runtime) -> KernelState
  runtime-next-candidate-id(rt: Runtime) -> UUID
  runtime-last-command(rt: Runtime) -> RuntimeCommand?

OPS testing
  chronos-r1-self-test() -> Boolean // Validates commit, validation, kernel, runtime pipelines