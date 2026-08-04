TYPES: History, ProjectionModel, SemanticModel, Graph, Observation, ExternalRep, NormalizedRep, CandidateEvent, RuntimeDecision, CanonicalEvent, InletVersion

OPS:
normalize_input(raw: ExternalRep) -> NormalizedRep
normalize_output(raw: Output) -> NormalizedRep
boundary_inlet(v: InletVersion, n: NormalizedRep) -> CandidateEvent
map_decision(o: Observation) -> RuntimeDecision
commit(c: CandidateEvent) -> CanonicalEvent

STATE:
active_inlet: InletVersion
phase_f_state: Immutable

PRE:
normalize_input: side_effects == 0
boundary_inlet: input_type == NormalizedRep

INV:
INV-1: count(active_inlet) == 1
INV-2: normalize_input(x) == normalize_input(x)
INV-3: normalize_output(x) == normalize_output(x)
INV-4: boundary_inlet(v, x) == boundary_inlet(v, x)
INV-5: map_decision(x) == map_decision(x)
INV-6: delta(authoritative_state) == 0
INV-7: active_inlet != null
INV-8: interpretation_scope == boundary_inlet
INV-9: modify(boundary_inlet) -> new_phase_f_version

FLOWS:
F0: History -> ProjectionModel -> SemanticModel -> Graph -> Observation -> boundary_inlet -> CandidateEvent
C2: ExternalRep -> normalize_input -> boundary_inlet -> CandidateEvent -> commit -> CanonicalEvent
C3: Observation -> map_decision -> RuntimeDecision -> RuntimeProcessing

MAPS:
decision_map: {normal: commit-request, echo: retry-request, stagnation: retry-request, drift: retry-request, discontinuity: abort-request}