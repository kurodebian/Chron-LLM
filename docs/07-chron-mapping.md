# Chron-OS ↔ Chron-LLM Mapping

**Status:** Informative

This document describes the conceptual correspondence between
Chron-LLM runtime abstractions and Chron-OS kernel concepts.

It is descriptive only and introduces no normative requirements.

---

| Chron-LLM | Chron-OS |
|-----------|----------|
| Candidate | proposalIR |
| Validation | Δ0 Validator |
| ValidationReport | Δ0 Validation Report |
| PolicyRouter | Δ0 Resolution Policy |
| Kernel | Runtime Kernel |
| Commit | Commit |
| Event | WAL Entry |
| History | WAL |
| Canonical | Canonical State |
| DeferredQueue | Deferred Proposal Queue |
| Replay | replay(snapshot) |
| Derived | snapshot / derived projection |
| Session | kernel-state |
| Context | replay input |
| MemoryRef | Runtime Reference Store |
| Config | Runtime Configuration |
| FaultEvent | Fault Event |
| External | external store |

---

## Notes

- **Candidate** is the Chron-LLM representation of Chron-OS `proposalIR`.
- **Validation** corresponds to the deterministic Δ0 validation stage.
- **ValidationReport** is the structured output produced by Validation before any policy decision.
- **PolicyRouter** corresponds to the deterministic policy layer that resolves a `ValidationReport` into a runtime `Action`.
- **Kernel** is the only component authorized to mutate Canonical state.
- **History** is represented by the Chron-OS Write-Ahead Log (WAL).
- **Replay** deterministically derives runtime context from Canonical history.
- **Derived** represents deterministic projections reconstructed from Canonical.
- This mapping is conceptual only and does not imply identical implementation details.