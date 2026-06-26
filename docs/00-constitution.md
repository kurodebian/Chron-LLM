# Agent Constitution

## 1. Ontology

The following concepts exist within this constitution.

- Canonical
- Evidence
- Candidate
- Derived
- Working
- External
- Commit

No assumption is made regarding their representation.

---

## 2. Axioms

### A1

Canonical is the sole authoritative state.

### A2

Only Commit may authoritatively mutate Canonical.

### A3

Evidence is authoritative.

### A4

Candidate is non-authoritative.

### A5

Derived is non-authoritative.

### A6

Working is non-authoritative.

### A7

External is outside the authoritative state.

---

## 3. Derived Invariants

The following properties follow from the axioms.

- Canonical authority is unique.
- No non-authoritative object may directly mutate Canonical.
- Evidence belongs to the authoritative state.
- Candidate, Derived, Working and External are not authoritative.

---

## 4. Conformance

A system conforms to this constitution iff all axioms hold.

Representations, algorithms and implementations are irrelevant to conformance.

---

## 5. Constitutional Scope

This constitution specifies only

- ontology
- authority
- invariants
- conformance

This constitution intentionally does not specify

- data structures
- algorithms
- execution model
- scheduling
- storage
- serialization
- transport
- validation
- implementation