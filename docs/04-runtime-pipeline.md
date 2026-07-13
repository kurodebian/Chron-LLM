# Agent Runtime Specification

**Status:** Normative  
**Version:** R1  
**Scope:** Runtime execution pipeline and integration points

---

# Runtime Flow

```
Input
    │
    ▼
Event(user)
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
Backend (LLM)
    │
    ▼
Candidate (OperationIR)
    │
    ▼
Validation
    │
    ├──────────────► ObservationCheck(Graph, Candidate)
    │
    ▼
ValidationReport
    │
    ▼
PolicyRouter
    │
    ▼
Action
    │
    ▼
Kernel
    │
    ▼
Action Dispatch
    │
    ├──────────────► Commit(Event)
    │                    │
    │                    ▼
    │                 Canonical
    │                    │
    │                    ▼
    │                  Replay
    │                    │
    │                    ▼
    │                  Derived
    │
    ├──────────────► DeferredQueue
    │                    │
    │                    ▼
    │          Canonical Advance
    │                    │
    │                    ▼
    │              Revalidation
    │
    ├──────────────► Retry
    │
    ├──────────────► RetryPenalty
    │
    └──────────────► Abort
                         │
                         ▼
                    FaultEvent
```

---

# Validation

Validation is a deterministic, side-effect-free function.

```
Validation(
    Candidate,
    Canonical,
    Config
)
→ ValidationReport
```

Observation := ObservationCheck(Graph, Candidate)

Validation collects objective facts only.

Validation performs no routing and no state mutation.

See:

- `05-validation-pipeline-r0.md`

---

# PolicyRouter

PolicyRouter interprets a ValidationReport according to Config.

```
PolicyRouter(
    ValidationReport,
    Config
)
→ Action
```

Possible actions are:

```
accept
reject
defer
retry
retry-penalty
abort
```

PolicyRouter performs interpretation only.

It performs neither validation nor state mutation.

---

# Kernel

Kernel is the sole component permitted to mutate authoritative state.

Kernel executes the Action returned by PolicyRouter.

Depending on the Action, Kernel may:

- Commit an Event
- Enqueue a Candidate into DeferredQueue
- Trigger a retry
- Trigger a retry with penalty
- Emit a FaultEvent

Kernel owns all runtime state transitions.

---

# Commit API

```
Commit(Event)
    ↓
Canonical'
    ↓
History++
```

If

```
Event.intent ∈ {
    memory-write
    recover
}
```

then

```
MemoryRef++
```

Commit is the only operation permitted to mutate Canonical.

---

# Replay API

```
Replay(Context)
    ↓
Projection
    ↓
Graph
    ↓
Summary
```
Replay は deterministic / reproducible / side-effect-free。

---

# Prompt Builder

```
Prompt :=
    BuildPrompt(
        Summary,
        Graph,
        MemoryRef,
        Config
    )

```

where

```
Context :=
    History
    Config
    MemoryRef
```

Prompt generation is deterministic.

---

# Backend

```
LLM :=
    CandidateGenerator(Prompt)
```

The backend is non-deterministic.

Its output is never authoritative until accepted by the Validation → PolicyRouter → Kernel pipeline.

---

# Deferred Processing

DeferredQueue is owned exclusively by the Kernel.

Candidates receiving the `defer` action are enqueued by the Kernel.

Wakeup is triggered only when Canonical advances.

```
Canonical Commit
        │
        ▼
Lamport Clock++
        │
        ▼
DeferredQueue Wakeup
        │
        ▼
Revalidation
```

Timeout-based wakeup is outside the R1 specification.

---

# Fault Processing

When Action is `abort`, Kernel emits a `FaultEvent`.

The FaultEvent ABI is defined in:

- `05-validation-pipeline-r0.md`

---

# Runtime Responsibility Summary

| Component | Responsibility |
|-----------|----------------|
| Validation | Collect objective facts |
| PolicyRouter | Interpret facts and select Action |
| Kernel | Execute runtime state transitions |
| Commit | Mutate Canonical |
| Replay | Derive runtime context |
| Prompt Builder | Construct deterministic prompts |
| Backend | Generate non-deterministic Candidates |
| DeferredQueue | Hold deferred Candidates until revalidation |