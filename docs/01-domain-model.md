# Domain Model

## 1. Primitive Types

Implementation-defined primitive types.

---

## 2. Event

Defines the concrete Event representation.

---

## 3. Evidence

Defines how Evidence is represented.

Examples may include:

- append-only sequence
- WAL
- DAG
- graph

---

## 4. Candidate

Concrete representation of a proposal.

Examples:

- OperationIR
- Command
- Plan
- Proof

---

## 5. Canonical

Defines the concrete authoritative state.

---

## 6. Working

Defines transient state.

---

## 7. Derived

Defines non-authoritative derived state.

---

## 8. External

Defines external resources.

---

## 9. Ownership

Defines ownership and lifecycle of each type.

---

## 10. Relationships

Defines structural relationships among domain objects.