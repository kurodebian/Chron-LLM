# Specification: chron-r2-0-a

## Overview
This module defines a test suite and invariant verification system for the `chron-r2-0-a` package. It validates behaviors related to memory storage, causal graph topology, context projection, and prefill state hashing within a deterministic environment.

**Package:** `chron-r2-0-a`

## Public API

### Entry Point
The primary entry point executes all defined invariants sequentially.

#### `run-r2-0-a-tests`
Executes the suite of test functions (`t1` through `t6`). Returns `T` if all assertions pass; signals an error otherwise.

```lisp
(defun run-r2-0-a-tests () ...)
```

## Internal Utilities

### `%assert`
A helper function used to enforce invariants within the tests.

*   **Parameters:**
    *   `condition`: Boolean expression.
    *   `description`: String describing the invariant.
*   **Behavior:**
    *   If `condition` is false, signals an error with message `"R2.0-A invariant failed: ~A"`.
    *   Returns `T` if `condition` is true.

### `%fixture`
Constructs a standard test environment consisting of a memory store and a causal graph.

*   **Parameters:**
    *   `with-evaluation`: Boolean (default `t`). Determines if an evaluation node is included in the fixture.
*   **Returns:** Multiple values: `(graph, store)`.
*   **Setup Logic:**
    1.  Creates a memory store and causal graph.
    2.  Adds Node `"s"` (System fact).
    3.  Adds Node `"p"` (User fact/Prompt).
    4.  Adds Edge `"s" -> "p"` (Type: `:causal`).
    5.  If `with-evaluation` is true:
        *   Adds Node `"e"` (Evaluation/Helpful).
        *   Adds Edge `"p" -> "e"` (Type: `:eval`).

## Verified Invariants & Behaviors

The following behaviors are enforced by the test functions (`t1`–`t6`) within this module. These represent the expected contract of the underlying system components.

### 1. Memory Determinism
*   **Source:** `t1-memory-determinism`
*   **Invariant:** Storing identical content must result in payloads with identical reference hashes.
*   **Invariant:** Stored payloads are immutable; retrieval (`load-payload`) returns the exact original string.

### 2. Graph Replay and Causal Order
*   **Source:** `t2-graph-replay`
*   **Invariant:** The causal subgraph of a node must reflect its ancestry in correct order (e.g., for prompt `"p"`, system `"s"` precedes it).
*   **Invariant:** Subgraph generation is deterministic; repeated calls with the same inputs yield equal results.

### 3. View Separation
*   **Source:** `t3-view-separation`
*   **Invariant:** Evaluation nodes (type `:eval`) are excluded from standard causal views of a prompt node unless explicitly requested.

### 4. Context Projection
*   **Source:** `t4-context-projection`
*   **Behavior:** When projecting context with evaluations included (`:include-evaluations t`):
    *   Causal content is preserved in order (System fact, then User fact).
    *   Evaluation feedbacks are correctly associated with their respective nodes.

### 5. Prefill Hash Stability
*   **Source:** `t5-prefill-hash-stability`
*   **Invariant:** Building a prefill state from identical graph/store inputs must produce an identical hash string every time.

### 6. Evaluation Independence
*   **Source:** `t6-evaluation-independence`
*   **Invariant:** By default (without explicit inclusion flags), the presence or absence of evaluation nodes in the graph does not affect the resulting prefill state hash. The base policy ignores eval nodes for hashing purposes.