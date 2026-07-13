# Chron-LLM Kernel State Machine Specification

**Status:** Normative  
**Version:** R1  
**Scope:** Deterministic authoritative state transitions executed by the Kernel.

---

# 1. Purpose

This specification defines the deterministic state transitions executed by the Chron-LLM Kernel.

The Validation Pipeline collects facts.

The PolicyRouter determines an Action.

The Kernel is the **sole component authorized to execute that Action and mutate the authoritative system state**.

This document separates execution semantics from decision semantics, ensuring that the Kernel remains the deterministic execution core of the architecture.

---

# 2. Design Principles

## Single Mutator

Only the Kernel may mutate:

- Canonical
- DeferredQueue
- FaultEvent log

---

## Deterministic State Transition

The Kernel performs:

- no validation
- no interpretation
- no external I/O
- no LLM invocation

Given identical inputs, the Kernel MUST produce identical outputs.

---

## Runtime Separation

The Kernel does not execute external operations.

Instead, it emits a non-authoritative `RuntimeCommand` for execution by the Runtime.

Execution of a RuntimeCommand is outside the scope of this specification.

---

## Clock-Driven Execution

State evolution depends only on Canonical advancement.

No wall-clock time participates in state transitions.

---

# 3. Kernel State

The Kernel operates on the composite KernelState.

```
KernelState :=

    Canonical
    DeferredQueue
    Working
```

where

```
Canonical :=

    History
    Config
    MemoryRef
```

```
Working :=

    Candidate
    Prompt
    Backend
    IR
    Metrics
    Lookup
```

---

# 4. Kernel Function

The Kernel is defined as the deterministic transition function

```
Kernel(
    Action,
    KernelState,
    Config
)
→
(
    KernelState',
    RuntimeCommand
)
```

where

- `Action` is produced by PolicyRouter.
- `KernelState` is the current runtime state.
- `RuntimeCommand` is a request emitted to the Runtime.

The Kernel never communicates directly with the Backend.

---

# 5. RuntimeCommand

RuntimeCommand is a non-authoritative instruction emitted by the Kernel.

Typical commands include

```
proceed

discard

sleep

regenerate

regenerate-with-penalty

terminate
```

Execution of RuntimeCommand belongs exclusively to the Runtime.

---

# 6. State Transition Rules

## accept

The Candidate is accepted.

The Candidate is materialized into one or more canonical Events.

```
Working.Candidate
        │
        ▼
Event Mapping
        │
        ▼
Commit(Event)
```

### Mutation

```
Canonical.History++

if Event.intent ∈ {

    memory-write

    recover

}

Canonical.MemoryRef++
```

Lamport Clock advances.

DeferredQueue is unchanged.

Working is reinitialized.

### RuntimeCommand

```
proceed
```

---

## reject

The Candidate is permanently discarded.

### Mutation

```
Canonical
    unchanged

DeferredQueue
    unchanged

Working
    reinitialized
```

### RuntimeCommand

```
discard
```

---

## defer

The Candidate is temporarily postponed.

### Mutation

```
DeferredQueue.enqueue(

    Working.Candidate

)
```

```
Canonical
    unchanged

Working
    preserved
```

### RuntimeCommand

```
sleep
```

---

## retry

Generation should be attempted again using the same Canonical state.

### Mutation

```
Canonical
    unchanged

DeferredQueue
    unchanged

Working
    preserved
```

### RuntimeCommand

```
regenerate
```

---

## retry-penalty

Generation should be retried with an adjusted decoding policy.

### Mutation

```
Canonical
    unchanged

DeferredQueue
    unchanged
```

```
Working.GenerationPolicy
    updated
```

or

```
Working.DecodingPolicy
    updated
```

according to the configured penalty strategy.

### RuntimeCommand

```
regenerate-with-penalty
```

---

## abort

A fatal unrecoverable failure has occurred.

### Mutation

```
Canonical
    unchanged

DeferredQueue
    unchanged

Working
    preserved
```

Kernel emits a deterministic FaultEvent.

### RuntimeCommand

```
terminate
```

---

# 7. DeferredQueue Semantics

DeferredQueue is owned exclusively by the Kernel.

Validation cannot enqueue.

PolicyRouter cannot enqueue.

Deferred candidates are revalidated only after Canonical advances.

Wakeup condition

```
Commit(Event)

↓

Lamport Clock++

↓

Canonical advances

↓

DeferredQueue Wakeup

↓

Revalidation
```

Timeout-based wakeup is outside the scope of R1.

---

# 8. Canonical Advancement

Canonical advances if and only if Commit succeeds.

Canonical advancement consists of

1. Event persistence
2. History update
3. MemoryRef update (when applicable)
4. Lamport Clock increment

Canonical advancement is the only trigger for DeferredQueue wakeup.

---

# 9. FaultEvent

Kernel emits a FaultEvent only during an `abort` transition.

FaultEvent records deterministic diagnostic information for post-mortem analysis.

FaultEvent does not belong to Canonical History.

Its ABI is defined in

```
05-validation-pipeline-r0.md
```

---

# 10. Determinism Guarantee

Given identical

- KernelState
- Config
- Action

the Kernel MUST always produce identical

- KernelState'
- RuntimeCommand

independent of

- platform
- language
- operating system
- execution timing

---

# 11. Constitutional Invariants

The following invariants are enforced.

- Validation determines what is true.
- PolicyRouter determines what should happen.
- Kernel determines how state changes.
- Runtime performs external execution.
- Only Commit may mutate Canonical.
- Kernel never invokes the LLM Backend.
- RuntimeCommand never mutates Canonical.
- DeferredQueue is owned exclusively by the Kernel.
- Kernel state transitions are deterministic and atomic.

---

# 12. Architectural Position

The Kernel occupies the deterministic execution boundary.

```
Candidate
        │
        ▼
Validation
        │
        ▼
ValidationReport
        │
        ▼
PolicyRouter
        │
        ▼
Action
        │
        ▼
Kernel
        │
        ▼
KernelState'
        │
        ▼
RuntimeCommand
        │
        ▼
Runtime
```

This separation guarantees that probabilistic LLM behavior never directly mutates the authoritative system state.