# Open Questions (Design Backlog)

**Status:** Backlog

This document tracks architectural questions that remain intentionally unspecified
or intentionally deferred to future revisions.

Nothing in this document is normative.

---

# Domain

## Event Identity

- UUID
- Sequential ID
- Lamport Clock
- Composite Identifier

---

## Event Metadata

- timestamp
- sequence
- lamport
- causal-parent
- implementation-specific metadata

---

## Candidate Representation

- OperationIR versioning
- serialization format
- compatibility strategy

---

## Evidence Representation

- committed Event encoding
- storage format
- replay compatibility

---

## Versioning Strategy

- Event ABI
- OperationIR
- ValidationReport ABI
- FaultEvent ABI

---

# Runtime

## Commit

- idempotency semantics
- atomicity guarantees

---

## Replay

Replay scope:

- History only
- History + Config
- History + Config + MemoryRef

---

## Configuration

Config schema:

- routing policy
- retry strategy
- penalty strategy
- detector thresholds
- logging
- metrics
- telemetry

---

## External Consistency

- LTM synchronization
- external storage update semantics

---

## Memory

MemoryRef architecture:

- lifecycle
- cache strategy
- persistence model

---

## Scheduling

- Candidate scheduling
- DeferredQueue ordering
- fairness policy
- starvation prevention

---

## Tool Execution

- synchronous vs asynchronous
- retry semantics
- failure propagation
- timeout policy

---

## Recovery

- restart behavior
- crash recovery
- replay guarantees

---

# Future Extensions

## Distributed Runtime

- Multi-agent causality
- Distributed sessions
- Remote Commit
- Shared Canonical
- Federated Memory
- Cross-agent replay

---

## Causal Models

- Causal DAG
- Vector Clocks
- Hybrid Logical Clocks
- Tool-event causal ordering
- Cross-session evidence linking

---

## Validation Extensions

- additional detectors
- additional invariant categories
- pluggable PolicyRouter implementations
- configurable routing strategies

---

## Runtime Extensions

- multiple Backend implementations
- distributed DeferredQueue
- parallel replay
- streaming Candidate generation