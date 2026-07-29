# R2.2-E Verification Suite Specification

**Package:** `chron-llm/r2-2-e-tests`  
**Source File:** `tests/r2-2-e-tests.lisp`

## Overview
This module defines a verification suite for the **E-Tier (Evaluation Tier)** of the Chron LLM system (R2.2-E). It validates core behavioral invariants regarding determinism, purity, policy enforcement, safety defaults, and operational derivation consistency using the `evaluate-observation` and `derive-ops` functions imported from `chron-llm/r2-2-e`.

## Public API

### `run-r2-2-e-verification`
Executes the full suite of E-Tier verification tests.

*   **Parameters:** None.
*   **Return Value:** 
    *   Returns `T` upon successful completion of all assertions.
    *   Signals an assertion error if any invariant is violated.
*   **Side Effects:** Prints "E-Tier verification passed." to standard output on success.

## Verification Invariants (Test Cases)

The suite validates five specific properties of the evaluation logic:

### E1: Deterministic Decision
Ensures that given identical inputs, the evaluator produces consistent decision types.

*   **Inputs:** 
    *   `world-state`: Fixed state vector.
    *   `observation`: A successful stop observation (`%make-stop-observation`).
    *   `policy`: Empty list.
*   **Procedure:** Invoke `evaluate-observation` twice with identical arguments.
*   **Invariant:** The `inference-decision-type` of both resulting decisions must be `EQ`.

### E2: No Side Effects (Purity)
Ensures the evaluation process does not mutate the provided world state.

*   **Inputs:** 
    *   `world-state`: A list structure containing mutable data (`(:counter 10)`).
    *   `observation`: A successful stop observation.
    *   `policy`: `NIL`.
*   **Procedure:** Capture a copy of the world state, invoke `evaluate-observation`, and compare.
*   **Invariant:** The `world-state` after evaluation must be `EQUAL` to its pre-evaluation copy.

### E3: Error-as-Fact Handling (Policy Enforcement)
Ensures specific error conditions trigger defined policy actions rather than generic failures.

*   **Inputs:** 
    *   `policy`: A rule mapping `:timeout` errors to a `:retry` action with parameters.
    *   `observation`: A timeout observation (`%make-timeout-observation`).
    *   `world-state`: `NIL`.
*   **Procedure:** Invoke `evaluate-observation`.
*   **Invariant:** The resulting decision type must be `EQ` to `:retry`.

### E4: Policy Safety (Fail-Safe Default)
Ensures unknown errors result in a safe abort state when no specific policy exists.

*   **Inputs:** 
    *   `policy`: `NIL`.
    *   `observation`: An observation with an unknown error type (`:unknown-error`).
    *   `world-state`: `NIL`.
*   **Procedure:** Invoke `evaluate-observation`.
*   **Invariant:** The resulting decision type must be `EQ` to `:abort`.

### E5: Replay Consistency (Derivation Stability)
Ensures that deriving operations from a decision is deterministic.

*   **Inputs:** 
    *   `decision`: A decision object derived from a successful stop observation with no policy.
*   **Procedure:** Invoke `derive-ops` twice on the same decision object.
*   **Invariant:** The resulting operation lists must be `EQUAL`.

## Internal Helpers

### `%make-stop-observation`
Constructs a canonical "success" observation for testing.
*   **Key Attributes:** 
    *   `finish-reason`: `:stop`
    *   `raw-text`: `"ok"`
    *   `error-info`: `NIL`

### `%make-timeout-observation`
Constructs a canonical "timeout" error observation for testing.
*   **Key Attributes:** 
    *   `finish-reason`: `:timeout`
    *   `raw-text`: `NIL`
    *   `error-info`: Contains type `:timeout`.