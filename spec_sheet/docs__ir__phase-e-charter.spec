StructuralGraph : {relations, identities, measurable_properties}
Observation : {structural_facts}
SemanticInterpretation : external

Observe : (G: StructuralGraph) -> O: Observation

INV-E1 : !semantic_selection(O)
INV-E2 : !semantic_normalization(O)
INV-E3 : O.subset(structural_properties(G))
INV-E4 : coexist(SemanticInterpretation[])
INV-E5 : invariant(Observe(G), SemanticInterpretation)
INV-E6 : G == G_post
INV-E7 : deterministic(Observe)
INV-E8 : !mutate(runtime_state)

Sigma-4 :
  F0 : O = Observe(G)
  C2 : delta(G) -> Observation

RuntimeSpecialization :
  Detector <: Observation
  INV : preserve(INV-E1..E8)
  Output : informational_only
  Decision : external

  EchoDetector :
    length_ratio = len(out) / len(in)
    similarity = StructuralSimilarity(out, in)
    Trigger : length_ratio in [0.95, 1.05] AND similarity >= threshold

  StagnationDetector :
    entropy = entropy(out)
    unique_ratio = unique(out) / total(out)
    Trigger : entropy < threshold OR unique_ratio < threshold

  DriftDetector :
    rate = context_consumption_rate
    Trigger : rate > threshold

  DiscontinuityDetector :
    dist = topology_distance(last, candidate)
    Trigger : dist > threshold