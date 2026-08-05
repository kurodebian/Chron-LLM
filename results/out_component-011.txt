# Structured Analysis Report: Component-011 (IR Observation Layer)

## 1. Optimal Merge Plan

| Source Artifact | Target Artifact | Relationship | Recommended Action | Execution Strategy |
|:---|:---|:---|:---|:---|
| `runtime/ir/stream.spec` | `runtime/ir/ir.spec` | `PARTIAL_OVERLAP` | **MERGE_B_INTO_A** | Absorb `stream.spec`'s runtime buffer logic (`adjustable=T`, `fill-pointer`) into `ir.spec` as a concrete implementation detail. Normalize Lisp-style global state (`*ir-stream*`) into an explicit, injectable buffer interface. |
| `runtime/ir/divergence.spec` | `runtime/ir/chron-llm-r1-ir-observation-layer-spec-v1.0.spec` | `PARTIAL_OVERLAP` | **MERGE_B_INTO_A** | Retain `chron-llm-r1...spec` as the canonical architectural layer. Extract concrete algorithmic logic from `divergence.spec` (`calc_divergence_metrics`, step-wise token frequency analysis) and integrate it into `chron-llm-r1...spec`'s `divergence-profile` operation. |
| `runtime/ir/callback.spec` | `runtime/ir/stream.spec` | `INDEPENDENT` | **KEEP_BOTH** | Maintain strict separation. `callback.spec` acts as the FFI ingestion bridge (Producer), while `stream.spec` acts as the storage buffer (Consumer). Link via explicit dependency injection rather than structural merging. |
| `runtime/ir/divergence.spec` | `runtime/ir/ir.spec` | `PARTIAL_OVERLAP` | **KEEP_BOTH** | Preserve `ir.spec` as the foundational schema. Refactor `divergence.spec` toimport `ir.spec`'s canonical `IR` type, eliminating local type duplication and preventing schema drift. |
| `runtime/ir/callback.spec` | `runtime/ir/ir.spec` | `PARENT_CHILD` | **KEEP_BOTH** | Maintain modularity. `ir.spec` defines the deterministic type contract; `callback.spec` implements the physical-to-IR bridge. Enforce compliance via invariant checks in the bridge layer. |

**Consolidated Architecture:**
- **Canonical Schema:** `ir.spec` (Single Source of Truth for `IR`, `Phase`, `Stream`)
- **Architectural Core:** `chron-llm-r1...spec` (Unified observation layer, analysis ops, and lifecycle)
- **Bridge Layer:** `callback.spec` (FFI ingestion, thread-safety gate)
- **Runtime Buffer:** Merged into `ir.spec` (formerly `stream.spec`)

---

## 2. Architectural Consistency & Invariant Verification

### Schema Alignment & Type Mismatches
| Type/Field | `ir.spec` (SOT) | `chron-llm-r1...spec` | `divergence.spec` | `stream.spec` | `callback.spec` | Status |
|:---|:---|:---|:---|:---|:---|:---|
| `IR.token` | `TOKEN_ID` (Int/ID) | `int` | `String` | Implicit | `Int` | **MISMATCH** (`divergence.spec` uses `String`) |
| `IR.phase` | `{0:PREFILL \| 1:GENERATION \| 2:FINALIZE}` | `{0:prefill \| 1:gen \| 2:finalize}` | `Int` | Implicit | `Int` | **NOMINAL DRIFT** (Enum casing/aliasing) |
| `IR.ctx-id` | `ID` | `ptr` | Missing | Implicit | `Ptr` | **MISSING** in `divergence.spec` |
| `IR.score` | `FLOAT` | `float` | Missing | Implicit | `Float` | **MISSING** in `divergence.spec` |
| `Stream` | `[IR]` | `array[IR]` | `Vector<IR>` | `Array[IR] {adjustable=T}` | Implicit | **IMPLEMENTATION VARIANCE** (Normalize to contiguous array/buffer) |

### Invariant Verification & Conflicts
- **Determinism (`INV-DETERMINISTIC` / `INV_DET`):** Consistent across `chron-llm-r1...spec` and `divergence.spec`. Requires explicit seed management in `run-trial` to guarantee `INV-REPLAY` compliance.
- **Immutability (`INV-IMMUTABLE` / `INV_LOSSLESS`):** Present in 3/5 specs. Conflict risk: `stream.spec` declares `adjustable=T` and `fill-pointer=0`, which implies mutability of the container, not the elements. Must clarify that `IR` elements are immutable post-creation, while the `Stream` container is append-only.
- **Isolation (`INV-ISOLATION` / `INV_OBS_ONLY`):** Consistent. Analysis operations must not feed back into Runtime/Kernel state. Enforce via read-only view injection into analysis ops.
- **Ordering (`INV-ORDERING` / `INV-S1` / `INV-ORDERED`):** Consistent. `extract-actions` must guarantee `pos` monotonicity. `stream.spec`'s `INV-S1` ties ordering to push timestamp (`t`), which may conflict with `pos`-based ordering if timestamps are non-monotonic across threads. **Recommendation:** Enforce ordering strictly by `pos`,not wall-clock time.

### Critical Risks
1. **Concurrency Safety:** `stream.spec` explicitly states `THREADING: UNSAFE(GlobalMutable(*ir-stream*))`, while `callback.spec` states `THREAD: Safe iff push_ir is Thread-Safe`. This is a direct contradiction. Global mutable state without synchronization will cause data races during concurrent LLM decoding.
2. **State Management Paradigm:** `stream.spec` uses Lisp-style dynamic globals (`*ir-stream*`). `chron-llm-r1...spec` uses explicit `STATE *ir-stream*`. This creates ambiguity in lifecycle management (clear/reset semantics) and hinders formal verification.

---

## 3. Actionable Roadmap

### Phase 1: Schema Unification & Import Refactoring
1. **Enforce `ir.spec` as SOT:** Update `divergence.spec` and `stream.spec` to import `IR`, `Phase`, and `Stream` directly from `ir.spec`. Replace `token: String` with `TOKEN_ID` and restore missing `ctx-id`/`score` fields.
2. **Normalize Enum Naming:** Standardize `Phase` enum to `{0:PREFILL, 1:GENERATION, 2:FINALIZE}` across all specs. Add explicit type aliases in `chron-llm-r1...spec` for backward compatibility if needed.
3. **Merge Buffer Logic:** Absorb `stream.spec` into `ir.spec`. Convert `*ir-stream*` global state into a deterministic, injectable `IR_Buffer` struct with explicit `allocate()`, `push()`, `clear()`, and `snapshot()` methods.

### Phase 2: Algorithmic Consolidation & State Normalization
1. **Integrate Divergence Algorithms:** Extract the step-wise token frequency calculation from `divergence.spec` and embed it into `chron-llm-r1...spec`'s `divergence-profile` operation. Standardize the `Profile` type to match `DivRes` schema.
2. **Standardize `extract-actions`:** Unify signature to `extract_actions(stream: Stream) -> List<IR>` with explicit `pos`-sorting and `phase==1` filtering. Remove redundant `copy()` and `sort()` calls by implementing a stable, index-preserving filter in the canonical layer.
3. **Lifecycle Enforcement:** Implement `INV-S4` (RunStart -> clear) as an explicit `begin_trial()` / `end_trial()` wrapper in `chron-llm-r1...spec` to guarantee bufferstate isolation between runs.

### Phase 3: Concurrency Hardening & Invariant Enforcement
1. **Resolve Threading Contradiction:** Replace `UNSAFE` global mutable array with a lock-free ring buffer or thread-local buffer with atomic commit. Update `callback.spec` to mandate `push_ir` uses atomic append or explicit mutex guards.
2. **Invariant Guards:** Implement runtime assertions for `INV-IMMUTABLE` (frozen `IR` fields post-creation) and `INV-APPEND-ONLY` (reject in-place mutations on `Stream`).
3. **Ordering Correction:** Decouple `INV-S1` from timestamp-based indexing. Enforce `pos`-monotonicity at push time; reject or reorder out-of-sequence `IR` entries based on `pos` field.

### Phase 4: Automated Verification & CI Integration
1. **Formal Property Testing:** Generate QuickCheck/Hypothesis test suites for:
   - `INV-DETERMINISTIC`: `run_trial(prompt, seed) == run_trial(prompt, seed)`
   - `INV-REPLAY`: `analyze(snapshot(S1)) == analyze(snapshot(S2))` if `S1 == S2`
   - `INV-ORDERING`: `extract_actions(stream).pos` is strictly non-decreasing.
2. **Schema Linting:** Implement a CI pipeline step that parses all `.spec` files and validates type imports against `ir.spec`. Fail build on `token: String` or missing`ctx-id`/`score` references.
3. **Integration Test Harness:** Build a mock `LLM_BACKEND` simulator that emits `IR` events at controlled intervals. Validate `callback.spec` bridge latency (`O(1)`), `stream.spec` buffer growth (`O(1)` append), and `divergence.spec` profiling accuracy against ground-truth token sequences.