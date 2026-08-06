# Structured Analysis Report: component-009

## 1. Optimal Merge Plan
**Relationship:** `SUPERSEDED` | **Recommendation:** `MERGE_B_INTO_A`
**Target Artifact:** `llama-agent/ir/llama-agent.spec` (A)
**Source Artifact:** `llama-agent/ir/llama-agent2.spec` (B)

**Merge Strategy:**
- **Header & Versioning:** Retain A's module declaration (`MODULE llama-agent.lisp : Bootloader`) but append B's versioning metadata (`Chron-LLM Δ3 Phase 1.1`).
- **Error Handling & Load Logic:** Replace A's lenient `load_system_file` (which uses `warn()` on missing files) with B's strict `ERROR("Required file not found")` implementation. This enforces the `INV_FailFast` invariant.
- **Boot Sequence Alignment:** Consolidate A's `SEQ boot_order` with B's explicit `LOAD_*` functions. Map B's granular loading steps (`LOAD_PHYSICAL`, `LOAD_LLM`, `LOAD_CORE`, etc.) to A's `Layer` type enumeration to create a deterministic, phase-gated initialization sequence.
- **Invariant Integration:** Inject B's comprehensive invariants (`INV_LoadOrder`, `INV_NoReverseDep`, `INV_PhysicalSwap`, `INV_FailFast`) into A's invariant block. Retain A's `INV_purity` and `INV_abi` as they remain compatible.
- **Scope & Constraints:** Append B's `NON_RESPONSIBILITIES` and `PHASE_1_1_CONSTRAINTS` sections to A's documentation layer to explicitly define architectural boundaries and forbid prohibited patterns (e.g., ASDF, lazy loading, hot reload).
- **Artifact Lifecycle:** Mark `llama-agent2.spec` as deprecated/archived post-merge verification.

## 2. Architectural Consistency & Invariant Verification
**Schema Alignment:**
- Both artifacts follow a declarative specification schema (`MODULE`, `STATE`, `OPS`, `INVARIANTS`). B extends this with explicit `VERSION`, `NON_RESPONSIBILITIES`, and`PHASE_1_1_CONSTRAINTS` blocks. Alignment is high (similarity: 0.8473). Merging B into A standardizes the schema toward B's explicit, production-ready format.

**SOT (Single Source of Truth) Consistency:**
- B supersedes A by introducing stricter initialization guarantees. The merged spec will establish `llama-agent.spec` as the canonical SOT. State variables (`*system-dir*`, `*use-mock-physical-p*`) are semantically identical across both artifacts. API signatures (`start-delta3`, `start-delta3-stub`) align functionally, though B provides explicit parameter defaults and blocking behavior documentation. No conflicting SOT definitions exist post-merge.

**Type Mismatches:**
- `Bool` (A) vs `Boolean` (B): Trivial lexical difference. Normalized to `Boolean` in the merged spec.
- `Path` (B) vs implicit string/path handling (A): B explicitly types `*system-dir*` as `Path`. A uses `uiop:pathname-directory-pathname` implicitly. Merged spec will enforce explicit `Path` typing for all file system references.
- `Layer` enumeration: A defines `TYPE Layer = Physical | Logical | Kernel | Immune | Runtime | Generation | MainLoop`. B implies the same layers but uses function names (`LOAD_PHYSICAL`, etc.). No structural mismatch; B's functions map 1:1 to A's type variants.

**Invariant Verification:**
- `INV_boot_seq` (A) vs `INV_LoadOrder` (B): B's explicit array `[Physical, LLM, Core, Graph, World, Immune, Runtime, Generation, Test]` supersedes A's shorter sequence. Verified as compatible; B adds missing layers (`Core`, `Graph`, `World`, `Test`) required for Δ3 Phase 1.1.
- `INV_abi` (A) vs `INV_PhysicalSwap` (B): B explicitly enforces that the Physical Layer is the sole swappable unit (Mock/FFI). This strengthens A's `sig(my-llama-*_mock) == sig(my-llama-*_real)` check.
- `INV_deps` (A) vs `INV_NoReverseDep` (B): Both enforce forward-only dependency resolution. Verified consistent.
- `INV_FailFast` (B): Critical addition. A's `warn()` violates this. Post-merge, all file probes must trigger immediate termination on failure.
- `INV_purity` (A): `post_boot_state(bootloader) == {}`. B's explicit logging and state initialization do not contradict this, provided bootloader functions are side-effect-free regarding application state. Verified compatible.

## 3. Actionable Roadmap
**Phase 1: Automated Spec Harmonization**
- [ ] Develop a spec-diff/merge script to parse both `.spec` files, extract B's strict error handling, invariants, and constraints, and inject them into A's structure.
- [ ] Normalize type declarations (`Bool` → `Boolean`, unify `Path` typing) and standardize indentation/syntax to match B's explicit style.
- [ ] Update module header to `MODULE llama-agent.lisp : Bootloader (Chron-LLM Δ3 Phase 1.1)`.
- [ ] Archive `llama-agent2.spec` and update repository metadata to reflect the merge.

**Phase 2: Verification & Validation**
- [ ] Run static analysis against the merged spec to validate all `INV_*` declarations for syntactic correctness and logical completeness.
- [ ] Cross-reference `LOAD_*` function paths with the actual filesystem layout under `*system-dir*` to ensure no broken references.
- [ ] Implement a spec-to-test harness that simulates missing file scenarios to verify `INV_FailFast` triggers immediate termination.
- [ ] Validate `INV_PhysicalSwap` by testing both `*use-mock-physical-p* = T` and `F` states against the FFI binding files.

**Phase 3: Code/Spec Integration & CI/CD Enforcement**
- [ ] Generate Lisp initialization stubs from the merged spec using a deterministic code generator.
- [ ] Refactor the bootloader implementation to replace `warn()` with `ERROR()` and enforce the explicit `LOAD_*` sequence.
- [ ] Implement a deterministic loader function that iterates through `boot_order`, enforcing `INV_NoReverseDep` at runtime.
- [ ] Add CI/CD pipeline stages:
  - `spec-lint`: Validates merged `.spec` syntax and invariant structure.
  - `invariant-check`: Runs static verification of dependency ordering and physical layer swap logic.
  - `integration-test`: Executes bootloader initialization in a sandboxed environment to verify fail-fast behavior and mock/real FFI compatibility.
- [ ] Document `NON_RESPONSIBILITIES` and `PHASE_1_1_CONSTRAINTS` in the project README to prevent scope creep and enforce architectural boundaries.