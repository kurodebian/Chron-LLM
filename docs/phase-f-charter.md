# PHASE F — Semantic Boundary Layer (Normative Charter)

## GOAL

Define the frozen semantic boundary between structural models and runtime integration.
Normalize representations crossing the boundary.
Ensure that semantic inlet selection, event generation, and runtime decisions remain deterministic without mutating authoritative state.


## INPUT

A : History
M : Projection Model
S : Semantic Model (Phase C output)
G : Graph
O : Observation
X : External Representation

## OUTPUT

Normalized Representation
Candidate Event
Runtime Decision
Candidate Event is a non-authoritative proposal.
Authoritative Canonical Event exists only after Commit acceptance.

## CORE CONCEPTS

- A single semantic inlet SHALL be explicitly versioned as the official runtime boundary.
- All representations crossing the boundary SHALL be normalized before further processing.
- Normalization SHALL be deterministic and reproducible.
- Normalized representations MAY produce Candidate Events.
- Candidate Events are non-authoritative until accepted by Commit.
- Runtime decisions are non-authoritative control information.
- Phase F performs no authoritative state mutation.

# NORMALIZATION

## Input Normalization

External representations SHALL be normalized before entering the semantic boundary.

Normalization MAY include:

- Unicode normalization
- whitespace normalization
- punctuation normalization
- control character removal

Formally:

```
normalize_input(raw_input)
│
▼
normalized_input
```

Normalization SHALL be:

- deterministic
- side-effect-free
- reproducible

## Output Normalization

Runtime-generated outputs SHALL be normalized before conversion into Candidate Events.
```
raw_output
    │
    ▼
normalized_output
    │
    ▼
Candidate Event
    │
    ▼
Commit
    │
    ▼
Canonical Event
```
Only Commit may create authoritative state transitions.

# SEMANTIC INLET

The semantic inlet defines the single versioned boundary where normalized representations are converted into boundary-defined structures.

semantic_inlet(version)

The inlet SHALL be:

- explicit
- versioned
- deterministic

No semantic selection SHALL occur outside the frozen inlet.

# RUNTIME DECISION

Observation results MAY be transformed into runtime decisions.
The transformation SHALL be deterministic.

Example:

| Observation | Runtime Decision |
|-------------|------------------|
| normal | commit-request |
| echo | retry-request |
| stagnation | retry-request |
| drift | retry-request |
| discontinuity | abort-request |

Runtime decisions:

- are non-authoritative
- do not mutate state
- require higher-level runtime components for execution

# INVARIANTS

**FINV-1**  
Exactly one semantic inlet version is active.

**FINV-2**  
Input normalization is deterministic.

**FINV-3**  
Output normalization is deterministic.

**FINV-4**  
Candidate Event generation is deterministic.

**FINV-5**  
Runtime decision generation is deterministic.

**FINV-6**  
Phase F does not mutate any authoritative state.

**FINV-7**  
Frozen inlet definition is explicit and versioned.

**FINV-8**  
Semantic selection occurs only within the frozen inlet.

**FINV-9**  
Replacement or modification of the inlet requires a new Phase F version.

**FINV-10**  
Phase F performs no authoritative state mutation.

# SIGMA-4

## F0
```
A
↓
M
↓
S
↓
G
↓
O
```
## C2

```
External Representation
    │
    ▼
Normalization
    │
    ▼
Semantic Inlet
    │
    ▼
Candidate Event
    │
    ▼
Commit
    │
    ▼
Canonical
```
## C3
```
Observation
    │
    ▼
Runtime Decision
    │
    ▼
Runtime Processing
```

# NON-GOALS

- Graph execution
- Observation generation
- History mutation
- Canonical state mutation
- Commit implementation
- Kernel state transitions
- LLM prompting strategy
- Safety policy
- Runtime scheduling
