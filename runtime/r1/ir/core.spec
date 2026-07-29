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

OPS
  derive(c: Canonical) -> {proj, graph, summary: [Event]} // |summary| <= limit; Pure
  replay(c) = derive(c)
  build-prompt(d: Derived, m: Memory, cfg: Config) -> Prompt // Det; Inputs subset {Canonical, Memory, Config}

  validate(cand: Candidate) -> Report // Pure. Checks Syntax/Sem/Inv/Obs(Echo/Stagnation/Disc). Recs:{Retry,Penalty,Abort}
  policy-route(rpt: Report) -> Action // Priority: Syntax > Sem > FatalInv > RecovInv > Obs(Abort>Penalty>Retry) > Accept

  commit(evt: Event) -> {new-canonical, committed} // Updates Clock++, Lamport, History+, Memory+. Only Canonical writer.
  cand-to-event(cand) = evt(metadata += {candidate-id, intent})

  kernel-transition(action: KernelAction, cand?, state: KernelState) -> {next-state, cmd}
    accept: commit(cand->event()) -> remove working; Proceed
    reject: remove working; Discard
    defer: add deferred; Sleep
    retry: Regenerate (no change)
    retry-penalty: policy(temp+0.2, top-p-0.1); RegenPenalty
    abort: create Fault; Terminate

  wake-deferred(state) // Triggered by CommitSuccess only. Re-eval deferred via Validate->Policy->Kernel.
  recover(canonical) -> {derived, memory, prefill} // Pure.
  branch-worldline() -> Candidate(metadata={causal-id}) // Standard path.

  runtime-run-candidate(cand) -> Validate -> Policy -> Kernel -> WakeDeferred; Returns {Runtime, Report, Action, Command}
  runtime-submit(inp) -> CreateCand -> run-candidate
  runtime-run-backend() -> Replay -> BuildPrompt -> Gen(P->T) -> Submit // Gen no Canonical access.

INVARIANTS
  INV1: Canonical immutable; new instance only via commit().
  INV2: validate(), policy-route() side-effect free.
  INV3: kernel-transition() sole Runtime state mutator.
  INV4: commit() sole Canonical updater.
  INV5: wake-deferred() trigger == CommitSuccess (no time-based).
  INV6: build-prompt() inputs subset {Canonical, Memory, Config}; excludes Obs/Fault/Metrics.
  INV7: Backend non-authoritative; output -> Candidate -> Validation pipeline mandatory.
  INV8: Worldline Branch uses standard Candidate->Validation->Commit path.