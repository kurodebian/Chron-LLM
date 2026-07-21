# Chron-LLM Prompt Builder Specification

**Status:** Normative
**Version:** R1

# Purpose

Define deterministic prompt construction.

# Prompt Components

Prompt SHALL be derived from:

- Summary
- Graph
- MemoryRef
- Config

All prompt components SHALL originate from:

- Canonical
- deterministic Derived state
- deterministic Runtime Configuration

# Construction

```
Canonical

↓

Replay

↓

Derived Context

↓

Summary

Graph

MemoryRef

Config

↓

Prompt
```

# Exclusions

Prompt SHALL NOT contain:

- Observation
- FaultEvent
- detector outputs
- runtime metrics

Observation is runtime control information only.

FaultEvent is diagnostic information only.

Neither introduces authoritative information into Prompt construction.

# Invariants

Prompt generation is deterministic.

Prompt construction SHALL NOT mutate Canonical.

Prompt depends only on:

- deterministic Replay outputs
- deterministic Configuration