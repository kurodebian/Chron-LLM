# PHASE C — Event Interpretation Layer (Normative Charter)

## GOAL

Derive Semantic Units from the Projection Model using the Event ABI contract.

## INPUT

M : Projection Model

ABI : Event Interpretation Contract


## OUTPUT

S = interpret(M, ABI)

J = j(S)


## CORE CONCEPTS

- Event ABI defines the interpretation boundary.
- Interpretation derives normalized Semantic Units from Projection Model elements.
- Semantic Units contain structured semantic fields.


## INVARIANTS

CINV-1 Interpretation is deterministic under a fixed Event ABI.

CINV-2 Event ABI is explicit and versioned.

CINV-3 Semantic Units are derived exclusively from the Projection Model.

CINV-4 Interpretation preserves ordering defined by the Projection Model.

CINV-5 Justification is derived only from Semantic Units.

CINV-6 No external semantic injection beyond the Event ABI.


## SIGMA-4

F0:

A = H

M = d(H)

S = interpret(M, ABI)

J = j(S)


C2:

G(J, H)


## NON-GOALS

Projection  
Knowledge  
Analysis  
Full semantic reasoning  
World modeling  
Execution semantics  
Graph construction  
Runtime evaluation
