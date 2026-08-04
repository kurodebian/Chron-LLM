# Chron-LLM_R2.0-D_Commit_Kernel_Constitution_Spec.md

**Document ID:** CHRON-R2.0-D-COMMIT-KERNEL-CONSTITUTION

**Constitution Revision:** 1.0

**Status:** Freeze Candidate

**Classification:** Constitution-Level Specification

**Layer:** R2.0-D Commit Kernel

**Depends on:**

- Chron-LLM R2.0-A Graph Runtime Core Constitution
- Chron-LLM R2.0-B World Runtime Constitution
- Chron-LLM R2.0-C Observability Runtime Constitution

# 0. Purpose

This document defines the only constitutionally valid mechanism for changing the Canonical state of Chron-LLM.

Any state transition outside this Commit Kernel is unconstitutional.

R2.0-D defines the deterministic Commit Kernel responsible for transforming validated Candidate Events into Canonical history.

The purpose of this Constitution is to guarantee:

- Canonical state uniqueness
- Deterministic state transition
- Append-only history
- World visibility consistency
- WAL-backed recovery
- Immutable Memory guarantees

# 1. Core Philosophy

Chron-LLM authority model:

```
Kernel        = Authority
Commit Kernel = State Transition Authority
Graph         = Canonical History Structure
Memory        = Immutable Content Store
World         = Execution View
Observation   = Read-only State Description
Evaluator     = Proposal Generator
Backend       = Generation Engine
```

Fundamental rule:

Only Commit Kernel creates Canonical Event.

Only Canonical Event advances World Head.

Only WAL-backed Commit becomes Canonical truth.

Failed Commit never changes Canonical.

# 2. Commit Kernel Responsibility Boundary

## 2.1 Responsibilities

Commit Kernel SHALL:

- receive Candidate Event
- resolve World
- resolve Current World Head
- validate parent eligibility
- generate deterministic identifiers
- append Commit Journal entry
- append Canonical Graph node
- advance World Head
- generate Commit Result

## 2.2 Non Responsibilities

Commit Kernel SHALL NOT:

- generate Candidate Event
- execute Backend generation
- evaluate quality
- select strategy
- create prompts
- modify Memory content
- modify Projection Policy
- modify Evaluator logic
- modify World semantics

# 3. Candidate Event Contract

Candidate Event represents a proposed state transition.

Candidate Event is not Canonical.

```
(defstruct candidate-event
  type
  world-id
  parent-id
  payload-ref
  metadata
  schema-version)
```

## 3.1 Candidate Rules

Candidate Event:

* MUST NOT contain payload content directly.
* MUST reference Memory through payload-ref.
* MUST be validated before Commit.
* MUST NOT modify Canonical state.

# 4. Canonical Event Contract

Canonical Event represents accepted history.

```
(defstruct canonical-event
  event-id
  causal-id
  parent-id
  world-id
  type
  payload-ref
  schema-version)
```

## 4.1 Canonical Event Rules

Canonical Event:

* MUST be immutable.
* MUST correspond to exactly one Graph Node append.
* MUST reference immutable Memory content.
* MUST represent accepted history only.

Timestamp fields are prohibited.

Reason:

```
Wall Clock Time is not deterministic.
```

# 5. Identifier Contract

Chron-LLM separates object identity and causal position.

## 5.1 event-id

Meaning:

```
Deterministic identity of Canonical Event Node
```

Generation:

```
event-id =
H(
 parent-id,
 world-id,
 type,
 payload-ref,
 schema-version
)
```

## 5.2 causal-id

Meaning:

```
Causal position identity
```

Generation:

```
causal-id =
H(
 parent-causal-id,
 world-id,
 type,
 payload-ref,
 schema-version
)
```

## 5.3 Identifier Requirements

Identifiers:

* MUST be deterministic.
* MUST be reproducible during replay.
* MUST NOT depend on:

  * timestamp
  * process id
  * memory address
  * random value

# 6. Single Event Commit Contract

Commit granularity:

```
1 Commit
 =
1 Canonical Event
 =
1 Graph Node Append
```

Multi-event transaction semantics are outside R2.0-D scope.

Future transactional layers MUST be implemented above Commit Kernel.

# 7. Commit Phase Order

Commit execution order is constitutionally fixed.

```
Candidate Receive

      ↓

Resolve World

      ↓

Resolve Current World Head

↓

Validate Parent Eligibility

↓

Generate event-id / causal-id

      ↓

WAL Append

      ↓

Graph Append

      ↓

World Head Advance

      ↓

Commit Receipt
```

No implementation may reorder these phases.

# 8. WAL Contract

## 8.1 Definition

WAL is:

```
Durable Commit Record
```

WAL records durable accepted commit transitions before Canonical visibility.

## 8.2 Authority Separation

```
Candidate Event

      ↓

WAL
 |
 | durable commit record
 |
 v

Canonical Graph
 |
 | runtime causal structure
 |
 v

World
 |
 | execution view
```

## 8.3 WAL Requirements

WAL MUST contain:

* event-id
* causal-id
* parent-id
* world-id
* type
* payload-ref
* schema-version

# 9. Commit Internal State

Commit Kernel MAY internally maintain implementation-defined transient states.

Example:

```
STAGED

↓

WAL_COMMITTED

↓

GRAPH_COMMITTED

↓

WORLD_COMMITTED
```

Internal states MUST NOT expose partial Canonical visibility.

External behavior:

```
SUCCESS
or
NO STATE CHANGE
```

# 10. World Head Visibility Contract

The World Head represents visible committed execution state.

Rules:

* Head MUST reference existing Graph node.
* Head MUST reference committed history.
* Head MUST never reference WAL-only state.
* Only Commit Kernel may advance head.

Visibility order:

```
WAL

 ↓

Graph Append

 ↓

World Head Update

 ↓

Visible State
```

# 11. Reject / Fault / Duplicate Contract

## 11.1 Reject

Rejected candidates:

* MUST NOT enter Canonical.
* MUST NOT update World.
* MUST NOT update Graph.

Examples:

```
invalid-parent
invalid-payload
schema-mismatch
```

## 11.2 Fault

Faults are non-Canonical.

Fault information belongs to:

* Fault Log
* Observability
* Debug Trace

Canonical Fault Events require explicit future specification.

## 11.3 Duplicate Commit

Commit MUST be idempotent.

Given identical Candidate Identity:

```
Commit(A)
Commit(A)
```

MUST produce:

```
same event-id
same causal-id
same result
```

# 12. Commit Result ABI

Commit Kernel returns:

```
(defstruct commit-result
  status
  event-id
  causal-id
  world-id
  reason)
```

Status values:

```
:committed
:rejected
:fault
```

# 13. Determinism Boundary

Given identical constitutionally defined Commit inputs,

the produced Commit Result MUST be identical.

Commit Kernel determinism is defined solely by the constitutionally defined Commit inputs.

Commit MUST NOT depend on:

* wall clock
* random source
* external mutable state
* thread ordering
* operating system timing

# 14. Verification Suite

## D1 — Valid Commit

Verify successful Candidate creates Canonical Event.

## D2 — Invalid Candidate Reject

Invalid Candidate MUST NOT mutate Canonical.

## D3 — Deterministic Identifier Generation

Given identical constitutionally defined Commit inputs,

event-id and causal-id MUST be identical.

## D4 — Graph Append Only

Commit MUST only append Graph history.

## D5 — World Visibility Order

Verify:

```
WAL
→
Graph
→
World Head
```

## D6 — WAL Replay

WAL replay MUST reconstruct identical Canonical state.

## D7 — Duplicate Commit

Repeated identical Commit MUST return identical result.

## D8 — Crash Recovery

Interrupted Commit MUST recover without Canonical corruption.

## D9 — Cross World Isolation

Commit in one World MUST NOT mutate another World.

## D10 — Memory Immutability

Commit MUST NOT modify Memory payload.

# 15. Out of Scope

R2.0-D excludes:

* Backend ABI
* Scheduler
* Evaluator implementation
* Merge Runtime
* Distributed Commit
* Garbage Collection
* Tool Execution
* Network Coordination

# 16. Constitution Freeze Criteria

Constitution Revision:
```
1.0
```
Freeze Target Status:

```
FROZEN
```
Freeze requires:

- The Commit Kernel conforms to this Constitution.
- All D1–D10 PASS.
- Commit ABI is stable.
- WAL contract is validated.
- Recovery behavior is deterministic.
- Canonical transition authority is preserved.

After Freeze:

- This Constitution Revision becomes immutable.
- Semantic compatibility is guaranteed.
- Any breaking change requires a new Constitution Revision.

# Final Statement

Chron-LLM R2.0-D Commit Kernel defines the only constitutionally valid mechanism for changing the Canonical state of Chron-LLM.

It guarantees:

* deterministic commits
* immutable history
* WAL-backed recovery
* isolated worlds
* reproducible execution

All future Runtime layers MUST conform to this Commit Constitution.

No component may bypass Commit Kernel to modify Canonical state.
