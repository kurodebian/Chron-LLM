# PHASE C — Event Interpretation Layer (Normative Charter)

## GOAL
Derive structured semantic representation from History events via ABI.

## INPUT
H : History

## OUTPUT
M = projection(H)  
J = justification(M)

## CORE CONCEPTS
- Event ABI introduces controlled interpretation boundary
- Events are normalized into structured triples:
  (role, type, payload)

## INVARIANTS

CINV-1 Event ABI is versioned and explicit  
CINV-2 Projection is deterministic over History  
CINV-3 No mutation of History during projection  
CINV-4 Model preserves event order  
CINV-5 Justification is derived only from Model  
CINV-6 No external semantic injection beyond ABI mapping  

## SIGMA-4

F0:
A = H  
M = d(H, ABI)  
J = j(M)

C2:
G(J, H)

## NON-GOALS
Full semantic reasoning  
World modeling  
Execution semantics  
Graph construction  
Runtime evaluation