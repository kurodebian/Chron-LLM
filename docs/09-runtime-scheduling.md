# Chron-LLM Runtime Scheduling Specification

**Status:** Normative
**Version:** R1

---

# Purpose

Define deterministic runtime scheduling.

---

# Queues

## IngressQueue

Receives external Events.

---

## ReadyQueue

Execution queue.

Ordering:

- Lamport Clock
- FIFO within identical Lamport values

---

## IsolatedQueue

Contains fault-isolated executions.

Normal dialogue execution MUST NOT depend on this queue.

---

# Retry Policy

## retry

Maximum retries


3


---

## retry-with-penalty

Maximum retries


2


Penalty


temperature += 0.2

top-p -= 0.1


Penalty applies only to Working state.

Canonical remains unchanged.

---

## abort


FaultEvent

↓

Terminate runtime branch


---

# Invariants

Scheduling is deterministic.

Ordering depends only on Canonical.