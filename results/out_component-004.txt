# Component-004 Specification Analysis Report

## 1. Optimal Merge Plan

### Merge Hierarchy & Actions
| Source Artifact | Target Artifact | Recommended Action | Execution Rationale |
|---|---|---|---|
| `architecture-v1.spec` | `architecture-v1.1.spec` | `DEPRECATE` | Superseded by v1.1 (stream/tool granularity, WAL-based traversal, simplified state model) |
| `chron-llm-causal.spec` | `causal-kernel.spec` | `DEPRECATE` | Superseded by mature Phase D/E kernel; conflicts with UUID/Hash invariants and lacks causal semantics |
| `chron-llm-graph.spec` | `architecture-v1.1.spec` | `MERGE_B_INTO_A` | Absorb `HealthyTable`, `find-parent-node-id`, and optimized parent lookup into canonical arch spec |
| `causal-kernel.spec` | `architecture-v1.1.spec` | `MERGE_B_INTO_A` | Integrate staging, world-line isolation (`wld`), `classify`, and `lift` logic into arch SOT |
| `13-worldline-branching.spec` | `Chron-LLM_R2.0-D_Commit...spec` | `INTEGRATE` | Branching policy must explicitlyinvoke Constitution's `Commit` operation for persistence instead of abstract `gen_id()` |
| `Chron-LLM_R2.0-D_Commit...spec` | `architecture-v1.1.spec` | `ALIGN` | Constitution becomes authoritative persistence layer; arch spec adopts its invariants and state definitions |

### Consolidated Architecture Structure
- **Primary SOT:** `architecture-v1.1.spec` (Unified control flow, state management, and graph construction)
- **Persistence Authority:** `Chron-LLM_R2.0-D_Commit_Kernel_Constitution_Spec.spec` (Phase D Constitution, immutable WAL/Graph rules)
- **Deprecated/Removed:** `architecture-v1.spec`, `chron-llm-causal.spec`

---

## 2. Architectural Consistency & Invariant Verification

### Schema Alignment & Type Mismatches
- **Identity Types:** Constitution mandates `Hash`/`UUID` for deterministic, collision-resistant IDs. `causal-kernel.spec`, `chron-llm-causal.spec`, and `chron-llm-graph.spec` use `Int`/`node-id`/`idx`. This violates `UNIQUENESS` and `DETERMINISM` invariants under concurrent or distributed loads.
- **Temporal Fields:** Constitution enforces `NO_TIMESTAMPS` and relies on cryptographic hashing for causal ordering. `architecture-v1.1.spec` and `causal-kernel.spec` explicitly track `clock: U64`/`Int` and `timestamp: U64`. This introduces non-deterministic mutation risks and conflicts with `DETERMINISM`/`IDEMPOTENCY`.
- **Event Payload Structure:** Constitution uses `CandidateEvent` → `CanonicalEvent` with strict schema versioning.`v1.1` uses `Event` with `stream_id` and `payload: Any`. `causal-kernel` uses `pay: {txt, tgt, meta}`. Lack of unified schema risks serialization/deserialization failures during `WAL` replay.

### SOT Consistency
- **Fragmented State Models:** Three competing state definitions exist: `SystemState` (v1.1), `System` (v1), and `Kernel` (causal-kernel). The Constitution defines `Graph`, `WAL`, and `WorldHead` as the canonical runtime state.
- **Operation Divergence:** `commit_stream` (v1.1) vs `commit-staged` (chron-llm-causal) vs `commit` (causal-kernel) vs `Commit` (Constitution). Only the Constitution enforces strict `WAL_ORDERING` and `HEAD_VALIDITY`. Other specs allow implicit state mutations without formal pre/post conditions.

### Invariant Conflict Analysis
- **`APPEND_ONLY` vs `STAGING`:** Constitution enforces strict append-only WAL visibility. Kernel/Graph specs implement `stage`/`discard` buffers. *Resolution:* Staging must be treated as a pre-commit transient buffer, not part of the canonical WAL until `Commit` post-conditions are met.
- **`ISOLATION` vs `WORLDLINE` TRACKING:** Constitution guarantees `Commit(w1)` does not affect `WorldHead[w2]`. Kernel tracks `cur-wld` globally, risking cross-world state leakage if not strictly scoped. Branching spec tracks `history: Map<CausalID, Worldline>`, which must align with Constitution's `WorldHead` map.
- **`DETERMINISM` vs `clock`-based Mutation:** Invariant `Commit(c) == Commit(c)` requires pure functions. Clock increments (`k.wal.clk++`, `e.clock = state.clock + 1`) introduce side effects. Must be replaced with deterministic sequence counters or cryptographic derivation.

---

## 3. Actionable Roadmap

### Phase 1: Deprecation & Consolidation (Week 1)
1. Execute `git rm` for `architecture-v1.spec` and `chron-llm-causal.spec`.
2. Extract `HealthyTable`, `find-parent-node-id`, and `graph-history` algorithms from `chron-llm-graph.spec` into `architecture-v1.1.spec` under a `GraphOptimization` module.
3. Integrate `stage`, `discard`, `commit`, and `wld` isolation logic from `causal-kernel.spec` into `architecture-v1.1.spec`'s `SystemState` and `Op` definitions.
4. Update `13-worldline-branching.spec` to replace abstract `gen_id()` and `S'.history[...]` with explicit calls to`Commit(c: CandidateEvent)` from the Constitution.

### Phase 2: Schema Unification & Type Alignment (Week 2)
1. Replace all `Int`/`node-id`/`idx` identifiers with `UUID`/`Hash` types across merged specs to satisfy `UNIQUENESS` and `DETERMINISM`.
2. Remove `clock` and `timestamp` fields from `Event` and `Node` types. Replace with deterministic causal counters derived from `H(parent-causal-id, world-id, type, payload-ref)`.
3. Standardize `Event` payload schema to match Constitution's `CandidateEvent`/`CanonicalEvent` structure, enforcing `schema-version: Int` and `payload-ref: Pointer` to `ImmutableStore`.
4. Run automated schema diff validation (e.g., `jsonschema` or `thrift`/`avro` linting) to ensure zero breaking changes post-merge.

### Phase 3: Invariant Enforcement & Verification (Week 3)
1. Implement formal property tests for Constitution invariants: `WAL_ORDERING`, `HEAD_VALIDITY`, `ISOLATION`, and `IMMUTABILITY`.
2. Refactor `stage`/`discard` operations to operate on isolated memory buffers, ensuring canonical `WAL` and `Graph` remain strictly append-only until `Commit` post-conditions are met.
3. Add runtime invariant checkers to `Commit` and `Branch` operations to fail-fast on `WAL_ORDERING` or `HEAD_VALIDITY` violations.
4. Execute crash-recovery simulation tests (D8) to verify `WAL` replay reconstructs `Graph` and `WorldHead` deterministically without corruption.

### Phase 4: Integration & Automation (Week 4)
1. Update CI/CD pipeline to run spec validation, invariant property tests, and schema compatibility checks on everyPR.
2. Generate runtime stubs/boilerplate from the unified `architecture-v1.1.spec` and `Constitution` using IDL-to-code generators.
3. Align test suites (`D1`-`D10` from Constitution) with integration tests for `Branch`, `Commit`, and `Graph` operations.
4. Freeze `architecture-v1.1.spec` and `Chron-LLM_R2.0-D_Commit_Kernel_Constitution_Spec.spec` as the official SOT for Phase D/E development.