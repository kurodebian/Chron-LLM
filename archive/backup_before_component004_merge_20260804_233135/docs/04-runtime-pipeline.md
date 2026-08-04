# Agent Runtime Pipeline

**Status:** Normative  
**Version:** R1  
**Scope:** Runtime execution pipeline and component integration.

# 1. Purpose

This specification defines the execution pipeline of the Chron-LLM runtime.

It specifies the ordering and integration of runtime components.

This document defines **where** each component participates in execution.

It does **not** define:

- data models
- operational semantics
- validation rules
- kernel state transitions
- implementation details

These are specified by their respective normative specifications.

# 2. Runtime Flow

```
Input
    │
    ▼
Event
    │
    ▼
Commit
    │
    ▼
Replay
    │
    ▼
Projection
    │
    ▼
Graph
    │
    ▼
Summary
    │
    ▼
Prompt Builder
    │
    ▼
Backend
    │
    ▼
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
    │
    ▼
RuntimeCommand
    │
    ▼
Runtime
```

# 3. Pipeline Overview

The runtime pipeline is composed of the following stages.

| Stage | Purpose |
|--------|---------|
| Commit | Persist authoritative Events |
| Replay | Reconstruct execution context |
| Prompt Builder | Construct deterministic prompts |
| Backend | Generate non-authoritative Candidates |
| Validation | Produce ValidationReport |
| PolicyRouter | Produce RuntimeRequest |
| Kernel | Execute deterministic state transitions |
| Runtime | Execute RuntimeCommand |

# 4. Commit

Commit is the entry point through which authoritative Events become part of Canonical.

The operational semantics of Commit are defined by:

- Operational Semantics

The state transition semantics of Commit are defined by:

- Kernel State Machine

# 5. Replay

Replay reconstructs the execution context required by the Runtime from Canonical.

Replay produces:

- Projection
- Graph
- Summary

Replay semantics are defined by:

- Operational Semantics

# 6. Prompt Builder

Prompt Builder constructs deterministic prompts from runtime context.

Typical inputs include:

- Summary
- Graph
- Memory Reference
- Configuration

Prompt construction semantics are outside the scope of this specification.

# 7. Backend

The Backend generates a Candidate from the constructed Prompt.

Backend execution is explicitly non-authoritative.

Its output does not become authoritative until processed by the Validation → PolicyRouter → Kernel pipeline.

# 8. Validation

Validation evaluates a Candidate and produces a ValidationReport.

Validation semantics are defined by:

- Validation Pipeline

# 9. PolicyRouter

PolicyRouter interprets a ValidationReport and produces a RuntimeRequest.

PolicyRouter semantics are defined by:

- Validation Pipeline

# 10. Kernel

The Kernel consumes a RuntimeRequest and produces a RuntimeCommand.

Kernel state transition semantics are defined by:

- Kernel State Machine

# 11. Runtime

The Runtime executes RuntimeCommand.

Runtime execution is outside the scope of this specification.

# 12. Pipeline Invariants

The runtime pipeline satisfies the following architectural invariants.

- Only Commit may mutate Canonical.
- Replay is deterministic.
- Validation performs no state mutation.
- PolicyRouter performs no state mutation.
- Kernel performs deterministic state transitions.
- Backend is non-authoritative.
- Runtime executes RuntimeCommand without defining state transition semantics.

# 13. Related Specifications

- 00 Constitution
- 01 Domain Model
- 02 Operational Semantics
- 05 Validation Pipeline
- 06 Kernel State Machine