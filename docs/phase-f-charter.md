# PHASE F — Semantic Freeze & Control Layer (Normative Charter)

## GOAL

Freeze a single semantic inlet as the exclusive entry point for runtime integration.

Normalize all runtime inputs and outputs into canonical representations.

Convert structural observations into deterministic runtime control actions.

---

## INPUT

A : History

C : Model (triples)

D : Graph

O : Observation

LLM Output

---

## OUTPUT

F = frozen_semantics(config)

S = semantic_inlet(F)

CanonicalEvent

RuntimeAction

---

## CORE CONCEPTS

- Exactly one semantic inlet is frozen as the official runtime entry point.
- Every runtime input is normalized before semantic interpretation.
- Every LLM output is normalized before entering the runtime.
- Observation results are mapped deterministically into runtime actions.
- Phase F is deterministic and side-effect-free.
- Phase F performs no state mutation.

---

## NORMALIZATION

### Input Normalization

The runtime SHALL normalize all incoming text before semantic processing.

Normalization includes:

- Unicode NFC
- whitespace collapse
- dialect normalization
  - Japanese punctuation
  - English punctuation
- control character removal

Formally

```
normalize_input(raw_input)
→ normalized_input
```

---

### Output Normalization

LLM output SHALL be normalized using the same normalization rules.

The normalized output SHALL then be converted into a CanonicalEvent.

```
normalize_output(raw_output)
        │
        ▼
normalized_output
        │
        ▼
CanonicalEvent
```

Normalization SHALL be deterministic.

---

## ROUTING

Observation labels SHALL be mapped to runtime actions using the following deterministic routing table.

| Observation | Runtime Action |
|-------------|----------------|
| normal | commit |
| echo | retry |
| stagnation | retry-with-penalty |
| drift | retry-with-penalty |
| discontinuity | abort |

Routing SHALL be deterministic.

Routing SHALL NOT mutate runtime state.

---

## INVARIANTS

FINV-1 Exactly one semantic inlet is active.

FINV-2 Input normalization is deterministic.

FINV-3 Output normalization is deterministic.

FINV-4 CanonicalEvent generation is deterministic.

FINV-5 Routing is deterministic.

FINV-6 Frozen semantics do not mutate A, C, or D.

FINV-7 Frozen inlet is explicit and versioned.

FINV-8 No semantic selection occurs outside Phase F.

FINV-9 Removal or replacement of the inlet requires a new Phase F version.

FINV-10 Phase F performs no state mutation.

---

## SIGMA-4

F0

```
inlet = A
```

C2

```
normalized_input
        │
        ▼
semantic_inlet
        │
        ▼
normalized_output
        │
        ▼
CanonicalEvent
```

C3

```
Observation
        │
        ▼
Routing
        │
        ▼
RuntimeAction
```

---

## NON-GOALS

Graph execution

Observation generation

History mutation

Kernel state transitions

LLM prompting strategy

Safety / policy decisions

Runtime scheduling