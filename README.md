# Chron-LLM

Deterministic runtime architecture for integrating non-deterministic reasoning components into a causal execution model.

# Specification Status

## Frozen Architecture

Chron-LLM follows a frozen specification model.

Frozen specifications define:

- architectural boundaries
- authority rules
- causal guarantees
- layer responsibilities

Implementation details MAY evolve within these boundaries.

Changes to frozen specifications require a new specification version.

# Frozen Specifications

## Constitution Layer

| Specification | Status | Responsibility |
|---|---|---|
| Agent Causality Constitution | Frozen | Defines authority, causality, and mutation rules |

# Phase Architecture

The system is organized as a deterministic transformation pipeline.

```
History
|
v
Projection Model
|
v
Semantic Model
|
v
Graph Structure
|
v
Observation
|
v
Semantic Boundary
|
v
Candidate Event
|
v
Commit
|
v
Canonical State
```

# Phase Specifications

## Phase A — History Layer

**Status:** Frozen

### Responsibility

Defines the canonical history representation.

### Guarantees

- History represents causal facts.
- History is authoritative within Canonical state.
- History is append-only.
- History contains no interpretation semantics.

## Phase B — Projection Model Layer

**Status:** Frozen

### Responsibility

Derives deterministic projection models from history.

### Guarantees

- Projection is deterministic.
- Projection does not mutate history.
- Projection is derived state.

## Phase C — Semantic Model Layer

**Status:** Frozen

### Responsibility

Constructs deterministic semantic representations.

### Guarantees

- Semantic Model is derived from previous layers.
- Semantic Model is not authoritative.
- Semantic representation does not directly mutate Canonical state.

## Phase D — Graph Structure Layer

**Status:** Frozen

### Responsibility

Constructs deterministic structural graphs.

### Input

```
S : Semantic Model
```

### Output

```
G = graph(S)
```

### Guarantees

- Graph construction is deterministic.
- Nodes preserve identity consistency.
- Edges represent structural relations only.
- Graph contains no interpretation layer.
- Graph does not introduce authoritative information.

## Phase E — Observation Layer

**Status:** Frozen  
**Version:** R0

### Responsibility

Observe structural properties of graphs without committing to semantics.

### Input

```
G : Structural Graph
```

Structural Graph contains:

- structural relations
- identity references
- measurable properties

Structural Graph contains no authoritative semantic interpretation.

### Output

```
O = Observation(G)
```

### Guarantees

Observation:

- does not select semantic interpretations
- does not resolve semantic ambiguity
- does not normalize semantics
- does not modify graphs
- does not perform execution
- does not mutate runtime state

### Runtime Specialization

Runtime-specific detectors MAY specialize Observation.

Examples:

- Echo detection
- Stagnation detection
- Drift detection
- Discontinuity detection

Observation outputs are informational only.

Runtime decisions are produced outside Phase E.

## Phase F — Semantic Boundary Layer

**Status:** Frozen  
**Version:** R0

### Responsibility

Defines the frozen semantic boundary between structural models and runtime integration.

### Input

```
A : History
M : Projection Model
S : Semantic Model
G : Graph
O : Observation
X : External Representation
```

### Output

```
Normalized Representation
Candidate Event
Runtime Decision
```

### Guarantees

- Exactly one semantic inlet version exists.
- All boundary-crossing representations are normalized.
- Normalization is deterministic.
- Candidate Events are non-authoritative.
- Runtime Decisions are non-authoritative.
- Phase F performs no Canonical mutation.

# Authority Model

Only Commit may create authoritative state transitions.

```
External Representation
|
v
Normalization
|
v
Semantic Boundary
|
v
Candidate Event
|
v
Commit
|
v
Canonical Event
|
v
Canonical State
```

# Frozen Boundary Rules

The following rules are immutable:

- Canonical state is authoritative.
- Only Commit may mutate Canonical state.
- History records causal facts.
- Projection is deterministic.
- Semantic Model is derived.
- Graph contains structure only.
- Observation does not select meaning.
- Semantic selection occurs only inside the frozen inlet.
- Candidate Events are non-authoritative.
- Runtime decisions do not directly mutate state.

# Repository Structure

```
Chron-LLM/
│
├── docs/
│   ├── constitution/
│   ├── phase-a/
│   ├── phase-b/
│   ├── phase-c/
│   ├── phase-d/
│   ├── phase-e/
│   └── phase-f/
│
├── kernel/
│   ├── canonical
│   ├── commit
│   ├── wal
│   └── state
│
├── graph-runtime/
│   ├── graph
│   ├── projection
│   ├── causal
│   └── traversal
│
├── runtime/
│   ├── r0/
│   └── ir/
│
├── llama-agent/
│
└── experiments/
```

# Directory Responsibilities

| Directory | Responsibility |
|---|---|
| docs/ | Normative specifications |
| kernel/ | Canonical authority and state transition enforcement |
| graph-runtime/ | Graph construction and structural runtime |
| runtime/ | Runtime execution layers |
| llama-agent/ | LLM integration components |
| experiments/ | Non-authoritative experiments |

# Development Rule

Implementation MUST preserve frozen specification boundaries.

New functionality MUST be introduced by:

1. extending non-frozen implementation layers, or
2. introducing a new specification version.

Frozen architecture MUST NOT be modified implicitly.

