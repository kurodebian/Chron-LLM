# Chron R2.0-A Specification

## Purpose
This module defines a deterministic test suite for validating core invariants of a causal world management system. It verifies behaviors related to world creation, forking, metadata isolation, graph sharing, commit visibility, replay determinism, and registry lifecycle operations.

## Package & Scope
- **Package:** `chron-r2-0-a`
- **Scope:** Internal test harness and invariant assertions. Relies on external system components (e.g., `make-world`, `fork-world`, `kernel-commit-world!`, `register-world`) assumed to be available in the environment.

## Core Utilities

### `%b-assert`
Enforces runtime conditions during testing. Signals an error if a condition fails; otherwise returns success.
- **Signature:** `(condition description)`
- **Parameters:**
  - `condition`: Boolean expression representing the invariant to check.
  - `description`: String describing the failing rule for error reporting.
- **Return Value:** `t` on success.
- **Behavior:** If `condition` is false, signals an error with format `"R2.0-B invariant failed: ~A"`.

### `%b-fixture`
Initializes a consistent test environment containing shared causal structures and registry state.
- **Signature:** `()`
- **Return Values (Multiple):** `graph`, `store`, `policy`, `registry`
- **Setup Details:**
  - Creates an in-memory store and causal graph.
  - Defines two nodes: `"root"` (system payload) and `"head"` (prompt payload).
  - Establishes a causal edge from `"root"` to `"head"`.
  - Initializes default policy `(:include-evaluations nil)` and a world registry bound to the graph/store.

## Public API: Test Functions
Each function takes no arguments, executes scenario-specific operations using `%b-fixture`, asserts invariants via `%b-assert`, and returns `t` on success. Failure signals an error halting execution.

| Function | Purpose | Key Operations Verified |
|----------|---------|--------------------------|
| `b1-world-creation` | World identity uniqueness | Unique IDs per world; duplicate ID registration errors (IDs never reused). |
| `b2-world-fork` | Forking semantics | Child inherits parent's root/head nodes; registry records correct ancestry. |
| `b3-root-stability` | Root immutability | Committing new nodes does not alter the world's root node. |
| `b4-head-independence` | Head isolation across forks | Commits in a child world do not mutate the parent's head node. |
| `b5-projection-isolation` | Policy encapsulation | Worlds with different projection policies maintain distinct policy states. |
| `b6-metadata-cow` | Metadata copy-on-write | Modifying child metadata does not affect parent metadata (structural sharing/COW). |
| `b7-graph-sharing` | Infrastructure sharing | Parent and child worlds share identical graph and memory store references (`eq`). |
| `b8-replay-independence` | Deterministic replay | Replay output depends only on constitutional input; session/metadata variations do not affect equality. |
| `b9-world-isolation` | Cross-world mutation safety | Metadata changes in one world do not leak to or mutate another world's state. |
| `b10-commit-visibility` | Commit ordering & visibility | Committed nodes are immediately present in the graph and update the world's head node. |
| `b11-registry-persistence` | Registry lifecycle rules | Identity, active state, ancestry, and listing order persist; archived worlds cannot be reactivated as active. |

## System Invariants & Behavioral Rules
Derived directly from test assertions:

### World Lifecycle & Identity
- Every world instance receives a unique identifier.
- World IDs are never reused after deletion or archival.
- Registry operations preserve object identity (`eq`) across lookups and activations.

### Forking & Lineage
- Forked worlds inherit the parent's root and head node references.
- The registry maintains an explicit ancestry map linking child world IDs to parent world IDs.
- Parent and child worlds share underlying graph and memory store structures but maintain independent mutable state (head, metadata).

### Immutability & Isolation
- **Root Node:** Immutable across all commits within a world's lifetime.
- **Head Node:** Independent per world; mutations in one branch do not affect others.
- **Metadata:** Implements copy-on-write semantics; modifications are local to the target world.
- **Projection Policy:** Encapsulated per world instance; does not leak between worlds with differing configurations.

### Commit & Visibility
- `kernel-commit-world!` atomically updates the causal graph and advances the committing world's head node.
- Committed nodes are immediately queryable via the shared graph reference.

### Replay Determinism
- World replay is a pure function of constitutional inputs; auxiliary metadata (e.g., session IDs) does not influence output equality.

### Registry Rules
- `list-worlds` returns worlds in a deterministic order.
- Archived worlds remain retrievable but cannot be set as the active world.
- Active world state persists across registry operations until explicitly changed or archived.

## Execution Flow
1. **Test Runner:** `run-r2-0-b-tests` iterates sequentially over the defined test list (`b1` through `b11`).
2. **Per-Test Lifecycle:**
   - Invoke `%b-fixture` to obtain fresh graph/store/registry state.
   - Construct worlds and perform operations (fork, commit, metadata update, registry actions).
   - Validate expected outcomes using `%b-assert`.
3. **Termination:** Returns `t` if all tests pass; halts with an error message identifying the first failed invariant otherwise.