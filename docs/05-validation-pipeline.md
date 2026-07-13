# Chron-LLM Validation Pipeline Specification
## Release R0 (Frozen)

**Status:** FROZEN  
**Version:** R0  
**Scope:** Chron-LLM Deterministic Validation Kernel  
**Compatibility:** Forward Compatible (R1+ Extension Model)

---

# 1. Purpose

This specification defines the deterministic validation boundary between non-deterministic LLM generation and the deterministic Chron-LLM kernel.
The Validation Pipeline is responsible only for collecting objective facts regarding a Candidate.
Interpretation of those facts is delegated to PolicyRouter.
Mutation of system state is delegated exclusively to Kernel.
This separation guarantees deterministic behavior while allowing future extension of validators, detectors, and routing policies without changing the core ABI.

---

# 2. Design Principles

## DP-1. Separation of Responsibilities

Validation performs validation only.
PolicyRouter performs interpretation only.
Kernel performs state transition only.

---

## DP-2. Fact-Oriented Reporting

Validation never returns decisions.
Validation returns facts only.
No PASS/FAIL state is required.
Success is represented by the absence of violations.

---

## DP-3. Deterministic Validation

Given identical input:
- Candidate
- Canonical
- Config
Validation MUST produce an identical ValidationReport.
Validation MUST NOT depend on timing, randomness, or external mutable state.

---

## DP-4. Kernel Authority

Only Kernel may mutate:
- Canonical
- DeferredQueue
- Event Log
- World State
Validation and PolicyRouter are pure functions.

---

## DP-5. Configuration Independence

Configuration MAY modify routing policy.
Configuration MUST NOT modify validation semantics.

---

# 3. System Architecture

```
Candidate
        │
        ▼
+----------------------+
|     Validation       |
+----------------------+
        │
        ▼
ValidationReport
(Facts Only)
        │
        ▼
+----------------------+
|    PolicyRouter      |
+----------------------+
        │
        ▼
Action
        │
        ▼
+----------------------+
|       Kernel         |
+----------------------+
        │
        ├──────────────┐
        ▼              │
Canonical      DeferredQueue
        ▲              │
        └────Clock─────┘
```

---

# 4. Validation Pipeline

Validation consists of four independent layers.
Execution order is deterministic.
```
SyntaxCheck
        │
SemanticCheck
        │
InvariantCheck
        │
ObservationCheck
        │
ValidationReport
```
Each layer contributes facts.
No layer performs routing.
No layer mutates system state.

---

# 5. ValidationReport ABI

```lisp
ValidationReport
{
    candidate-id : CandidateID
    syntax-violations : [SyntaxViolation]
    semantic-violations : [SemanticViolation]
    invariant-violations : [InvariantViolation]
    observations : [Observation]
}
```
Empty arrays represent successful validation.

---

# 6. SyntaxViolation

```lisp
SyntaxViolation
{
    code : Symbol
    reason : String
}
```
Examples:
- ParseError
- InvalidToken
- UnsupportedFormat

---

# 7. SemanticViolation

```lisp
SemanticViolation
{
    code : Symbol
    reason : String
}
```
Examples:
- MissingMemoryReference
- InvalidMetadata
- CanonicalConflict

---

# 8. InvariantViolation

```lisp
InvariantViolation
{
    category : Symbol
    code : Symbol
    recoverable : Boolean
}
```
Categories:
- Clock
- Identity
- ABI
- Generation
- History
Examples:
```
Clock
    MonotonicViolation
Identity
    DuplicateID
ABI
    EventMismatch
Generation
    PartialGenerationViolation
History
    DependencyUnavailable
```
Recoverability:
```
false
    Permanent violation
true
    Temporary synchronization issue
```

---

# 9. Observation

```lisp
Observation
{
    detector : Symbol
    score : Float
    threshold : Float
    recommendation : Recommendation
}
```
Recommendation is one of:
```
retry
retry-penalty
abort
```
Observation contains no routing logic.
It merely reports detector output.

---

# 10. Validation Layer Specifications

---

## 10.1 SyntaxCheck

Purpose:
Validate structural correctness.
Input:
```
Candidate
```
Output:
```
SyntaxViolation*
```
Properties:
- deterministic
- pure
- stateless

---

## 10.2 SemanticCheck

Purpose:
Validate semantic consistency against Canonical.
Input:
```
Candidate
Canonical
```
Checks include:
- payload consistency
- metadata validity
- history references
Output:
```
SemanticViolation*
```
Properties:
- deterministic
- canonical-only

---

## 10.3 InvariantCheck

Purpose:
Validate deterministic kernel invariants.
Checks include:
Clock
Identity
ABI
Generation
History
Output:
```
InvariantViolation*
```

---

## 10.4 ObservationCheck

Purpose:
Observe runtime anomalies.
Observation does not reject.
Observation produces Observation objects.
Standard detectors (R0):
```
EchoDetector
StagnationDetector
DriftDetector
DiscontinuityDetector
```
Additional detectors may be introduced in future versions.
No ABI modification is required.

---

# 11. PolicyRouter

PolicyRouter consumes ValidationReport.
It performs no validation.
It performs no observation.
It performs interpretation only.
Signature:
```lisp
PolicyRouter(
    ValidationReport,
    Config
)
→ Action
```

---

# 12. Routing Rules

Rules are evaluated in priority order.

---

## Rule 1

If
```
syntax-violations ≠ ∅
```
Return
```
reject
```

---

## Rule 2

If
```
semantic-violations ≠ ∅
```
Return
```
reject
```

---

## Rule 3

If any
```
InvariantViolation
recoverable = false
```
Return
```
reject
```

---

## Rule 4

If
```
InvariantViolation
recoverable = true
```
and no unrecoverable violation exists
Return
```
defer
```

---

## Rule 5

If observations exist whose
```
score >= threshold
```
Return the highest recommendation.
Priority:
```
abort
>
retry-penalty
>
retry
```

---

## Rule 6

If no violations exist
and no observation exceeds threshold
Return
```
accept
```

---

# 13. DeferredQueue

DeferredQueue is owned exclusively by Kernel.
Validation cannot enqueue.
PolicyRouter cannot enqueue.
Kernel enqueues after Action == defer.

---

## Wakeup Condition

DeferredQueue SHALL NOT use timeout.
Deferred candidates SHALL be revalidated only after Canonical advances.
Trigger:
```
Canonical Commit
↓
Lamport Clock++
↓
DeferredQueue Wakeup
↓
Revalidation
```
This guarantees deterministic replay.

---

# 14. Kernel Actions

Possible actions:
```
accept
reject
defer
retry
retry-penalty
abort
```
Only Kernel executes actions.

---

# 15. FaultEvent ABI

```lisp
FaultEvent
{
    id : FaultID
    clock : LamportClock
    origin : Symbol
    cause : String
    detector : Symbol
    candidate-id : CandidateID
    extensions : Map
}
```
Origin examples:
```
Validation
Scheduler
Commit
Replay
```
Extensions MAY contain implementation-specific debugging information.

---

# 16. Configuration

Configuration belongs outside Validation.
Examples:
```
retry-limit
penalty-strategy
detector-thresholds
logging
metrics
telemetry
```
Configuration SHALL NOT alter validation semantics.

---

# 17. Extension Rules

Future versions MAY add:
- new detectors
- new invariant categories
- new recommendation strategies
- new policy implementations
Future versions MUST NOT:
- mutate ValidationReport semantics
- change Kernel authority
- introduce state mutation inside Validation

---

# 18. Determinism Guarantee

The following function is deterministic:
```
(Candidate,
 Canonical,
 Config)
        │
        ▼
ValidationReport
```
The following function is deterministic:

```
(ValidationReport,
 Config)
        │
        ▼
Action
```
Kernel is the sole owner of state transition.

---

# 19. Frozen Constitutional Invariants

The following principles are constitutionally frozen in R0.
1. Validation collects facts only.
2. ValidationReport contains facts only.
3. PolicyRouter interprets facts only.
4. Kernel is the only component allowed to mutate state.
5. DeferredQueue is owned by Kernel.
6. Validation is deterministic.
7. Policy is configurable.
8. Semantics are immutable.

---

# End of Specification

**Document Status:** FROZEN

**Release:** Chron-LLM Validation Pipeline R0

**This document defines the deterministic observation boundary between probabilistic LLM generation and the Chron-LLM deterministic kernel.**