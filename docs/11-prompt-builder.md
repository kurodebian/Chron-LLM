# Chron-LLM Prompt Builder Specification

**Status:** Normative
**Version:** R1

---

# Purpose

Define deterministic prompt construction.

---

# Prompt Components

Prompt SHALL be derived from

- Summary
- Graph
- MemoryRef
- Config

---

# Construction


History

↓

Replay

↓

Summary

Graph

MemoryRef

Config

↓

Prompt


---

# Exclusions

Prompt SHALL NOT contain

- Observation
- FaultEvent
- detector outputs
- runtime metrics

Observation is runtime control information only.

---

# Invariants

Prompt generation is deterministic.

Prompt depends only on Replay outputs.