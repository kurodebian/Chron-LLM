STATE: H : History, M : ProjectionModel, S : SemanticModel, G : RelationalGraph
OP: graph(S) -> G
AXIOM: G = graph(S)
AXIOM: H -> M -> S -> G
AXIOM: T(G)
INV: graph.deterministic_from(S)
INV: nodes.preserve_identity_consistency
INV: edges.structural_relations_only
INV: traversal.deterministic
INV: interpretation !in G
INV: G.non_authoritative
EXCLUDE: SemanticInterpretation, EventABIProcessing, ObservationSemantics, MeaningAttribution, ExternalWorldBinding, KnowledgeGeneration, RuntimeExecution