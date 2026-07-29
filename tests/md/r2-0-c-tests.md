# Chron R2.0-C Verification Specification

## Overview
This module defines a deterministic test suite verifying core behavioral guarantees of the Chron R2.0-C system. It validates immutability, determinism, ancestry accuracy, diffing semantics, and value-based equality for world and registry observations.

## Internal Utilities

### `%c-assert`
- **Purpose:** Assertion helper used throughout the test suite.
- **Parameters:**
  - `condition`: Boolean expression to evaluate.
  - `description`: String describing the assertion requirement.
- **Behavior:** Signals an error with a formatted message if `condition` is false; otherwise returns `t`.

## Test Fixture

### `%c-fixture`
- **Purpose:** Initializes a standard, isolated environment for verification tests.
- **Returns:** Multiple values: `(graph store registry)`
- **Setup Details:**
  - Creates an in-memory store and causal graph.
  - Instantiates two nodes: `"root"` (system payload) and `"head"` (prompt payload).
  - Adds both nodes to the graph and creates a causal edge from `"root"` → `"head"`.
  - Constructs a world registry bound to the graph and store.

## Verification Tests (Public API)

Each test function returns `t` on success or signals an error via `%c-assert` on failure.

### `d1-world-non-mutation`
- **Purpose:** Ensures describing a world does not mutate its internal state.
- **Setup:** Creates a world with projection policy `(:include-evaluations nil)` and metadata `(:label "stable")`.
- **Assertions:**
  - `describe-world` returns a valid world observation (`world-observation-p`).
  - World attributes (id, root/head nodes, projection policy, metadata, lifecycle) remain identical before and after description.
  - Observation exposes the expected schema version (`+observation-schema-version+`).

### `d2-registry-non-mutation`
- **Purpose:** Ensures describing a registry does not mutate its internal state.
- **Setup:** Registers two worlds ("first", "second"), sets active world to "second", archives "first".
- **Assertions:**
  - `describe-registry` returns a valid registry observation (`registry-observation-p`).
  - Registry state (world list, active world, ancestry structure) remains identical before and after description.

### `d3-deterministic-observation`
- **Purpose:** Verifies that observations are deterministic across repeated calls.
- **Assertions:**
  - Two consecutive `describe-world` calls on the same world yield identical world IDs.
  - Two consecutive `describe-registry` calls yield identical lists of registered world IDs.

### `d4-accurate-ancestry`
- **Purpose:** Validates that ancestry reporting accurately reflects registration relationships.
- **Setup:** Registers "parent" and "child" worlds with an explicit parent-child link.
- **Assertions on `describe-ancestry`:**
  - Returns a valid ancestry observation (`ancestry-observation-p`).
  - Reports correct child world ID ("child").
  - Reports correct parent world ID ("parent").
  - Ancestry path matches the runtime edge: `("child" . "parent")`.

### `d5-deterministic-difference`
- **Purpose:** Verifies diff observations are deterministic and correctly detect changes.
- **Assertions on `describe-diff`:**
  - Returns a valid diff observation (`diff-observation-p`).
  - Diffing identical world observations reports no change (`changed-p` = nil) and no changed fields.
  - Repeated diffs of the same inputs yield identical results (deterministic).
  - Diffing different observation kinds (world vs registry) correctly detects a difference (`changed-p` = t).

### `d6-representation-independence`
- **Purpose:** Ensures equivalent world configurations produce semantically equivalent observations regardless of internal representation.
- **Setup:** Creates two distinct world instances with identical parameters ("same").
- **Assertions:**
  - Both worlds yield observations with matching world IDs.
  - Both observations report the same root node ID, confirming semantic consistency.

### `d7-value-object-equality`
- **Purpose:** Validates that observation objects support content-based (value) equality rather than identity comparison.
- **Setup:** Same as `d6-representation-independence`.
- **Assertions:**
  - Observations from equivalent worlds are considered equal via either standard `equal` or the domain-specific `world-observation-equal` predicate, symmetrically in both directions.

## Test Runner

### `run-r2-0-c-tests`
- **Purpose:** Executes the complete verification suite sequentially.
- **Control Flow:** Iterates over all test function symbols (`d1` through `d7`), invokes each via `funcall`, and asserts successful completion (non-nil return). Returns `t` upon full execution.

## System Invariants & Guarantees
Derived from the assertion suite, the following invariants are enforced:

- **Immutability:** Observation generation (`describe-world`, `describe-registry`) is side-effect free with respect to the described entities.
- **Determinism:** Observations and diffs are purely functional; identical inputs always yield identical outputs.
- **Schema Compliance:** World observations expose a defined schema version constant.
- **Ancestry Accuracy:** Ancestry paths strictly reflect explicit parent-child registration relationships.
- **Diff Semantics:** Identical observations produce empty diffs; structurally different observation types are flagged as changed.
- **Value Semantics:** Observations behave as value objects, comparable by content rather than memory identity.