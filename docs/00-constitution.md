# Agent Causality Constitution v1.0
(Baseline Constitution)

---

# Purpose

This Constitution defines the minimum constitutional principles governing authoritative causal state evolution.

It specifies constitutional responsibilities rather than implementation.

All implementation details remain outside the constitutional scope.

---

# Scope

This Constitution defines only:

* authoritative state
* constitutional invariants
* causal constraints

Representation, algorithms, processing order, validation,
storage, transport, synchronization, optimization,
and implementation details are intentionally unspecified.

Any implementation conforming to these constitutional constraints is valid.

---

## 1. Fundamental Principles

* Canonical is the sole authoritative state.
* Only Commit may mutate Canonical.
* Evidence consists of committed Events.
* Evidence is causally ordered.
* Derived is reproducible, deterministic, and non-authoritative.
* Derived SHALL NOT introduce authoritative information.
* Working is ephemeral and non-authoritative.
* External is non-authoritative.

---

## 2. Session

A Session consists of four constitutional state categories:

* Canonical
* Working
* Derived
* External

### Canonical

Authoritative state.

### Working

Ephemeral, non-authoritative state.

### Derived

A non-authoritative representation derived from Canonical.

Derived does not possess authority.

### External

Non-authoritative state outside Canonical.

---

## 3. Event

An Event possesses:

* identity
* payload
* metadata

Evidence consists of committed Events.

Evidence is causally ordered.

---

## 4. Candidate

A Candidate is a non-authoritative proposal.

Its representation is implementation-defined.

---

## 5. Commit

Only Commit may mutate any authoritative component of Canonical.

Commit incorporates Evidence into Canonical.

Commit establishes the next authoritative Canonical state.

Commit preserves all constitutional invariants.

The behavior of Commit is implementation-defined except where constrained by this Constitution.

---

## 6. Derivation

Derived is obtained by applying Derive to Canonical.

Derive is:

* deterministic
* side-effect-free

The derivation mechanism is implementation-defined.

---

## 7. Authoritative Causality

Authoritative state evolves only through Commit.

No operation other than Commit may directly mutate Canonical.

The ordering of non-authoritative processing is implementation-defined.

---

## 8. Constitutional Invariants

* Canonical is authoritative.
* Only Commit may mutate Canonical.
* Evidence consists of committed Events.
* Evidence is causally ordered.
* Candidate is not Canonical.
* Working is not Canonical.
* Derived is not Canonical.
* External is not Canonical.
* Rejected proposals preserve Canonical.
* Deferred proposals preserve Canonical.

---

## 9. Evolution

This Constitution intentionally specifies only the minimum constitutional constraints.

Future amendments SHALL preserve constitutional consistency.

No new constitutional principle SHALL be introduced unless existing principles cannot adequately express the required constitutional responsibility.
