# Open Questions (Design Backlog)

## Domain-Level
- Event identity semantics (UUID / seq / lamport / composite-id)
- Metadata schema (timestamp, seq, lamport, causal-parent?)
- Versioning strategy for Event / OperationIR

## Runtime-Level
- Validation policy (pure vs contextual)
- Commit idempotency semantics
- Commit atomicity guarantees
- Replay scope (History only vs History+Config+MemoryRef)
- External consistency model (LTM update semantics)

## Future Extensions
- Multi-agent causality
- Distributed sessions
- Vector clocks / hybrid logical clocks
- Tool-event causal ordering
- Cross-session evidence linking
