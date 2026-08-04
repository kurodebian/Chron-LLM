# PHASE C — Semantic Derivation Layer (Normative Charter)

## GOAL

Derive structured Semantic Model from the Projection Model through the versioned Event ABI contract.

Phase C performs deterministic semantic derivation only.

It does not perform semantic commitment or authoritative state mutation.

## INPUT

```
M : Projection Model

ABI : Event Interpretation Contract
```

## OUTPUT

```
S = interpret(M, ABI)

J = justify(S)
```

where:
- S : Semantic Model
- J : Justification Structure

## CORE CONCEPTS

- Event ABI defines the interpretation boundary.
- Interpretation derives a normalized Semantic Model from Projection Model elements.
- Semantic Model contains structured fields derived from the Event ABI.
- Semantic Model represents derived structural-semantic records.
- Semantic Model is a non-authoritative representation.
- Justification is derived from Semantic Model only.

## INVARIANTS

```
**CINV-1**  
Interpretation is deterministic under a fixed Event ABI.

**CINV-2**  
Event ABI is explicit and versioned.

**CINV-3**  
Semantic Model is derived exclusively from the Projection Model.

**CINV-4**  
Interpretation preserves ordering defined by the Projection Model.

**CINV-5**  
Justification is derived only from the Semantic Model.

**CINV-6**  
No external semantic injection occurs beyond the Event ABI.

**CINV-7**  
Semantic Model is a derived and non-authoritative representation.
```

## SIGMA-4

## F0

```
A = H

M = projection(H)

S = interpret(M, ABI)

J = justify(S)
```

## C2

```
Projection Model
    │
    ▼
Semantic Model
    │
    ▼
Justification
```

## NON-GOALS

- Projection generation
- Knowledge generation
- Analysis
- Full semantic reasoning
- World modeling
- Execution semantics
- Graph construction
- Runtime evaluation
- Canonical state mutation
