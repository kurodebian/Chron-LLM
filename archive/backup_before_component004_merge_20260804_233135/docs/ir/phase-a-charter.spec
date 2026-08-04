STATE: H : History
AXIOM: A = H
INV: H.authoritative_causal_record
INV: H.reproducible
INV: H.inspectable
INV: H.derivable
INV: EventABI !in H
INV: ResolutionSemantics !in H
EXCLUDE: EventABI, Resolution, SemanticUnit, Interpretation, LLMRuntime