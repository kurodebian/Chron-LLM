PKG chronos-r1 : USE(cl)

TYPE event = { id, source, payload, metadata } INV immutable
TYPE candidate = { id, source, trigger, intent, payload, constraints, metadata }
TYPE canonical = { history: [event], config, memory-ref, clock } INV single-authority
TYPE kernel-state = { canonical, deferred-queue: [candidate], working, faults }
TYPE validation-report = { candidate-id, syntax-violations, semantic-violations, invariant-violations, observations }
TYPE runtime-command = { kind, data }

OPS domain-api : make-event(event), event-p(x)->bool | make-candidate(candidate), candidate-p(x)->bool | make-canonical(canonical), canonical-p(x)->bool | make-kernel-state(kernel-state) | validation-report-p(x)->bool | runtime-command-p(x)->bool

OPS pure-ops : derive(canonical) -> info | replay(history: [event]) -> state | build-prompt(...) -> prompt | validate(candidate, canonical) -> validation-report | policy-router(validation-report) -> action | recover(state) -> config INV no-side-effects

OPS kernel-boundary : commit(canonical, event) -> canonical' | kernel-transition(kernel-state, action) -> kernel-state' | wake-deferred(kernel-state) -> kernel-state' | branch-worldline(canonical) -> new-canonical INV authoritative-update

TYPE runtime = { state, next-candidate-id, last-command }
OPS runtime-facade : make-runtime() -> runtime | runtime-submit(runtime, input) -> runtime' | runtime-run-candidate(runtime, candidate) -> runtime' | runtime-run-backend(runtime) -> runtime'

OPS inspection : runtime-state(runtime) -> state | runtime-next-candidate-id(runtime) -> id | runtime-last-command(runtime) -> command

OPS testing : chronos-r1-self-test() -> result INV validates-commit-validation-kernel-runtime