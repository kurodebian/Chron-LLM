STATE: H : History, M : ProjectionModel, ABI : EventABI, S : SemanticModel, J : JustificationStructure, A : History
OP: interpret(M, ABI) -> S, justify(S) -> J
AXIOM: A = H
AXIOM: M = projection(H)
AXIOM: S = interpret(M, ABI)
AXIOM: J = justify(S)
INV: interpret.deterministic_under(ABI)
INV: ABI.explicit_and_versioned
INV: S.derived_exclusively_from(M)
INV: interpret.preserves_order(M)
INV: J.derived_exclusively_from(S)
INV: external_semantic_injection !in interpret
INV: S.non_authoritative
EXCLUDE: ProjectionGeneration, KnowledgeGeneration, Analysis, FullSemanticReasoning, WorldModeling, ExecutionSemantics, GraphConstruction, RuntimeEvaluation, CanonicalStateMutation