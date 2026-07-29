# Llama Engine Package Specification

## Overview
The `llama-engine` package provides a Common Lisp interface to an external C library (likely related to llama.cpp) for loading models, initializing contexts, and executing inference streams. It utilizes **CFFI** for foreign function interfaces.

## Public API
The following symbols are exported from the package:

*   `load-model`
*   `init-context`
*   `llama-run`
*   `*model*` (Global variable)
*   `*ctx*` (Global variable)

## Global State
Two global variables manage state within the package. They are initialized to `nil`.

| Symbol | Type | Description |
| :--- | :--- | :--- |
| `*model*` | Pointer / Nil | Stores the pointer to the currently loaded model instance. |
| `*ctx*` | Pointer / Nil | Stores the pointer to the currently initialized context instance. |

## Functions

### load-model
Loads a model from a specified file path and updates the global state.

*   **Signature:** `(load-model path)`
*   **Parameters:**
    *   `path`: String representing the filesystem path to the model file.
*   **Return Value:** Pointer to the loaded model (C pointer).
*   **Side Effects:** Sets the package variable `*model*` to the returned pointer.

### init-context
Initializes a context using the currently loaded global model (`*model*`).

*   **Signature:** `(init-context)`
*   **Parameters:** None.
*   **Return Value:** Pointer to the initialized context (C pointer).
*   **Side Effects:** Sets the package variable `*ctx*` to the returned pointer.
*   **Dependencies:** Relies on `*model*` being non-nil and valid prior to execution.

### llama-run
Executes a streaming inference run using provided model, context, and prompt arguments. Note that this function accepts explicit pointers rather than relying solely on global state.

*   **Signature:** `(llama-run model ctx prompt)`
*   **Parameters:**
    *   `model`: Pointer to the loaded model.
    *   `ctx`: Pointer to the initialized context.
    *   `prompt`: String containing the input text.
*   **Return Value:** Void (`:void`).

## CFFI Bindings (Internal)
The package defines internal wrappers for the following C functions:

1.  `%llama-model-load-simple`
    *   Maps to: `"llama_model_load_simple"`
    *   Args: `(path :string)`
    *   Returns: `:pointer`
2.  `%llama-init-context-safe`
    *   Maps to: `"llama_init_context_safe"`
    *   Args: `(model :pointer)`
    *   Returns: `:pointer`
3.  `%llama-run-stream-simple`
    *   Maps to: `"llama_run_stream_simple"`
    *   Args: `(model :pointer)`, `(ctx :pointer)`, `(prompt :string)`
    *   Returns: `:void`