# PHASE B — Projection Layer (Normative Charter)

## GOAL
Derive Model and Justification Structure from History.

## INPUT
H : History

## OUTPUT
M = d(H)  
J = j(M)

## INVARIANTS

BINV-1 Projection is deterministic  
BINV-2 J is derived only from H  
BINV-3 Projection introduces no semantic interpretation  
BINV-4 Projection remains reproducible  

## SIGMA-4

F0:
A = H  
M = d(H)  
J = j(M)

C2:
G(J, H)

## NON-GOALS
Event ABI  
Resolution  
Semantic Unit  
Interpretation  
LLM Runtime  
