# Structured Analysis Report: Specification Component Integration

## 1. Optimal Merge Plan

| File | Lifecycle Status | Role in Architecture | Merge/Refactor Action |
|------|------------------|----------------------|------------------------|
| `chron-llm-spec-v0.2.spec` | **ACTIVE (SOT)** | Canonical type system & behavioral contract for Delta3 Kernel IR layer | Retain as primary specification. Absorb algorithmic pre/post conditions from deprecated specs. |
| `3cluster.spec` | **ACTIVE (TEST/EXAMPLE)** | Concrete test fixture & canonical topology validator | Refactor to import types from `chron-llm-spec-v0.2.spec`. Preserve instance `G` and instance-level invariants for regression testing. |
| `chron-llm-r1-dynamical-analysis-experiment-spec-v0.1.spec` | **DEPRECATED** | Preliminary dynamical analysis contract | Archive. Migrate algorithmic definitions (`rollout*`, `find-cycle`, `build-basin-map`) into `chron-llm-spec-v0.2.spec`. |
| `basin.spec` | **DEPRECATED** | Legacy basin/attractor traversal logic | Archive. Migrate `build-basin-structure` invariants and pre/post conditions into `chron-llm-spec-v0.2.spec`. |

**Consolidation Strategy:**
- Establish `chron-llm-spec-v0.2.spec` as the Single Source of Truth (SOT).
- Decouple `3cluster.spec` from type definitions; convert it to a pure instance/configuration module that references the canonical type system.
- Eliminate redundancy by removing local type redeclarations in deprecated files and enforcing import-only policies for the test fixture.

## 2. Architectural Consistency & Invariant Verification

### Schema Alignment & Type Mapping
| Component | `3cluster.spec` | `chron-llm-spec-v0.2.spec` (SOT) | Alignment Status |
|-----------|-----------------|----------------------------------|------------------|
| `Node` | `{ id: Symbol, role: Role }` | `{ id: ID, role: Role, ts: Time }` | **MISMATCH** (`Symbol` → `ID`, missing `ts`) |
| `Edge` | `{ from: Node, to: Node, relation: Relation, strength: Float[0.0, 1.0] }` | `{ from: ID, to: ID, rel: Role, str: Float[0,1], cnt: Int }` | **MISMATCH** (`Node` refs → `ID` refs, `relation`→`rel`, `strength`→`str`, missing `cnt`) |
| `Basin` | `{ attractor: Node[], nodes: Node[] }` | `{ att: Attractor, nodes: ID[], mass: Int, ratio: Float[0,1], cov: Area }` | **MISMATCH** (Structure & field names diverge) |
| `Graph` | `{ nodes: Node[], edges: Edge[] }` | `{ nodes: Node[], edges: Edge[], clusters: Cluster[], meta: Map }` | **EXTENSION** (v0.2 adds `clusters`, `meta`) |

**Resolution:** `3cluster.spec` must adopt `chron-llm-spec-v0.2.spec` type signatures. Field aliases (`strength` → `str`, `relation` → `rel`) and ID-based referencing must be enforced via schema migration scripts.

### SOT Consistency & Temporal Alignment
- `chron-llm-spec-v0.2.spec` explicitly supersedes both `basin.spec` and `chron-llm-r1...v0.1.spec` (similarity > 0.76, relationship: `SUPERSEDED`).
- Temporal drift is confirmed: v0.1 introduced deterministic map abstractions and SCC-based cycle detection; v0.2 evolved these into stochastic trajectory modeling (`Trajectory`, `EventSelection`, `CycleResult`) with stability metrics.
- **Risk:** Concurrent maintenance of v0.1/v0.2 logic will cause behavioral divergence in LLM reasoning trace analysis. Enforcing import-only dependencies from the SOT eliminates this risk.

### Invariant Verification & Conflict Resolution
| Invariant Source | Type | Status | Action |
|------------------|------|--------|--------|
| `3cluster.spec` | Instance-level (`INV \|G.nodes\| = 8`, `INV SCCs(G) = [...]`) | **VALID** (Test Fixture Scope) | Retain as regression assertions. Isolate from global SOT invariants. |
| `basin.spec` | Universal (`INV-PARTITION`, `INV-MASS`, `INV-RATIO`) | **OBSOLETE** | Merge into `chron-llm-spec-v0.2.spec` `Basin` type constraints. |
| `chron-llm-r1...v0.1.spec` | Algorithmic (`INV Graph`, `INV Basin`) | **OBSOLETE** | Integrate into SOT operation pre/post conditions. |
| `chron-llm-spec-v0.2.spec` | Structural/Behavioral (`INV SCC.is_att`, `INV Basin.ratio`, `PRE rollout*`) | **ACTIVE** | Serve as primary verification targets. |

**Conflict Note:** `chron-llm-spec-v0.2.spec` defines `INV Basin.ratio == Basin.mass / len(Graph.nodes)`, while `basin.spec` uses `len(nodes)`. The SOT definition is architecturally correct for global normalization. Update test fixtures to align with SOT normalization logic.

## 3. Actionable Roadmap

### Phase 1: Deprecation & Archival (Week 1)
- [ ] Mark `basin.spec` and `chron-llm-r1-dynamical-analysis-experiment-spec-v0.1.spec` as `@deprecated` in repository metadata.
- [ ] Generate migration guides mapping deprecated operations (`build-basin-map`, `find-cycle`, `rollout*`) to their v0.2 equivalents.
- [ ] Archive files in `/specs/archive/v0.1/` with cross-references to `chron-llm-spec-v0.2.spec`.

### Phase 2: Schema Unification & Refactoring (Week 2)
- [ ] Refactor `3cluster.spec` to remove local type definitions (`Role`, `Node`, `Edge`, `Graph`, `Basin`).
- [ ] Implement explicit imports from `chron-llm-spec-v0.2.spec`.
- [ ] Apply field normalization: `strength` → `str`, `relation` → `rel`, `Symbol` → `ID`, `Node` references → `ID` references.
- [ ] Update concrete instance `G` to conform to v0.2 type signatures (add `ts`, `cnt`, `str` fields where applicable).

### Phase 3: Contract Integration & Validation (Week 3)
- [ ] Merge algorithmic pre/post conditions from deprecated specs into `chron-llm-spec-v0.2.spec` operation definitions.
- [ ] Standardize invariant enforcement:
  - Global invariants → Type-level constraints in SOT.
  - Instance invariants → Unit test assertions in `3cluster.spec`.
- [ ] Run schema diff validation to ensure 100% type compatibility between SOT and test fixture.

### Phase 4: Automation & CI/CD Enforcement (Week 4)
- [ ] Implement AST/Schema validation pipeline (e.g., Zod, JSON Schema, or custom parser) to block local type redeclarations outside `chron-llm-spec-v0.2.spec`.
- [ ] Add CI checks to verify:
  - `INV Basin.ratio` normalization matches SOT.
  - No deprecated files are imported or referenced.
  - `3cluster.spec` instance `G` passes regression against v0.2 type contracts.
- [ ] Generate automated API/IR documentation from `chron-llm-spec-v0.2.spec` to enforce documentation-spec parity.