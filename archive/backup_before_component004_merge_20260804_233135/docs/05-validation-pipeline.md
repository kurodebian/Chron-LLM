# Chron-LLM Validation Pipeline Specification

**Status:** Normative  
**Version:** R1  
**Scope:** Deterministic validation and policy routing.

# 1. Purpose

This specification defines the deterministic validation boundary between non-authoritative Candidate generation and the deterministic Chron-LLM runtime.

The Validation Pipeline is responsible for:

- collecting objective facts
- producing a ValidationReport
- interpreting those facts through PolicyRouter
- producing a RuntimeRequest

This document does **not** define:

- kernel state transitions
- canonical mutation
- deferred execution
- runtime execution

These are defined by the Kernel State Machine.

# 2. Design Principles

## DP-1. Separation of Responsibilities

Validation performs validation only.

PolicyRouter performs interpretation only.

Kernel performs state transition only.

## DP-2. Fact-Oriented Reporting

Validation never returns decisions.

Validation returns facts only.

No PASS/FAIL state is required.

Success is represented by the absence of violations.

## DP-3. Deterministic Validation

Given identical

- Candidate
- Canonical
- Config

Validation MUST produce an identical ValidationReport.

Validation MUST NOT depend on

- timing
- randomness
- external mutable state

## DP-4. Configuration Independence

Configuration MAY modify routing policy.

Configuration MUST NOT modify

- validation semantics
- observation measurement semantics

# 3. Pipeline

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
RuntimeRequest
      │
      ▼
Kernel
```

RuntimeRequest is consumed exclusively by the Kernel.

Kernel behavior is defined by the Kernel State Machine.

# 4. Validation Layers

Validation consists of four deterministic layers.

```
SyntaxCheck
      │
      ▼
SemanticConsistencyCheck
      │
      ▼
InvariantCheck
      │
      ▼
ObservationCheck
      │
      ▼
ValidationReport
```

Each layer contributes objective facts.

No layer performs routing.

No layer mutates runtime state.

# 5. ValidationReport

```
ValidationReport
{
    candidate-id
    syntax-violations
    semantic-violations
    invariant-violations
    observations
}
```

ValidationReport contains facts only.

It contains no routing decision.

# 6. Observation

Observation records structural runtime facts.

```
Observation
{
    detector
    score
    threshold
    facts
}
```

Observation

- contains no routing logic
- contains no runtime decision
- never rejects a Candidate

# 7. PolicyRouter

PolicyRouter consumes a ValidationReport and produces a RuntimeRequest.

```
PolicyRouter(
    ValidationReport,
    Config
)
→ RuntimeRequest
```

RuntimeRequest is declarative.

It requests a runtime operation.

It performs no state transition.

# 8. RuntimeRequest

The RuntimeRequest domain object is defined by the Domain Model.

This specification defines the permitted RuntimeRequest kinds.

```
RuntimeRequest ∈ {

    commit-request

    reject-request

    defer-request

    retry-request

    retry-penalty-request

    abort-request

}
```

The semantics of RuntimeRequest execution are defined by the Kernel State Machine.

# 9. Routing Rules

The following rules define the deterministic evaluation order.

The resulting RuntimeRequest is determined according to the configured routing policy.

```
syntax violation
        ↓
reject-request

semantic violation
        ↓
reject-request

unrecoverable invariant
        ↓
reject-request

recoverable invariant
        ↓
defer-request

observation threshold exceeded
        ↓
configured retry /
retry-penalty /
abort

otherwise
        ↓
commit-request
```

# 10. Configuration

Configuration MAY define

- retry limit
- penalty strategy
- detector thresholds
- routing policy

Configuration SHALL NOT modify

- validation semantics
- observation semantics

# 11. Determinism Guarantee

The following functions are deterministic.

```
(Candidate, Canonical, Config)
        │
        ▼
ValidationReport
```

```
(ValidationReport, Config)
        │
        ▼
RuntimeRequest
```

# 12. Constitutional Invariants

The following principles are constitutionally frozen.

- Validation collects facts only.
- ValidationReport contains facts only.
- Observation contains structural facts only.
- PolicyRouter interprets facts only.
- Validation is deterministic.
- RuntimeRequest is declarative.
- RuntimeRequest is consumed exclusively by the Kernel.
- Configuration cannot change validation semantics.