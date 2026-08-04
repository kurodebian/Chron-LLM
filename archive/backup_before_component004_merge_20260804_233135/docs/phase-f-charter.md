# PHASE F — Boundary Integration Layer (Normative Charter)

## GOAL

Define the frozen boundary between deterministic derived representations and runtime integration.

Normalize representations crossing the boundary.

Ensure that boundary normalization, Candidate Event generation, and runtime decision generation remain deterministic without mutating authoritative state.

## INPUT

```
A : History

M : Projection Model

S : Semantic Model (Phase C output)

G : Graph

O : Observation

X : External Representation
```

## OUTPUT

```
Normalized Representation

Candidate Event

Runtime Decision
```

Candidate Event is a non-authoritative proposal.

Authoritative Canonical Event exists only after Commit acceptance.

## CORE CONCEPTS

- A single boundary inlet SHALL be explicitly versioned as the official runtime boundary.
- All representations crossing the boundary SHALL be normalized before further processing.
- Normalization SHALL be deterministic and reproducible.
- Normalized representations MAY produce Candidate Events.
- Candidate Events are non-authoritative until accepted by Commit.
- Runtime decisions are non-authoritative control information.
- Phase F performs no authoritative state mutation.

# NORMALIZATION

## Input Normalization

External representations SHALL be normalized before entering the boundary inlet.

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

# BOUNDARY INLET

The boundary inlet defines the single versioned interface where normalized representations are converted into runtime boundary structures.

```
boundary_inlet(version)
```

The inlet SHALL be:
- explicit
- versioned
- deterministic

Boundary interpretation SHALL occur only within the frozen inlet.

No authoritative mutation SHALL occur within Phase F.

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

```
**FINV-1**  
Exactly one boundary inlet version is active.

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
Boundary interpretation occurs only within the frozen inlet.

**FINV-9**
Replacement or modification of the inlet requires a new Phase F version.

**FINV-10**
Phase F performs no authoritative state mutation.
```

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
↓
Boundary Inlet
↓
Candidate Event
```

## C2

```
External Representation
    │
    ▼
Normalization
    │
    ▼
Boundary Inlet
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
