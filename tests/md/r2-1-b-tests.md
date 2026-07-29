# Chron LLM R2.1-B Verification Specification

## Purpose
This module defines mock inference scenarios and executes a suite of backend ABI verification tests (D-Tier) for the `chron-llm` system. It validates execution flow, error handling, data immutability, deterministic replay capabilities, and provider abstraction independence using mocked dependencies.

**Package:** `chron-llm/r2-1-b`

## Public API

### `run-r2-1-b-verification`
Executes the full suite of D-Tier verification tests (D1–D6). Each test case clears the mock registry prior to execution and signals an error immediately if any invariant is violated.

*   **Parameters:** None.
*   **Return Value:** `t` upon successful completion; otherwise, signals a Common Lisp condition via `assert`.
*   **Side Effects:** Prints "D-Tier verification passed." to standard output on success.

## Internal Helpers

### `%make-test-observation`
Constructs an inference observation object with validated primitive data for testing purposes.

*   **Parameters (Keyword):**
    *   `raw-text`: String or nil.
    *   `prompt-text`: String.
    *   `usage-tokens`: List of token usage metrics.
    *   `token-count`: Integer.
    *   `finish-reason`: Symbol indicating termination status.
    *   `config`: Property list of configuration settings.
    *   `provider-metadata`: Property list of provider-specific data.
    *   `error-info`: Property list or nil describing errors.
*   **Return Value:** An instance of `inference-observation`.

### `%register-basic-success-scenario`
Registers a deterministic mock scenario representing a successful inference completion.

*   **Scenario ID:** `:mock-success-basic`
*   **Key Attributes:**
    *   Finish Reason: `:stop`
    *   Raw Text: `"mock-success-response"`
    *   Config Temperature: `0.0`
*   **Return Value:** The registered observation object.

### `%register-timeout-scenario`
Registers a deterministic mock scenario representing a provider timeout error.

*   **Scenario ID:** `:mock-openai-timeout`
*   **Key Attributes:**
    *   Finish Reason: `:timeout`
    *   Error Type: `:timeout`
    *   Raw Text: `nil`
*   **Return Value:** The registered observation object.

## Verification Test Cases (D-Tier)

The following invariants are verified by `run-r2-1-b-verification`. Each test invokes `execute-inference` with the mode `:mock`.

### D1: Single Attempt (Mock Success)
Verifies basic execution flow and data retrieval for a successful scenario.
*   **Setup:** Registers `:mock-success-basic`.
*   **Assertions:**
    *   Observation object is non-nil.
    *   Finish reason equals `:stop`.
    *   Raw text matches `"mock-success-response"`.

### D2: Error-as-Fact (Mock Error)
Verifies that errors are returned as structured data within the observation rather than signaling unhandled conditions.
*   **Setup:** Registers `:mock-openai-timeout`.
*   **Assertions:**
    *   Finish reason equals `:timeout`.
    *   Error info contains a non-nil message (`"Provider request timeout."`).

### D3: No Partial Mutation
Verifies that modifying configuration data retrieved from an observation does not affect the original stored state.
*   **Setup:** Registers `:mock-success-basic`.
*   **Procedure:** Retrieves config, modifies temperature in the returned list to `99.0`.
*   **Assertion:** Original observation config temperature remains `0.0`.

### D4: Observation Immutability
Verifies that provider metadata is immutable across multiple retrievals and external modifications.
*   **Setup:** Registers `:mock-success-basic`.
*   **Procedure:** Retrieves metadata twice (`metadata-a`, `metadata-b`), modifies model name in `metadata-a`.
*   **Assertions:**
    *   `metadata-b` retains original model `"mock-model"`.
    *   Observation's internal metadata retains original model `"mock-model"`.

### D5: Deterministic Replay (ID Matching)
Verifies that the same scenario ID produces identical results regardless of provider symbol or prompt context.
*   **Setup:** Registers `:mock-success-basic`.
*   **Procedure:** Executes inference twice with different providers (`:provider-a`, `:provider-b`) and prompts.
*   **Assertions:**
    *   Raw text is identical in both observations.
    *   Finish reason is identical in both observations.

### D6: Provider Abstraction Independence
Verifies that the mock execution ignores the specific structure or identity of the provider object passed to `execute-inference`.
*   **Setup:** Registers `:mock-success-basic`.
*   **Procedure:** Executes inference with a symbol (`:provider-one`) and an arbitrary list object as providers.
*   **Assertion:** Raw text is identical in both observations.