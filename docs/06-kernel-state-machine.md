# Chron-LLM Kernel State Machine Specification

**Status:** Normative  
**Version:** R1  
**Scope:** Deterministic authoritative state transitions executed by the Kernel.

# 1. Purpose

This specification defines the deterministic state transitions executed by the Chron-LLM Kernel.

The Kernel is the sole component authorized to execute RuntimeRequests and mutate the authoritative system state.

This document defines **how authoritative state changes**.

It does not define Validation, PolicyRouter, or Runtime behavior.

# 2. Design Principles

## Single Mutator

Only the Kernel may mutate

- Canonical
- DeferredQueue
- FaultEvent Log

## Deterministic State Transition

The Kernel performs

- no validation
- no policy interpretation
- no external I/O
- no Backend invocation

Given identical inputs, the Kernel SHALL produce identical outputs.

## Runtime Separation

The Kernel emits RuntimeCommands.

Execution of RuntimeCommands belongs exclusively to the Runtime.

## Clock-Driven Execution

Kernel state evolution depends solely on Canonical advancement.

Wall-clock time shall not affect Kernel state transitions.

# 3. Kernel State

The Kernel operates on

```
KernelState
```

whose structure is defined by the Domain Model.

KernelState contains

- Canonical
- DeferredQueue
- Working

# 4. Kernel Function

The deterministic transition function is

```
Kernel(
    RuntimeRequest,
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

- RuntimeRequest is produced by PolicyRouter.
- RuntimeCommand is consumed by the Runtime.

# 5. RuntimeCommand

The RuntimeCommand domain object is defined by the Domain Model.

This specification defines its execution semantics.

Typical commands are

```
proceed

discard

sleep

regenerate

regenerate-with-penalty

terminate
```

Execution semantics belong to the Runtime.

# 6. State Transition Rules

## commit-request

The Candidate is materialized into one or more Events.

```
Working.Candidate
        │
        ▼
Event Mapping
        │
        ▼
Commit(Event)
```

Mutation

```
Canonical.History++

if Event.intent ∈ {

    memory-write

    recover

}

Canonical.MemoryRef++
```

Lamport Clock advances.

DeferredQueue remains unchanged.

Working is reinitialized.

RuntimeCommand

```
proceed
```

---

## reject-request

Mutation

```
Canonical unchanged

DeferredQueue unchanged

Working reinitialized
```

RuntimeCommand

```
discard
```

---

## defer-request

Mutation

```
DeferredQueue.enqueue(

    Working.Candidate

)
```

```
Canonical unchanged

Working preserved
```

RuntimeCommand

```
sleep
```

---

## retry-request

Mutation

```
Canonical unchanged

DeferredQueue unchanged

Working preserved
```

RuntimeCommand

```
regenerate
```

---

## retry-penalty-request

Mutation

```
Canonical unchanged

DeferredQueue unchanged
```

```
Working.GenerationPolicy updated
```

or

```
Working.DecodingPolicy updated
```

according to the configured penalty policy.

RuntimeCommand

```
regenerate-with-penalty
```

---

## abort-request

Mutation

```
Canonical unchanged

DeferredQueue unchanged

Working preserved
```

Kernel emits a deterministic FaultEvent.

RuntimeCommand

```
terminate
```

# 7. DeferredQueue

DeferredQueue is owned exclusively by the Kernel.

Candidates are revalidated only after Canonical advances.

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

# 8. Canonical Advancement

Canonical advances if and only if Commit succeeds.

Canonical advancement consists of

1. Event persistence
2. History update
3. MemoryRef update (when applicable)
4. Lamport Clock increment

Canonical advancement is the sole trigger for DeferredQueue wakeup.

# 9. FaultEvent

FaultEvent is emitted only during an `abort-request` transition.

FaultEvent is non-authoritative.

Its ABI is defined in

```
01-domain-model.md
```

# 10. Determinism Guarantee

Given identical

- KernelState
- RuntimeRequest
- Config

the Kernel SHALL always produce identical

- KernelState'
- RuntimeCommand

independent of

- platform
- language
- operating system
- execution timing

# 11. Constitutional Invariants

The following invariants are enforced.

- Only Commit may mutate Canonical.
- RuntimeCommand never mutates Canonical.
- DeferredQueue is owned exclusively by the Kernel.
- Kernel never invokes the Backend.
- Kernel state transitions are deterministic and atomic.

# 12. Architectural Position

```
RuntimeRequest
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

The Kernel forms the deterministic execution boundary between PolicyRouter and Runtime.