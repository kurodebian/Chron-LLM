# Chron-LLM Memory Model Specification

**Status:** Normative
**Version:** R1

# Purpose

This specification defines the deterministic memory architecture used by Chron-LLM.

# Memory Layers

The runtime defines three logical memory layers.

## Short-Term Memory

Stores the most recent committed Events.

Characteristics

- bounded
- replayable
- deterministic

```
ShortTermMemory := History[last N Events]
```

## Long-Term Memory

Stores persistent knowledge.

Characteristics

- implementation-defined storage
- mutable only through Commit when represented as Canonical Memory
- replay compatible

## Canonical Memory

CanonicalMemory is the authoritative memory referenced by the runtime.

Only Commit may modify CanonicalMemory.

# MemoryRef

MemoryRef identifies memory visible to Replay and Prompt Builder.

```
MemoryRef :=
{
short-term
long-term
canonical
}
```

# Intent Semantics

## memory-read

```
Derived.MemoryRef
│
▼
Prompt
```

No mutation occurs.

## memory-write

```
Commit(Event)

↓

CanonicalMemory++

↓

MemoryRef updated
```

Only Commit may update CanonicalMemory and MemoryRef.

## recover

Recovery includes MemoryRef during Prefill reconstruction.

```
Replay
│
MemoryRef
│
▼
Prefill
```

# Invariants

- Only Commit updates CanonicalMemory.
- Only Commit updates authoritative MemoryRef.
- MemoryRef is deterministic.
- MemoryRef participates in Replay.
- MemoryRef is replayable.