# Chron-LLM_R2.0-B_World_Runtime_Constitution_Spec.md

**Document ID:** CHRON-R2.0-B-WORLD-CONSTITUTION

**Status:** Constitution Revision 2.0 — Freeze Candidate

**Target:** CodeX Implementation & Verification Suite

**Phase:** R2.0-B Worldline Runtime

**Purpose:** Deterministic World Runtime Foundation

**Depends on:** Chron-LLM_R2.0-A_Graph_Runtime_Core_Constitution_Spec.md (Constitution Revision 1.0)

---

# 0. Purpose

R2.0-B defines the constitutional semantics of Worldline Runtime.

Its purpose is to establish deterministic execution views over a single Canonical Graph without duplicating history or violating the deterministic guarantees established in R2.0-A.

The World Runtime extends the deterministic kernel while preserving all R2.0-A invariants.

---

# 1. Core Philosophy

Chron-LLM separates truth from observation.

```
Kernel      = Authority
Graph       = Truth
Memory      = Content
World       = Execution View
Projection  = Observation
Prompt      = Usage
Backend     = Generation
Evaluator   = Proposal
```

Fundamental principles:

```
Truth is unique.
Views are multiple.
History is shared.
Execution is isolated.
```

---

# 2. World Identity Contract

A World is a persistent identity associated with an evolving execution position.

```
Identity(World) := world.id
```

Two Worlds are identical if and only if:

```
world.id is identical
```

The following fields are properties, not identity:

- head-node
- projection-policy
- metadata
- lifecycle state

## Requirements

world.id:

- MUST be globally unique.
- MUST never be reused.
- MUST remain stable for the lifetime of the World.

---

# 3. Graph Ownership & Sharing Contract

Exactly one Canonical Graph exists.

Exactly one Memory Store exists.

Every World references these shared objects.

```
Canonical Graph
        ▲
        │
   graph-ref
        │
     World
```

Requirements:

- All Worlds MUST resolve to the same Canonical Graph.
- All Worlds MUST resolve to the same Memory Store.
- Worlds MUST NOT own the Graph.
- Worlds MUST NOT own the Memory Store.
- Kernel owns truth.

---

# 4. World = View Contract

A World represents an execution view.

```
World :=
    graph-ref
    memory-ref
    root-node
    head-node
    projection-policy
    metadata
```

Where:

- graph-ref resolves to the unique Canonical Graph.
- memory-ref resolves to the unique Memory Store.

Worlds contain no historical data.

History exists only inside the Canonical Graph.

---

# 5. Commit Visibility Contract

Visibility order is constitutionally fixed.

```
Commit
    ↓
Canonical Graph Update
    ↓
World Head Update
    ↓
Visible Execution State
```

Requirements:

- Graph MUST be updated first.
- World head-node MUST be updated second.
- World MUST NEVER reference uncommitted nodes.
- World MUST NEVER point to future history.

---

# 6. Root Node Contract

root-node defines the historical origin of a World.

Requirements:

- MUST exist in the Canonical Graph.
- MUST never change after World creation.

---

# 7. Head Node Contract

head-node defines the current execution position.

Requirements:

- MUST exist in the Canonical Graph.
- MAY advance only through Kernel-approved commits.
- MUST NOT point to future nodes.
- MUST NOT point to non-existent nodes.
- Only the Kernel MAY modify head-node.

Backend, Evaluator, Registry, and Projection MUST NOT directly update head-node.

---

# 8. Projection Policy Contract

Projection Policy defines how history is viewed.

It never modifies history.

Requirements:

Projection Policy:

- MUST be deterministic.
- MUST be immutable during a World's lifetime.
- MUST NOT modify Graph.
- MUST NOT modify Memory.

Changing Projection Policy requires creating a new World.

---

# 9. Metadata Boundary Contract

Metadata stores World-specific transient information.

Requirements:

Metadata:

- MAY differ between Worlds.
- MUST follow Copy-on-Write semantics.
- MUST NOT contain Graph state.
- MUST NOT contain Memory state.
- MUST NOT cache Graph nodes.
- MUST NOT shadow Canonical history.

---

# 10. World Isolation Contract

Worlds are execution-isolated.

Updating one World MUST NOT modify another World.

Communication between Worlds occurs exclusively through Kernel-approved Graph commits.

No direct World-to-World mutation is permitted.

---

# 11. Branch Contract

fork-world creates a new execution view.

It does not duplicate history.

Requirements:

MUST preserve:

- root-node

MUST initialize:

- head-node = parent.head-node

MUST copy:

- projection-policy
- metadata (Copy-on-Write)

MUST NOT copy:

- Graph
- Memory

fork-world MUST be deterministic.

Given identical parent World and identical inputs:

All child properties MUST be identical except world.id.

---

# 12. Registry Contract

Registry indexes Worlds.

Kernel defines World semantics.

```
Kernel owns truth.
Registry owns discovery.
```

Registry MUST:

- register Worlds
- resolve World identifiers
- maintain ancestry
- manage active World

Registry MUST NOT:

- derive truth
- modify Graph
- modify Memory
- modify World semantics

---

# 13. Required Registry API

Required ABI:

```
register-world
find-world
active-world
set-active-world
list-worlds
```

Every API defined here MUST have deterministic verification tests.

---

# 14. Registry Persistence Contract

Registry MUST preserve:

- world.id
- ancestry
- active World

Registry MAY rebuild derived indexes.

Persistent data represents truth.

Derived indexes represent cache.

---

# 15. World Lifecycle Contract

Lifecycle:

```
CREATED
    ↓
ACTIVE
    ↓
INACTIVE
    ↓
ARCHIVED
```

Requirements:

ARCHIVED Worlds:

- MUST NOT become ACTIVE again.
- MUST remain addressable.
- MAY be referenced by replay.

Reactivation requires creation of a new World.

---

# 16. Replay Boundary Contract

Replay Input is defined as:

```
Replay Input :=

Canonical Graph
Memory Store
World State
```

Where:

```
World State :=

world.id
head-node
projection-policy
metadata
```

Replay MUST NOT depend on:

- wall clock
- process id
- scheduler timing
- memory addresses
- thread interleaving
- random sources
- external mutable state

Replay MUST produce identical execution state for identical Replay Input.

---

# 17. World Invariants

The following invariants are constitutionally required.

- World identity is immutable.
- Root node is immutable.
- Head node always references committed history.
- Graph is globally shared.
- Memory is globally shared.
- Projection is deterministic.
- Metadata follows Copy-on-Write.
- Registry is non-authoritative.
- Replay is deterministic.

---

# 18. Branch Runtime Verification Suite

The following Kernel Invariants MUST PASS.

| Test ID | Name | Objective |
|----------|------|-----------|
| B1 | World Creation | make-world creates globally unique Worlds |
| B2 | World Fork | fork-world preserves ancestry |
| B3 | Root Stability | root-node never changes |
| B4 | Head Independence | child head updates never affect parent |
| B5 | Projection Isolation | Projection Policies remain isolated |
| B6 | Metadata CoW | Metadata follows Copy-on-Write |
| B7 | Graph Sharing | All Worlds resolve to the same Graph and Memory |
| B8 | Replay Independence | Replay is deterministic including World State |
| B9 | World Isolation | Worlds cannot mutate each other |
| B10 | Commit Visibility | Commit order is Graph → World |
| B11 | Registry Persistence | Registry preserves identity and ancestry |

Every constitutional API MUST have at least one deterministic verification test.

---

# 19. Out of Scope

R2.0-B explicitly excludes:

- Backend ABI
- Evaluator integration
- World persistence
- Distributed Registry
- Scheduler
- Merge
- Garbage Collection
- Tool execution

---

# 20. Constitution Freeze Criteria

Constitution Revision:

```
2.0
```

Status:

```
FROZEN
```

Freeze requires:

- All B1–B11 PASS.
- Every constitutional API has deterministic verification tests.
- World semantics are stable.
- Registry ABI is stable.
- Backward compatibility is guaranteed.

Breaking changes require a new Constitution Revision.

---

# Final Statement

This document defines the constitutional semantics of the Chron-LLM World Runtime.

It establishes deterministic World execution over a single shared Canonical Graph while preserving the deterministic kernel defined in Constitution Revision 1.0.

All future phases, including Backend ABI, Evaluator, Scheduler, Merge, Persistence, and distributed execution, MUST conform to the contracts defined herein.

No implementation may violate this Constitution without an approved Constitution Revision.