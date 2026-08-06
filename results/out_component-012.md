### 1. Optimal Merge Plan
- **Decision:** `KEEP_BOTH` (No Merge)
- **Rationale:** The artifacts demonstrate a strict **Separation of Concerns**. 
  - `09-runtime-scheduling.spec` manages the **Orchestration Layer**: queue topology, scheduling policies, retry mechanics, and fault isolation boundaries.
  - `10-tool-execution.spec` manages the **Tool Interaction Layer**: event lifecycle, state transition rules, and causal consistency enforcement.
- **Boundary Definition:** Maintain as independent modules. The integration boundary should explicitly define how `Execution` state transitions from the scheduling layer trigger `ToolEvent` payloads in the execution layer. Overlapping `CanonicalState` invariants reflect shared architectural principles, not functional redundancy.

### 2. Architectural Consistency & Invariant Verification
- **Schema Alignment & Type Mapping:**
  - `Execution.causalOrder` (LamportClock) in Doc 09 aligns functionally with `Context.causal_id` (ID) in Doc 10. Both enforce causal ordering but use divergent naming/type conventions. **Risk:** Potential mapping friction during inter-module communication.
  - `Execution.state` (`Working | Faulted`) and `State` (`{ canonical, dialogue }`) operate at different abstraction layers. No direct type conflict exists, but explicit bridging logic is required when passing execution context to tool handlers.
- **SOT Consistency & Invariant Cross-Check:**
  - **Determinism & Immutability:** `INV Schedule == Deterministic(CanonicalState)` (09) and `INV(determinism)` (10) are fully aligned. Both enforce deterministic outcomes derived from canonical state.
  - **Retry Semantics:** `INV Retry -> !Mutate(CanonicalState)` (09) perfectly matches `INV(retry_no_mutation)` and `INV(no_bypass)` (10). Both strictly prohibit canonical state mutation during retry or non-COMMIT events.
  - **Fault Isolation:** `INV FaultIsolation -> !Affect(NormalDialogueReplay)` (09) is reinforced by `INV(isolation_fail)` (10), which ensures `dialogue` state remains unchanged on `TIMEOUT`/`ABORT`. Consistency is verified.
- **Conflict Analysis:** Zero contradictions detected. Invariants are complementary and enforce a consistent "commit-on-success, isolate-on-failure" architecture.

### 3. Actionable Roadmap
- **Automation & Tooling:**
  1. Deploy a cross-module invariant validator (e.g., AST-based spec analyzer or property-based testing framework) to automatically verify `CanonicalState` immutability across both files during CI.
  2. Generate interface stubs from `09-runtime-scheduling.spec` to `10-tool-execution.spec` to enforce type-safe handoffs and catch signature drift.
- **Verification & Testing:**
  1. Develop integration test suites simulating the full lifecycle: `Schedule` → `retry-with-penalty` → `apply(ToolEvent)` → `INV` verification.
  2. Implement mutation testing to ensure `INV(no_bypass)` and `INV(retry_no_mutation)` correctly block unauthorized state transitions and enforce strict commit semantics.
- **Code/Spec Integration Steps:**
  1. **Standardize Causal Identifiers:** Extract `causalOrder`/`causal_id` into a shared `types.spec` module to unify naming, typing, and serialization.
  2. **Define Explicit Contracts:** Document the exact payload transformation from `Execution` (Doc 09) to `ToolEvent` + `Context` (Doc 10) in a central API/contract specification.
  3. **CI Pipeline Enforcement:** Configure linting rules to flag any new invariant that contradicts `!Mutate(CanonicalState)` or `deterministic_outcome` across the component boundary.
  4. **Refactor Shared Concepts:** Move overlapping invariant definitions (`Deterministic`, `!Mutate`, `Isolation`) to a common `architectural-principles.spec` to reduce duplication while preserving module independence.