# Chron-LLM Recovery Specification

**Status:** Normative
**Version:** R1

# Purpose

Define deterministic recovery from abnormal runtime interruption.

# Recovery Boundary

Recovery reconstructs non-authoritative runtime state.

Recovery SHALL NOT mutate Canonical.

Only Commit may mutate Canonical.

# Input

```
Canonical
MemoryRef
```

# Output

```
Recovered Context
```

# Recovery Procedure

```
Canonical

↓

Replay

↓

Derived Reconstruction

↓

MemoryRef Reconstruction

↓

Working Reconstruction

↓

Resume Runtime
```

# Allowed Operations

Recovery MAY:

- destroy runtime cache
- destroy KV cache
- reconstruct Prefill
- reconstruct Derived
- reconstruct Working
- resume execution

# Forbidden Operations

Recovery SHALL NOT:

- mutate Canonical
- create authoritative Events
- bypass Commit

# Invariants

Recovery is deterministic.

Recovery is replay compatible.

Previous Canonical states remain recoverable.

Recovery does not introduce authoritative information.