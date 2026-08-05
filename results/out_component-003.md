# Structured Analysis Report: Component-003

## 1. Optimal Merge Plan

Based on artifact relationships, similarity scores, and recommended actions, the 12 specification components are consolidated into five architectural tiers. Redundant definitions are deprecated, superseded files are merged, and separation of concerns is preserved.

| Tier | Primary Artifact (SOT) | Secondary/Target Artifacts | Recommended Action | Rationale & Integration Path |
|:---|:---|:---|:---|:---|
| **Core Constitution** | `docs/ir/Chron-LLM_R2.0-A_Graph_Runtime_Core_Constitution_Spec.spec` | `docs/ir/Chron-LLM_R2.0-B_World_Runtime_Constitution_Spec.spec` | `KEEP_BOTH` | **PARENT_CHILD**. A defines data invariants & causal purity; B defines World lifecycle & isolation. Maintain modularity. B is `FROZEN`; A remains the active constitutional anchor. |
| **World & Registry Runtime** | `docs/spec/ir/R2.0-B_C_World_Runtime_Observation_Contract_v1.0.spec` | `world/ir/world.spec`, `registry/ir/registry.spec`, `docs/spec/ir/Chron-R2.0-World-Graph-Runtime-Specification-v1.0.spec` | `MERGE_B_INTO_A` / `DEPRECATE_OBSOLETE` | Contract A supersedes B's implementation details (`head-cell` vs `head`, `Shared` refs). Registry spec contradicts constitutional non-authoritative invariants and must be deprecated. Merge World/Registry logic into A's observation contract. |
| **Graph & Context Runtime** | `graph-runtime/ir/chron-llm-r2-graph-runtime-causal-context-spec-v1.0.spec` | `graph-runtime/ir/graph.spec`, `graph-runtime/ir/prefill.spec`, `graph-runtime/ir/projection.spec` | `KEEP_BOTH` (Graph) / `KEEP_A_DELETE_B` (Prefill/Projection) | Context spec is the canonical v1.0 runtime contract. `graph.spec` provides low-level kernel primitives and must be kept for separation of concerns. `prefill.spec` and `projection.spec` are subsumed; their logic migrates to the Context spec. |
| **Memory & Storage** | `memory/ir/store.spec` | `docs/ir/Chron-LLM_R2.0-A_Graph_Runtime_Core_Constitution_Spec.spec` | `KEEP_BOTH` | **PARENT_CHILD**. Store spec implements operational granularity (SHA-256 logic, CoW semantics). Constitution defines high-level invariants (`INV-MEM-IMMUTABLE`, `INV-MEM-HASH`). Maintain distinct abstraction layers. |
| **Verification & Testing** | `tests/md/ir/r2-0-b-tests.spec` | `docs/ir/Chron-LLM_R2.0-B_World_Runtime_Constitution_Spec.spec` | `KEEP_BOTH` | **PARENT_CHILD**. Tests map directly to Constitution B's `TEST B1-B12`. Keep separate to preserve boundary between requirements and validation. Fix package naming (`r2-0-a` → `r2-0-b`). |

---

## 2. Architectural Consistency & Invariant Verification

### Schema Alignment & Type Mismatches
| Type/Field | Inconsistency Detected | Resolution Required |
|:---|:---|:---|
| `PayloadRef` | `hash` typed as `Hash/Str/SHA256`; `size` as `Int/U64`; `storage` as `StorageType/Ref/Keyword`. | Unify to `hash: String (SHA256 hex)`, `size: U64`, `storage: Enum(:memory | :disk | :remote)`. |
| `World.head` | `world/ir/world.spec` defines `head-cell: [NodeID]` (list); all others use `head: ID/NodeRef`. | Standardize to `head: ID`. Remove list wrapper; enforce single active head per lifecycle state. |
| `Registry` Ownership | `registry/ir/registry.spec` owns `graph` & `memory` state. Constitution B mandates `World.graph-ref == GlobalState.canonical-graph`. | Refactor Registry to hold only `Map<UUID, World>` and `ancestry`. Graph/Memory must be external shared references. |
| `ContextNode.content` | `prefill.spec` uses `String`; `chron-llm-r2-graph-runtime-causal-context-spec-v1.0.spec` uses `Payload`. | Align to `content: String` post-materialization. Keep `payload-ref` in `CausalNode` for immutability; materialize only during `project-context`. |

### SOT Consistency & Drift Analysis
- **Fragmented Graph Definitions:** `CausalGraph`, `CausalNode`, and `CausalEdge` are redundantly defined across 5 files. The Constitution A and `chron-llm-r2-graph-runtime-causal-context-spec-v1.0.spec` must serve as the single source of truth. All other files must import or reference these canonical types.
- **Lifecycle State Drift:** `registry/ir/registry.spec` uses `State={inactive,active,archived}` while Constitution B uses `LifecycleState := CREATED \| ACTIVE \| INACTIVE \| ARCHIVED`. Align to B's explicit state machine to enforce `ARCHIVED !-> ACTIVE` transition rules.
- **Kernel Authority Violation:** `Chron-R2.0-World-Graph-Runtime-Specification-v1.0.spec` exposes mutable `add-node!` operations on shared graphs, directly contradicting `INV-AUTHORITY` and `INV-GRAPH-APPEND`. Graph mutations must be routed exclusively through `CommitKernel`.

### Invariant Conflict Resolution
| Invariant | Conflict Source | Verification Status | Remediation |
|:---|:---|:---|:---|
| `INV-GRAPH-APPEND` / `INV-AUTHORITY` | `Chron-R2.0-World-Graph-Runtime-Specification-v1.0.spec` allows direct graph mutation. | ❌ FAIL | Restrict all graph modifications to `kernel-commit-world!` or `CommitKernel` pipeline. |
| `INV-CAUSAL-SEPARATION` / `INV-EVAL-INDEP` | `project-context` logic in `projection.spec` mixes evals into causal traversal when `include_eval=true`. | ⚠️ PARTIAL | Enforce strict separation: `build-prefill-state` must exclude evals. `include_eval` should only affect a secondary `feedback-context` projection, not causal ancestry. |
| `INV-REPLAY-DET` / `INV-PREFILL-DET` | `prefill.spec` lacks explicit builder determinism constraints; `chron-llm-r2...spec` enforces `INV Determinism`. | ✅ PASS | Adopt `chron-llm-r2...spec`'s deterministic serialization and hash stability rules as the baseline. |
| `INV_META_COW` | `world/ir/world.spec` uses `w.meta = [copy(new-meta)]` but lacks structural sharing guarantees. | ⚠️ PARTIAL | Implement explicit Copy-on-Write (CoW) semantics at the data structure level to ensure parent metadata remains logically isolated. |

---

## 3. Actionable Roadmap

### Phase 1: Consolidation & Deprecation (Weeks 1-2)
- [ ] **Merge & Deprecate:** Consolidate `prefill.spec` and `projection.spec` into `chron-llm-r2-graph-runtime-causal-context-spec-v1.0.spec`. Mark both as `DEPRECATED` in the spec registry.
- [ ] **Registry Refactor:** Deprecate `registry/ir/registry.spec`. Migrate non-authoritative registry logic into `R2.0-B_C_World_Runtime_Observation_Contract_v1.0.spec`.
- [ ] **World Spec Alignment:** Replace `world/ir/world.spec` definitions with the Observation Contract. Resolve `head-cell` vs `head` discrepancy by standardizing on `head: ID`.
- [ ] **Package Naming Fix:** Update `tests/md/ir/r2-0-b-tests.spec` package declaration from `r2-0-a` to `r2-0-b`.

### Phase 2: Invariant Enforcement & Schema Unification (Weeks 3-4)
- [ ] **Type Schema Unification:** Generate a unified JSON Schema/IDL for `PayloadRef`, `CausalNode`, `World`, and `Registry`. Enforce `U64` for sizes, `String` for hashes, and `Enum` for lifecycle/storage types.
- [ ] **Invariant Guardrails:** Implement static analysis rules (e.g., AST linters or custom schema validators) to flag:
  - Direct `add-node!` calls outside `CommitKernel`
  - Mutable `World.graph-ref` or `World.memory-ref`
  - Non-deterministic `build-prefill-state` inputs
- [ ] **Causal/Eval Separation Enforcement:** Update `project-context` and `build-prefill-state` signatures to strictly isolate causal traversal from evaluation metadata. Introduce explicit `include_feedbacks` flag that operates on a disjoint projection path.

### Phase 3: Automation, Verification & Integration (Weeks 5-8)
- [ ] **Spec-to-Code Scaffolding:** Generate language-agnostic type definitions (TypeScript/Go/Rust) from the unified schemas. Embed invariant checks as compile-time or runtime assertions.
- [ ] **CI/CD Integration:** 
  - Integrate `tests/md/ir/r2-0-b-tests.spec` into the CI pipeline as property-based tests (PBT) using frameworks like `QuickCheck` or `Hypothesis`.
  - Add spec-diff checks to prevent future architectural drift between Constitution A/B and runtime implementations.
- [ ] **Determinism Verification Pipeline:** Implement automated hash-stability tests for `PrefillState` across varying input permutations. Validate `INV-REPLAY-DET` by replaying graph+memory states and comparing output hashes.
- [ ] **Documentation & Dependency Graph:** Publish a spec dependency graph mapping `Constitution A/B` → `Observation Contract` → `Graph/Runtime Specs` → `Store/Tests`. Enforce import-only relationships to prevent redundant type definitions.