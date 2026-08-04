# Structured Analysis Report

## 1. Optimal Merge Plan

Based on the provided artifact relationships and architectural constraints, a **`KEEP_BOTH`** strategy is mandated across all component pairs. Merging would violate explicit invariants, conflate abstraction layers, and break the Delta3 Kernel's separation of concerns. The optimal plan groups artifacts by architectural tier and defines cross-referencing protocols instead of file consolidation.

| Architectural Tier | Artifacts | Merge Decision | Rationale & Integration Strategy |
|:---|:---|:---|:---|
| **Core State & Orchestration** | `chron-llm-kernel.spec`, `chron-llm-runtime.spec` | `KEEP_BOTH` | Kernel is the sole state mutator (`INV: Kernel -> Sole State Mutator`). Runtime orchestrates but must remain LLM/Graph-agnostic (`INV: Runtime.knows(LLM) == FALSE`). **Strategy:** Runtime imports Kernel API definitions. No shared mutable state. |
| **Semantic IR & Backend HAL** | `chron-llm.spec`, `ffi-bindings.spec`, `ffi-bindings-mock.spec` | `KEEP_BOTH` | `chron-llm.spec` defines logical Events/Headers/Nodes. FFI specs handle physical memory/layout and C/llama.cpp mapping. Mock is required for deterministic testing (`INV: mock_compat`). **Strategy:** FFI specs auto-generate bindings from `chron-llm.spec` type definitions. Mock acts as a drop-in replacement for unit testing. |
| **Execution Policy & Session Layer** | `generate.spec`, `chat-loop.spec`, `chron-llm-r0-session-execution-layer-spec-v1.0.spec` | `KEEP_BOTH` | R0/R1 spec is the architectural contract defining layer boundaries and `RuntimeCommand` ABI. `chat-loop.spec` implements R0 session flow. `generate.spec` implements agent policy/safety. **Strategy:** R0/R1 spec acts as the master interface contract. `chat-loop` and `generate` implement against it via explicit module imports. |

**Integration Protocol:**
- Replace file merges with **module-level imports** and **interface contracts**.
- Define a shared `DomainTypes` schema for cross-layer primitives (`Role`, `ID`, `Clock`, `Status`).
- Enforce `RuntimeCommand` ABI as the sole communication channel between R0/R1 layers and the Kernel.

---

## 2. Architectural Consistency & Invariant Verification

### Schema Alignment
- **State Types:** `KernelState` (Kernel) and `KernelState` (Runtime) are structurally aligned but scoped differently. Runtime wraps Kernel state for API exposure. Consistent.
- **History/Events:** Kernel uses `HistoryEntry` (WAL-backed, clocked). R0/Chat uses `HistoryEvent` (session-scoped, role-based). FFI uses `event` struct. Consistent via explicit DTO projection (`%history->dto` in Kernel spec).
- **Context Objects:** Kernel's `ContextObject` (system prompt, history, metadata) is distinct from `chron-llm.spec`'s `Context` (LLM inference state: `model`, `ctx`, `n-past`). No conflict; different abstraction layers.

### Single Source of Truth (SOT) Consistency
- **Kernel as SOT:** `INV: Kernel == SingleSourceOfTruth` and `INV: Kernel -> Sole State Mutator` are upheld. All state mutations flow through `kernel-commit-event` -> `stage-event` -> `commit-staged`.
- **Runtime Isolation:** Runtime accesses Kernel exclusively via API. It holds no direct references to WAL/Graph/History. Consistent.
- **FFI Statelessness:** `INV: stateless` ensures FFI layer holds only native pointers. No inference logic or state persistence. Consistent.
- **Session/Trace Scope:** `chat-loop.spec` and `generate.spec` operate on ephemeral session state. They do not conflict with Kernel SOT as they are transient execution contexts.

### Type Mismatches & Resolution
| Mismatch | Locations | Risk | Resolution |
|:---|:---|:---|:---|
| `Symbol` vs `Role` vs `Status` | Kernel (`:user-message`), R0 (`'user' | 'assistant'`), FFI (`symbol`) | Cross-layer serialization errors | Define unified `Role` enum in shared schema. Map Kernel symbols to R0 roles via adapter. |
| `Integer` vs `ID` vs `WALPos` | Kernel (`world_id: Integer`), R1 (`ID`, `Pos`), FFI (`int32`) | Pointer/offset misalignment | Enforce `int64` for all positional/clock types in FFI. Cast explicitly at layer boundaries. |
| `Any?` / `Any` / `PropertyList` | Kernel (`metadata: Any?`), `chron-llm.spec` (`payload: PropertyList`) | Type safety degradation | Replace `Any` with strict `Map<String, Value>` or JSON schema validation in production FFI bindings. |

### Invariant Verification
- ✅ `INV: Graph = f(WAL)` & `INV: Post-Commit: WAL.persisted AND Graph.updated` → Verified by `refresh-projections(k)` and `commit-staged(k.wal)`.
- ✅ `INV: Fault -> !Commit; Rollback -> Stage.Empty` → Verified in `generate.spec` `FAULT_RECOVERY()`.
- ⚠️ **Critical Conflict:** `generate.spec` calls `rollback-stage(wal)` directly. This violates `INV: Kernel -> Sole State Mutator`. **Fix:** `generate.spec` must invoke `kernel-rollback(k)` API instead of direct WAL manipulation.
- ✅ `INV: abi_1to1` & `INV: mock_compat` → FFI and Mock specs are structurally aligned. Mock returns deterministic values (`MOCK_TOKEN_ID`, `SUCCESS_CODE`) matching production signatures.

---

## 3. Actionable Roadmap

### Phase 1: Schema Unification & Type Alignment
- [ ] **Create `shared/domain-types.spec`:** Define canonical enums for `Role`, `Status`, `Clock`, `ID`, and `Payload`. Export to all layers.
- [ ] **Resolve Type Mismatches:** Update `chat-loop.spec` and `ffi-bindings.spec` to use canonical types. Implement explicit casting macros in FFI layer.
- [ ] **Standardize Context Mapping:** Define `ContextObject` ↔ `LLM Context` transformation rules in `chron-llm-runtime.spec` to prevent semantic drift.

### Phase 2: Invariant Enforcement & Static Verification
- [ ] **Implement Invariant Linter:** Develop a static analysis tool to parse `INV:` statements and verify compliance across module boundaries (e.g., flag direct WAL access outside Kernel).
- [ ] **Fix SOT Violation:** Refactor `generate.spec` to delegate `rollback-stage(wal)` to a new `kernel-rollback(k)` API. Update `chron-llm-kernel.spec` to expose this operation.
- [ ] **Contract Validation Pipeline:** Add CI step to validate `RuntimeCommand` ABI compliance between R0/R1 specs and Kernel interface. Reject PRs that bypass the contract.

### Phase 3: FFI & Mock Automation
- [ ] **Generate FFI Bindings:** Build a code generator that parses `ffi-bindings.spec` and `ffi-bindings-mock.spec` to auto-produce C/LLVM bindings and mock implementations.
- [ ] **ABI Parity Testing:** Implement property-based tests that run identical sequences against `ffi-bindings.spec` (production) and `ffi-bindings-mock.spec` (mock). Verify `INV: mock_compat` at runtime.
- [ ] **Pointer Safety Checks:** Integrate `valgrind`/`AddressSanitizer` hooks into the FFI layer to enforce `INV: stateless` and prevent dangling native pointer references.

### Phase 4: Integration & CI/CD Pipeline
- [ ] **Module Import Registry:** Establish a central registry for cross-spec imports. Enforce dependency graphs to prevent circular references between Kernel, Runtime, and Backend.
- [ ] **Automated Trace Reconstruction:** Implement a verification harness that uses `R0Trace` snapshots (`h-before`, `h-after`) to replay session flows and validate `INV: trace.snapshots`.
- [ ] **Deployment Gate:** Require all spec changes to pass invariant checks, type alignment validation, and FFI mock parity tests before merging. Document architectural boundaries in `chron-llm-r0-session-execution-layer-spec-v1.0.spec` as the source of truth for layer contracts.