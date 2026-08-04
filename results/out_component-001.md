# Structured Analysis Report

## 1. Optimal Merge Plan

### Cluster A: `docs/ir/` (Abstract & Architectural Specifications)
*   **Merge `04-runtime-pipeline.spec` into `02-operational-semantics.spec`** (`pair_11`): Consolidate the behavioral pipeline flow into the formal operational semantics. `02` provides superior PRE/POST conditions and atomicity invariants; merging `04` into `02` enforces rigorous verification across all pipeline stages while preserving the PromptBuilder/Backend flow.
*   **Maintain `01-domain-model.spec` & `07-chron-mapping.spec` as Independent Artifacts** (`pair_42`, `pair_33`, `pair_70`): Preserve strict separation of concerns. `01` remains the canonical schema definition (Phase C), while `07` acts as the semantic bridge to Delta3 Kernel internals (Phase E). No merge; enforce cross-referencing.
*   **Maintain `02-operational-semantics.spec` & `07-chron-mapping.spec` Separately** (`pair_33`): Keep abstract invariants decoupled from concrete runtime artifacts to maintain kernel refactoring flexibility.

### Cluster B: `runtime/r1/ir/` (Concrete Runtime Specifications)
*   **Merge `package.spec` into `core.spec`** (`pair_4`): `core.spec` is the authoritative compliance specification. Merge `package.spec` to adopt its cleaner operation categorization (`pure-ops`, `kernel-boundary`, `runtime-facade`, `inspection`, `testing`) and integrate its inspection/testing interfaces into a single source of truth.

### Cross-Cluster Integration Strategy
*   Enforce `01-domain-model.spec` as the Single Source of Truth (SOT) for all type definitions.
*   `02` (merged with `04`) must formally reference `01` types rather than duplicating enums.
*   `core.spec` (merged with `package.spec`) must import strictly from `01` to eliminate semantic duplication.
*   `07-chron-mapping.spec` must replace type definitions with `@map` annotations pointing to `01` and `core.spec`.

## 2. Architectural Consistency & Invariant Verification

### Schema Alignment & Type Consistency
*   **`Event` Definition Mismatch**: 
    *   `01`: `{id, source:Source, content, meta:{ts,seq,causal-ref?}}`
    *   `core`: `{id: UUID, source: Source, payload: Any, metadata: Map}`
    *   *Resolution*: Standardize field names (`content` → `payload` or vice versa) and unify `meta`/`metadata` structure in `01`. `core` must adopt the unified schema.
*   **`Candidate` Definition Mismatch**:
    *   `01`: `{id, origin, intent:Intent, content, constraints, meta}`
    *   `core`: `{trigger: Any, constraints: List, metadata: Map} + Event`
    *   `package`: `{id, source, trigger, intent, payload, constraints, metadata}`
    *   *Resolution*: Consolidate into a single definition in `01`. Align `origin`/`trigger`/`source` and `content`/`payload`. `core` and `package` must inherit via import.
*   **`RuntimeRequest` vs `KernelAction` vs `RuntimeCommand`**:
    *   `01`/`02` define `RuntimeRequest` (policy output).
    *   `core` defines `KernelAction` (accept, reject, defer, retry, etc.).
    *   `01`/`package` define `RuntimeCommand` (kernel output).
    *   *Resolution*: Clarify the pipeline contract: `PolicyRouter` outputs `RuntimeRequest` → `Kernel` interprets as `KernelAction` → `Kernel` outputs `RuntimeCommand`. Ensure type signatures reflect this transformation explicitlyin `02`/`core`.
*   **`Canonical` Nesting**: `01` nests `Canonical` inside `Session`, while others treat it as a top-level state. *Resolution*: Elevate `Canonical` to a top-level type in `01` and reference it from `Session` to maintain consistencyacross `02`, `04`, `07`, and `core`.

### Invariant Verification & SOT Consistency
*   **Canonical Immutability & Mutation Authority**: 
    *   `INV(Canonical): mutate_only_via(Commit)` (`01`) ✅ Matches `INV4: commit() sole Canonical updater.` (`core`) ✅ Matches `INV: write(CanonicalState) == Commit` (`07`). **Consistent.**
*   **Determinism & Purity**: 
    *   `PROP: Pure | Deterministic` for `Replay`, `Derive`, `Validation` (`02`) ✅ Matches `INV2: validate(), policy-route() side-effect free.` (`core`) ✅ Matches `INV: Deterministic(Replay)` (`04`). **Consistent.**
*   **State Mutation Boundaries**: 
    *   `INV3: kernel-transition() sole Runtime state mutator.` (`core`) ✅ Aligns with `OWNERSHIP` constraints in `01`. **Consistent.**
*   **Single Source of Truth (SOT) Violations**: 
    *   High duplication of type definitions across `01`, `02`, `04`, `07`, `core`, and `package`. Current architecture violates SOT principles. Cross-referencing must be enforced to prevent divergence during refactoring.
*   **Ownership & Data Flow Alignment**: 
    *   `PROD_CONS` (`01`) accurately maps to the pipeline in `04` and `core`. `OWNERSHIP` constraints align with `core`'s `kernel-transition` and `commit` boundaries. No logical conflicts detected.

## 3. Actionable Roadmap

### Phase 1: Schema Unification & Import Enforcement
1.  **Standardize Core Types in `01-domain-model.spec`**: Resolve `Event` (`content` vs `payload`), `Candidate` (`origin` vs `trigger`), and `Canonical` nesting discrepancies. Publish v1.0 of the canonical schema.
2.  **Implement Import/Reference Protocol**: Update `core.spec` and `package.spec` to use explicit module imports (e.g., `IMPORT 01-domain-model.spec AS Schema`). Remove all redundant type definitions.
3.  **Refactor `07-chron-mapping.spec`**: Replace concrete type definitions with mapping annotations (e.g., `@map Event -> WAL_Entry`, `@map Canonical -> CanonicalState`). Ensure it only contains binding logic.

### Phase 2: Merge Execution & Refactoring
1.  **Execute `04` → `02` Merge**: Integrate pipeline operations (`PromptBuilder`, `Backend`, `Validation`, `PolicyRouter`, `Kernel`, `Runtime`) into `02-operational-semantics.spec`. Attach formal PRE/POST conditions and invariantsto each operation.
2.  **Execute `package` → `core` Merge**: Consolidate `package.spec` into `core.spec`. Organize operations into thecategorized blocks (`domain-api`, `pure-ops`, `kernel-boundary`, `runtime-facade`, `inspection`, `testing`). Retainall invariant definitions (`INV1`-`INV8`).
3.  **Validate Cross-Cluster Consistency**: Run a dependency checker to ensure `02` (merged) and `core` (merged) correctly reference `01` types without circular dependencies.

### Phase 3: Automated Verification & CI Integration
1.  **Static Analysis Rules**: Implement AST-based linters to enforce `INV1`-`INV8`. Flag any mutation outside `commit()` or `kernel-transition()`, and detect side-effects in `pure-ops`.
2.  **Formal Verification Scripts**: Generate TLA+ or Coq specifications from `02`'s PRE/POST conditions to mathematically verify atomicity, determinism, and state transitions.
3.  **CI Pipeline Integration**: 
    *   Add `chronos-r1-self-test()` (from merged `core.spec`) to the test suite to validate the commit-validation-kernel-runtime flow.
    *   Enforce schema import compliance in pre-commit hooks. Fail builds on type duplication or missing cross-references.
4.  **Documentation Generation**: Auto-generate API contracts and pipeline diagrams from the unified specs to ensure external consumers and runtime implementations stay aligned with the SOT.