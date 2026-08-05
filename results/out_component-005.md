# Structured Analysis Report: Component-005

## 1. Optimal Merge Plan

**Decision:** `MERGE_A_INTO_B`  
**Target Artifact:** `llama-agent/ir/chron-llm-world.spec`  
**Source Artifact:** `llama-agent/ir/chron-llm-immune.spec`  
**Rationale:** Artifact B (`chron-llm-world.spec`) represents the canonical, implementation-ready specification. Itfeatures a robust data model (`CausalNode` with fault/valid classification), explicit phase constraints, and maturealgorithmic definitions. Artifact A (`chron-llm-immune.spec`) contains redundant branching logic and a less structured state model. The `ImmuneStatus` domain from A must be integrated into B as a derived query to maintain a single source of truth for World operations.

### Merge Execution Steps
1.  **Type Integration:**
    *   Import `ImmuneStatus = :ok | :degraded` into B's `TYPES` section.
    *   Retain B's `CausalNode` model; discard A's implicit `Node` type in favor of B's explicit `CausalNode` definition.
    *   Align `BranchEvent` payload structure. Replace A's `{ParentNodeID, ParentWorldID}` with B's `{parent_node, parent_world}` to match B's naming convention and `CausalNode` references.
2.  **Operation Integration:**
    *   Add `check-immune-status(WorldID: WorldID) -> ImmuneStatus` to B's `OPS` section.
    *   Implement `check-immune-status` logic in B's `ALGORITHMS` section:
        *   Query `get_latest_node_in_world(WorldID)`.
        *   Return `:ok` if result is non-NIL and `result.class == :valid`.
        *   Return `:degraded` if result is NIL or `result.class == :fault`.
    *   Subsume A's `clean-history` and `stage-event` into B's existing `wal` management or mark as Phase2/Omitted per B's constraints.
3.  **State & Counter Alignment:**
    *   Standardize state naming to B's convention: `wal_world_counter`, `graph`, `wal`.
    *   Adopt B's `graph: [CausalNode]` list structure over A's `{WorldID: Node}` map for consistency with `get_latest_node_in_world` filtering logic.
4.  **Invariant Consolidation:**
    *   Merge A's `INV(BranchEvent): ParentNodeID -> CommittedNode` into B's `INV: Query excludes :fault nodes` and`INV: Query returns single latest node per WorldID`.
    *   Retain B's `INV: RootParent == 0` (implicitly supported by A's fallback logic).

---

## 2. Architectural Consistency & Invariant Verification

### Schema Alignment & Drift Analysis
| Component | Artifact A (`chron-llm-immune.spec`) | Artifact B (`chron-llm-world.spec`) | Status | Action |
| :--- | :--- | :--- | :--- | :--- |
| **Types** | `EventKind = :branch` | Hardcoded `kind: :branch` in `BranchEvent` | **Drift** | Adopt B's inline definition; `EventKind` is redundant for current scope. |
| **Payload Keys** | `ParentNodeID`, `ParentWorldID` | `parent_node`, `parent_world` | **Mismatch** | Standardize to B's snake_case/lowercase keys. |
| **Graph Model** | `Graph: {WorldID: Node}` | `graph: [CausalNode]` | **Mismatch** | Adopt B's list model; enablesefficient fault filtering and max-ID queries. |
| **Counter** | `wal-world-counter` | `wal_world_counter` | **Mismatch** | Standardize to B's naming. |
| **Fault Handling** | Implicit via `ImmuneStatus` | Explicit `class: :fault | :valid` | **Enhancement** | B's model is superior; A's `ImmuneStatus` becomes a derived view of B's fault state. |

### SOT Consistency
*   **Source of Truth:** `chron-llm-world.spec` is confirmed as SOT.
*   **Logic Redundancy:** A's `stage-branch-world` logic duplicates B's `stage_branch_world` but lacks B's fault-aware filtering in `get_latest_node_in_world`. B's implementation is strictly more robust.
*   **Phase Constraints:** B explicitly defines `Phase1: Implemented=[stage_branch_world, get_latest_node_in_world]`. A's `check-immune-status` should be evaluated against this. Since `check-immune-status` is a derived query over existing ops, it can be integrated into Phase1 without new state mutations, or marked as a Phase1 extension if complexity warrants.

### Invariant Verification
*   **Monotonicity:** Both specs enforce `wal_world_counter` monotonicity. **PASS**.
*   **Uniqueness:** B's `POST: returned WorldID unique` and `INV: wal_world_counter monotonic` ensure uniqueness. **PASS**.
*   **Fault Exclusion:** B's `INV: Query excludes :fault nodes` and algorithm `n.class != :fault` ensure data integrity. A's `ParentNodeID -> CommittedNode` is satisfied by B's model where `CommittedNode` maps to `class: :valid`. **PASS**.
*   **Immune Logic:** A's `INV(Immune): HistoryExists -> Status = :ok` requires verification against B.
    *   *Verification:* If `HistoryExists` implies a valid node exists, B's `get_latest_node_in_world` returns a valid node. The derived `check-immune-status` will return `:ok`. If history is degraded (faults), B returns `:degraded`. **PASS** (with integration).

---

## 3. Actionable Roadmap

### Automation & Integration
1.  **Spec Refactoring Script:**
    *   Execute merge of `chron-llm-immune.spec` into `chron-llm-world.spec`.
    *   Apply field renaming: `Payload.ParentNodeID` → `payload.parent_node`, `Payload.ParentWorldID` → `payload.parent_world`.
    *   Inject `ImmuneStatus` type and `check-immune-status` operation definition.
    *   Inject `check-immune-status` algorithm body referencing `get_latest_node_in_world`.
2.  **Constraint Update:**
    *   Update `chron-llm-world.spec` `CONSTRAINTS` section:
        ```markdown
        Phase1: Implemented=[stage_branch_world, get_latest_node_in_world, check-immune-status]
        Phase1: Omitted=[commit, merge, replay, validation]
        ```
3.  **Deprecation:**
    *   Mark `chron-llm-immune.spec` as `DEPRECATED` in the component registry.
    *   Remove file from active build pipeline; retain only for historical reference.

### Verification & Testing
1.  **Invariant Checks:**
    *   Verify `check-immune-status` returns `:ok` for worlds with `class: :valid` nodes.
    *   Verify `check-immune-status` returns `:degraded` for worlds where `get_latest_node_in_world` returns `NIL` or `class: :fault`.
    *   Ensure `RootParent == 0` invariant holds for root world creation.
2.  **Type Safety:**
    *   Validate that `BranchEvent` payload types strictly match `NodeID` and `WorldID`.
    *   Confirm `CausalNode` class enum is exhaustive (`:fault | :valid`).
3.  **Regression:**
    *   Run existing tests for `stage_branch_world` and `get_latest_node_in_world` against the merged spec to ensure no behavioral drift in core operations.
    *   Add unit tests for `check-immune-status` covering edge cases (empty graph, all faults, mixed faults).

### Code/Spec Synchronization
*   **Delta3 Kernel:** Update kernel implementation to expose `check-immune-status` as a read-only query derived from the `graph` state.
*   **WAL Schema:** Ensure WAL serialization format aligns with B's `BranchEvent` structure (lowercase keys).
*   **Documentation:** Update API documentation to reflect `ImmuneStatus` as a derived metric of `CausalNode` validity, removing any references to independent `Immune` state management.