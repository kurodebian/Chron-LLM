# Agent Domain Model v1.0 (Baseline)

---

# Purpose

This Domain Model defines the architectural concepts used by the Agent to instantiate the constitutional responsibilities defined by the Constitution.

It defines conceptual entities and relationships, not implementation details.

---

# Scope

This document defines:

- conceptual entities
- state categories
- relationships between concepts

This document does **not** define:

- representations
- algorithms
- execution order
- storage
- runtime implementations

---

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

---

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

---

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

---

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

---

# Working

Working is ephemeral and non-authoritative state.

```

Working {
Candidate
ProcessingState
}

```

Working contains temporary information used during non-authoritative processing.

---

# Derived

Derived is a non-authoritative representation derived from Canonical.

```

Derived {
Projection
Analysis
}

```

Derived is reproducible and does not introduce authoritative information.

---

# External

External represents non-authoritative state outside Canonical.

```

External {
ExternalReference
}

```

---

# Context

Context represents the information required to interpret current Agent operation.

```

Context {
CanonicalReference
}

```
