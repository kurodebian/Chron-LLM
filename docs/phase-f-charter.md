# PHASE F — Semantic Freeze Layer (Normative Charter)

## GOAL
Freeze a single semantic inlet as the exclusive entry point for runtime integration.

## INPUT
A: History  
C: Model (triples)  
D: Graph  

## OUTPUT
F = frozen_semantics(config)  
S = semantic_inlet(F)

## CORE CONCEPTS
- Exactly one semantic inlet is frozen as the official entry point
- LLM outputs are normalized only through this inlet
- All other semantic representations remain non-selected and non-binding
- Phase F is stateless and holds no semantic information itself

## INVARIANTS

FINV-1 Only one semantic inlet is active at a time  
FINV-2 LLM output normalization is total and deterministic at the inlet  
FINV-3 Frozen semantics do not mutate A, C, or D contracts  
FINV-4 Frozen inlet is explicit and versioned  
FINV-5 No semantic selection occurs outside Phase F  
FINV-6 Removal or change of inlet requires new F version  
FINV-7 Inlet binding is canonical and immutable for the lifetime of F instance  

## SIGMA-4

F0:
inlet = A

C2:
bind(LLM_output → inlet)

## NON-GOALS
Graph execution  
Observation usage in selection  
History mutation policy  
LLM prompting strategy  
Safety / policy decisions
