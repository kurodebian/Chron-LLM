# Agent Domain Model v1.0 (Baseline)

# Purpose

This Domain Model defines the architectural concepts used by the Agent to instantiate the constitutional responsibilities defined by the Constitution.

It defines conceptual entities and relationships, not implementation details.

# Scope

This document defines:

- conceptual entities
- state categories
- ownership of conceptual entities
- producer / consumer relationships

This document does **not** define:

- representations
- algorithms
- execution order
- storage
- runtime implementations
- operational semantics

# Event

An Event represents a causal fact.

```
Event {
    id
    source ∈ {
        user,
        assistant,
        tool,
        system
    }
    content
    metadata {
        timestamp
        seq
        causal-reference?
    }
}
```

Source identifies the origin of an Event.

Source does not determine authority.

Committed Events constitute Evidence.

Evidence is causally ordered.

# Candidate

A Candidate represents a non-authoritative proposal.

```
Candidate {
    id
    origin
    intent
    content
    constraints
    metadata
}
```

Intent describes the proposed operation.

```
intent ∈ {
    append,
    reflect,
    tool,
    memory-read,
    memory-write,
    recover,
    summarize
}
```

Candidate representation is implementation-defined.

An implementation may represent a Candidate using an intermediate form such as OperationIR.

# ValidationReport

ValidationReport represents the objective facts collected during validation.

Its detailed structure is defined by the Validation Pipeline specification.

# RuntimeRequest

RuntimeRequest represents a declarative request produced by PolicyRouter.

```
RuntimeRequest {
    kind
    payload
}
```

```
kind ∈ {
    commit-request
    reject-request
    defer-request
    retry-request
    retry-penalty-request
    abort-request
}
```

Its detailed structure and semantics are defined by the Validation Pipeline specification.

# RuntimeCommand

RuntimeCommand represents a declarative command emitted by the Kernel for execution by the Runtime.

```
RuntimeCommand {
    kind
    payload
}
```

```
kind ∈ {
    proceed
    discard
    sleep
    regenerate
    regenerate-with-penalty
    terminate
}
```

Its detailed structure and semantics are defined by the Kernel State Machine specification.

# FaultEvent

FaultEvent represents deterministic diagnostic information produced by the Kernel.

```
FaultEvent {
    type
    reason
    metadata
}
```

Its operational semantics are defined by the Kernel State Machine specification.

# Session

A Session consists of four constitutional state categories.

```
Session {
    Canonical
    Working
    Derived
    External
}
```

Session is the top-level runtime container.

# Canonical

Canonical is the authoritative state.

```
Canonical {
    Evidence
    Configuration
    MemoryReference
}
```

Canonical is mutated only through Commit.

# Working

Working is ephemeral and non-authoritative state.

```
Working {
    Candidate
    ProcessingState
}
```

Working contains temporary information used during non-authoritative processing.

# Derived

Derived is a non-authoritative representation derived from Canonical.

```
Derived {
    Projection
    Analysis
}
```

Derived is reproducible and does not introduce authoritative information.

# External

External represents non-authoritative state outside Canonical.

```
External {
    ExternalReference
}
```

# Context

Context represents the information required to interpret current Agent operation.

```
Context {
    CanonicalReference
}
```

Its concrete representation is implementation-defined.

# Ownership

| Object | Owner | Reader |
| --- | --- | --- |
| Candidate | Runtime | Validation, Kernel |
| ValidationReport | Validation | PolicyRouter |
| RuntimeRequest | PolicyRouter | Kernel |
| RuntimeCommand | Kernel | Runtime |
| FaultEvent | Kernel | Observability |
| Canonical | Kernel | Replay, Validation |
| Working | Runtime | Runtime |
| Derived | Replay | Runtime |
| External | Runtime | Runtime |

Ownership specifies the component responsible for creating or mutating the corresponding object.

# Producer / Consumer

| Object           | Produced by  | Consumed by        |
| ---------------- | ------------ | ------------------ |
| Event            | Commit       | Replay, History    |
| Candidate        | Backend      | Validation         |
| ValidationReport | Validation   | PolicyRouter       |
| RuntimeRequest   | PolicyRouter | Kernel             |
| RuntimeCommand   | Kernel       | Runtime            |
| FaultEvent       | Kernel       | Observability      |
| Derived          | Replay       | Prompt Builder     |
| Canonical        | Commit       | Replay, Validation |

Producer / Consumer relationships describe the architectural flow of conceptual objects.

Operational semantics are defined by the corresponding specifications.
