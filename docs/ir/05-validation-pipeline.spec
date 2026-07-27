TYPES:
Candidate : {id}
Canonical : State
Config : {retry-limit, penalty-strategy, thresholds[], policy}
Violation : {type, severity:{recoverable|unrecoverable}}
Observation : {detector, score, threshold, facts[]}
ValidationReport : {cid: Candidate.id, syntax-violations: [Violation], semantic-violations: [Violation], invariant-violations: [Violation], observations: [Observation]}
RuntimeRequestKind : commit | reject | defer | retry | retry-penalty | abort
RuntimeRequest : {kind: RuntimeRequestKind}

OPS:
Validation(Candidate c, Canonical canon) -> ValidationReport r
  Layers: SyntaxCheck(c) -> SemanticConsistencyCheck(c,canon) -> InvariantCheck(c,canon) -> ObservationCheck(c)
  Output: r = aggregate(Layers.facts)

PolicyRouter(ValidationReport r, Config cfg) -> RuntimeRequest req
  Logic:
    IF len(r.syntax-violations) > 0 -> req.kind = reject
    ELSE IF len(r.semantic-violations) > 0 -> req.kind = reject
    ELSE IF exists(v in r.invariant-violations | v.severity == unrecoverable) -> req.kind = reject
    ELSE IF exists(v in r.invariant-violations | v.severity == recoverable) -> req.kind = defer
    ELSE IF exists(o in r.observations | o.score > o.threshold) -> req.kind = cfg.policy.resolve(o)
    ELSE -> req.kind = commit

INV:
  Determinism(Validation): Input(c,canon) -> Output(r) is pure; no timing/randomness/ext-state.
  FactOnly(ValidationReport): r contains NO routing-decision.
  FactOnly(Observation): o contains NO routing-logic/runtime-decision/rejection.
  ConfigBoundary: cfg modifies PolicyRouter ONLY; NOT Validation semantics/observation-measurement.
  KernelExclusivity: RuntimeRequest consumed BY Kernel ONLY.