STATE: H : History, M : ProjectionModel, J : JustificationStructure, A : History
OP: d(H) -> M, j(M) -> J
AXIOM: A = H
AXIOM: M = d(H)
AXIOM: J = j(M)
AXIOM: G(J, H)
INV: d.deterministic
INV: j.derived_exclusively_from(d)
INV: d.semantically_neutral
INV: d.reproducible
EXCLUDE: EventABI, Resolution, SemanticUnit, Interpretation, Knowledge, LLMRuntime