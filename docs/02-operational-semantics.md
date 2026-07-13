# Operational Semantics

**Status:** Normative  
**Version:** R1  
**Scope:** Formal operational semantics of the Chron-LLM runtime.

---

# 1. Purpose

This specification defines the operational semantics of the deterministic Chron-LLM runtime.

It specifies the observable behavior of the core runtime operations while remaining independent of implementation details.

This document defines **what** each operation means, not **how** it is implemented.

---

# 2. Commit

## Purpose

Commit is the sole operation permitted to mutate Canonical.

## Input

```
Event
Canonical
```

## Output

```
Canonical'
```

## Observable Effects

- Event is appended to History.
- Lamport Clock advances.
- MemoryRef is updated when required.
- Canonical becomes the new authoritative state.

## Preconditions

- Event has passed Validation.
- Kernel has selected `accept`.

## Postconditions

- Canonical reflects the committed Event.
- Previous Canonical state remains replayable.

## Failure Semantics

Commit SHALL either:

- complete atomically, or
- leave Canonical unchanged.

Partial commits are prohibited.

---

# 3. Replay

## Purpose

Replay reconstructs deterministic runtime context from Canonical.

## Input

```
Canonical
```

## Output

```
Projection
Graph
Summary
```

## Observable Behavior

Replay SHALL be

- deterministic
- reproducible
- side-effect-free

Replay SHALL NOT mutate Canonical.

---

# 4. Derive

## Purpose

Derive computes non-authoritative runtime representations from Canonical.

## Input

```
Canonical
```

## Output

```
Derived
```

Derived MAY include

- Projection
- Graph
- Summary

## Observable Behavior

Derive SHALL

- preserve determinism
- produce identical outputs for identical Canonical
- perform no state mutation

---

# 5. Validation

## Purpose

Validation collects objective facts regarding a Candidate.

## Input

```
Candidate
Canonical
Config
```

## Output

```
ValidationReport
```

## Observable Behavior

Validation SHALL

- be deterministic
- be side-effect-free
- perform no routing
- perform no state mutation

Interpretation of ValidationReport is delegated to PolicyRouter.

---

# 6. Candidate Lifecycle

A Candidate progresses through the following lifecycle.

```
Generated
        │
        ▼
Validated
        │
        ▼
PolicyRouter
        │
        ▼
Action
        │
        ├────────────► accept
        │                  │
        │                  ▼
        │              Commit
        │
        ├────────────► reject
        │
        ├────────────► defer
        │                  │
        │                  ▼
        │          DeferredQueue
        │
        ├────────────► retry
        │
        ├────────────► retry-penalty
        │
        └────────────► abort
```

Only the `accept` path may produce authoritative state mutation.

---

# 7. Recovery

## Purpose

Recover reconstructs execution after abnormal termination or worldline branching.

## Input

```
Canonical
MemoryRef
```

## Output

```
Recovered Context
```

## Observable Behavior

Recovery MAY

- destroy runtime caches
- reconstruct Prefill
- resume execution

Recovery SHALL NOT modify Canonical directly.

Canonical mutation remains exclusively the responsibility of Commit.

---

# 8. Worldline Branching

## Purpose

Branch execution into a new causal worldline.

## Input

```
Canonical
Branch Condition
```

## Output

```
New causal-id
```

## Observable Behavior

Branching MAY

- destroy KV cache
- reconstruct Prefill
- traverse causal Graph

The new causal-id becomes authoritative only after Commit.

---

# 9. State Transitions

The deterministic runtime transition function is

```
KernelState × Action
        │
        ▼
KernelState'
```

Only the Kernel performs state transitions.

Validation and PolicyRouter are pure functions.

---

# 10. Determinism

The following operations SHALL be deterministic:

- Replay
- Derive
- Validation
- PolicyRouter
- Kernel State Transition

The Backend (LLM generation) is explicitly non-deterministic.

---

# 11. Constitutional Constraints

This specification conforms to the Constitution.

In particular:

- Only Commit may mutate Canonical.
- Derived is non-authoritative.
- Replay is deterministic.
- Validation collects facts only.
- PolicyRouter performs interpretation only.
- Kernel performs state transitions only.