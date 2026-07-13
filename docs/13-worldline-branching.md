# Chron-LLM Worldline Branching Specification

**Status:** Normative
**Version:** R1

---

# Purpose

Define deterministic worldline branching.

---

# Worldline

A worldline is identified by


causal-id


---

# Branch Conditions

A new causal-id SHALL be generated when

- discontinuity detected
- abort issued
- drift detected three consecutive times
- stagnation detected five consecutive times

---

# Branch Procedure


Generate new causal-id

↓

Destroy KV Cache

↓

Traverse Graph using causal edges only

↓

Construct clean Prefill

↓

Record new causal-id

↓

Resume execution


---

# Canonical

The new causal-id SHALL be committed through Commit.

Only Commit may mutate Canonical.

---

# Invariants

Worldline branching is deterministic.

Branch history remains replayable.

Previous worldlines remain immutable.