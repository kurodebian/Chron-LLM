IMPORT ir::01-domain-model AS Schema

MODULE chronos-r1

TYPES
  Source = {user, assistant, tool, system}
  Intent = {append, reflect, tool, memory-read, memory-write, recover, summarize}
  KernelAction = {accept, reject, defer, retry, retry-penalty, abort}
  Event = {id: UUID, source: Source, payload: Any, metadata: Map} // Read-only
  Candidate = {trigger: Any, constraints: List, metadata: Map} + Event // Non-Canonical
  Canonical = {history: [Event], config: Config, memory-ref: Ref, clock: Int} // Immutable
  ValidationReport = {syntax-errs: [], semantic-errs: [], inv-errs: [], obs: []}
  RuntimeCommand = {kind: CmdKind, data: Any}
  Fault = {id, clock, origin, cause, detector, candidate-id}
  KernelState = {canonical: Canonical, deferred: [Candidate], working: Candidate?, faults: [Fault]}
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
  policy-route(rpt: ValidationReport) -> KernelAction // Priority: Syntax > Sem > FatalInv > RecovInv > Obs(Abort>Penalty>Retry) > Accept
  recover(canonical: Canonical) -> {derived, memory, prefill} // Pure.

OPS kernel-boundary
  commit(evt: Event) -> {new-canonical, committed} // Updates Clock++, Lamport, History+, Memory+. Only Canonical writer.
  kernel-transition(action: KernelAction, cand: Candidate?, state: KernelState) -> {next-state: KernelState, cmd: RuntimeCommand?}
    accept: commit(cand->event()) -> remove working; Proceed
    reject: remove working; Discard
    defer: add deferred; Sleep
    retry: Regenerate (no change)
    retry-penalty: policy(temp+0.2, top-p-0.1); RegenPenalty
    abort: create Fault; Terminate
  wake-deferred(state: KernelState) -> KernelState // Triggered by CommitSuccess only. Re-eval deferred via Validate->Policy->Kernel.
  branch-worldline() -> Candidate // Standard path (metadata={causal-id}).

OPS runtime-facade
  runtime-run-candidate(cand: Candidate) -> {Runtime, ValidationReport, KernelAction, RuntimeCommand} // Validate -> Policy -> Kernel -> WakeDeferred
  runtime-submit(inp: Any) -> {Runtime, ValidationReport, KernelAction, RuntimeCommand} // CreateCand -> run-candidate
  runtime-run-backend() -> {Runtime, ValidationReport, KernelAction, RuntimeCommand} // Replay -> BuildPrompt -> Gen(P->T) -> Submit // Gen no Canonical access.

OPS inspection
  runtime-state(rt: Runtime) -> KernelState
  runtime-next-candidate-id(rt: Runtime) -> UUID
  runtime-last-command(rt: Runtime) -> RuntimeCommand?

OPS testing
  chronos-r1-self-test() -> Boolean // Validates commit, validation, kernel, runtime pipelines