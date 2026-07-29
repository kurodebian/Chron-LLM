# Chron LLM R2.3-S Test Suite Specification

## Overview
This module defines a verification suite (`chron-llm/r2-3-s-tests`) for the core `chron-llm/r2-3-s` system. Its purpose is to validate critical invariants regarding state immutability, structural sharing (Write-Ahead Log behavior), causal lineage, and state transition logic via automated assertions.

## Package Definition
*   **Name:** `chron-llm/r2-3-s-tests`
*   **Usage:** Uses Common Lisp (`cl`).
*   **Imports from `chron-llm/r2-3-s`:**
    *   World State: `make-world-state`, `copy-world-state`, accessors for causal-id, parent-id, status, retry-count, history, context.
    *   Actions: `make-physical-action`, accessors for type and payload.
    *   Core Logic: `scheduler-step`.
*   **Exports:**
    *   `run-r2-3-s-verification`

## Public API

### Function: `run-r2-3-s-verification`
Executes the S-Tier verification suite. It performs a sequence of tests against a genesis world state and signals an error if any assertion fails.

*   **Parameters:** None.
*   **Return Value:** `T` (if all assertions pass).
*   **Side Effects:** Prints "S-Tier verification passed." to standard output upon success.

## Internal Helpers

### Function: `%make-genesis-world`
Constructs the initial zero-point world state used as a baseline for tests.

*   **Parameters:** None.
*   **Return Value:** A `world-state` instance with the following properties:
    *   `causal-id`: `"genesis"`
    *   `parent-id`: `nil`
    *   `status`: `:running`
    *   `retry-count`: `0`
    *   `history`: `nil`
    *   `context`: `'(:phase :r2-3-s :origin :genesis)`

## Verification Invariants (Control Flow)

The verification suite executes four distinct checks (S1–S4). Each check creates a fresh genesis world and invokes `scheduler-step`.

### S1: Immutable State
Verifies that the scheduler is side-effect free regarding the input state.

*   **Procedure:**
    1. Create a genesis world (`world`).
    2. Deep copy it (`before`).
    3. Invoke `(scheduler-step world '(:op :retry) "child")`.
    4. Ignore returned values.
*   **Invariant:** The original `world` must remain structurally equal to the pre-execution copy `before`.
    *   Assertion: `(equalp world before)`

### S2: WAL Append & Structural Sharing
Verifies that history updates utilize structural sharing (O(1) append).

*   **Procedure:**
    1. Create a genesis world (`world`).
    2. Capture the initial history pointer (`old-history`, which is `nil`).
    3. Invoke `(scheduler-step world '(:op :retry ...) "child")`.
*   **Invariants:**
    *   The new world's history head must equal the operation list passed to the scheduler.
        *   Assertion: `(equal ops (first (world-state-history new-world)))`
    *   The tail of the new history list must be physically identical (`eq`) to the old history pointer, confirming structural sharing rather than deep copying.
        *   Assertion: `(eq old-history (cdr (world-state-history new-world)))`

### S3: Causal-ID Branching
Verifies that causal lineage is correctly established during state transitions.

*   **Procedure:**
    1. Create a genesis world (`world`).
    2. Invoke `(scheduler-step world '(:op :retry) "child-id")`.
*   **Invariants:**
    *   The new world's `causal-id` must match the ID provided to the scheduler step.
        *   Assertion: `(string= "child-id" (world-state-causal-id new-world))`
    *   The new world's `parent-id` must match the causal ID of the source world (`"genesis"`).
        *   Assertion: `(string= "genesis" (world-state-parent-id new-world))`

### S4: State Transition & Physical Action
Verifies specific logic for retry and abort operations, including state mutations in the returned object and generated physical actions.

*   **Procedure A (Retry):**
    1. Invoke `(scheduler-step world '(:op :retry) "c1")`.
    *   Returns `w-retry` (world) and `a-retry` (action).
    *   **Invariants:**
        *   Retry count increments to 1: `(= 1 (world-state-retry-count w-retry))`
        *   Action type is invoke-api: `(eq :invoke-api (physical-action-type a-retry))`

*   **Procedure B (Abort):**
    1. Invoke `(scheduler-step world '(:op :abort) "c2")`.
    *   Returns `w-abort` (world) and `a-abort` (action).
    *   **Invariants:**
        *   World status becomes halted: `(eq :halted (world-state-status w-abort))`
        *   Action type is halt: `(eq :halt (physical-action-type a-abort))`