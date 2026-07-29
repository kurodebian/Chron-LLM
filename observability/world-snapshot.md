# Package Specification: chron-r2-0-c

## Purpose
Defines a data-only boundary for snapshotting domain entities (Worlds, Registries) into immutable observation structures. Ensures all stored fields contain only primitive values suitable for serialization or external consumption. Provides APIs to construct these observations from domain objects and compute structural diffs between them.

Relies on package `chron-r2-0-a` for underlying domain types (`world-p`, `world-registry-p`, etc.).

## Constants & Invariants

### Schema Version
- **Symbol**: `+observation-schema-version+`
- **Value**: `1`
- All observation structures embed this version as their first slot.

### Primitive Tree Invariant
Observation fields must contain only "primitive trees" to guarantee serializability and immutability:
- **Primitive Leaf**: `null`, `t`, string, number, character, or keyword.
- **Primitive Tree**: A primitive leaf, or a cons cell where both car and cdr are primitive trees.
- **Enforcement**: Builders validate inputs via `%require-primitive-tree`. Accessors deep-copy strings and lists (`%copy-primitive-tree`) on retrieval to prevent external mutation of internal state.

## Observation Structures

All observations are implemented as fixed-length vectors with read-only slots. Internal constructors are prefixed with `%make-`; public construction is handled by `build-*` functions.

### World Observation
Represents a snapshot of a single world's structural metadata.
- **Type Predicate**: `world-observation-p` (checks vector length 8 and schema version)
- **Equality**: `world-observation-equal`
- **Fields & Accessors**:
  - `schema-version`: Integer (read-only, no copy)
  - `world-id`: Primitive tree
  - `root-node-id`: Primitive tree
  - `head-node-id`: Primitive tree
  - `projection-policy`: Primitive tree
  - `metadata`: Primitive tree
  - `lifecycle`: Value (read-only, no copy)
  - `parent-world-id`: Primitive tree

### Registry Observation
Represents a snapshot of the world registry's state.
- **Type Predicate**: `registry-observation-p` (checks vector length 4 and schema version)
- **Equality**: `registry-observation-equal`
- **Fields & Accessors**:
  - `schema-version`: Integer
  - `world-ids`: Primitive tree (list of world IDs)
  - `active-world-id`: Primitive tree
  - `archived-world-ids`: Primitive tree (list of archived world IDs)

### Ancestry Observation
Represents the lineage relationship for a specific world.
- **Type Predicate**: `ancestry-observation-p` (checks vector length 4 and schema version)
- **Equality**: `ancestry-observation-equal`
- **Fields & Accessors**:
  - `schema-version`: Integer
  - `world-id`: Primitive tree
  - `parent-world-id`: Primitive tree
  - `ancestry-path`: Primitive tree (list starting with world-id, followed by parent)

### Diff Observation
Represents the result of comparing two observations.
- **Type Predicate**: `diff-observation-p` (checks vector length 3 and schema version)
- **Equality**: `diff-observation-equal`
- **Fields & Accessors**:
  - `schema-version`: Integer
  - `changed-p`: Boolean
  - `changed-fields`: Primitive tree (list of symbols indicating differing fields, or `(:type)` on type mismatch)

## Public API: Builders

Constructs observation structures from domain objects. Validates inputs and enforces the primitive tree invariant.

### build-world-observation
```lisp
(build-world-observation world &key parent-world-id)
```
- **Parameters**:
  - `world`: Must satisfy `world-p`.
  - `parent-world-id` (optional): Primitive tree value for lineage tracking.
- **Behavior**: Extracts structural fields from the domain world object using internal accessors (`world-id`, `world-root-node`, etc.). Errors if `world` is invalid.

### build-registry-observation
```lisp
(build-registry-observation registry)
```
- **Parameters**:
  - `registry`: Must satisfy `world-registry-p`.
- **Behavior**: 
  - Collects all world IDs via `(list-worlds registry)`.
  - Identifies active world ID via `(active-world registry)`.
  - Filters archived worlds by checking if `(world-lifecycle world)` equals `:archived`.
  - Errors if `registry` is invalid.

### build-ancestry-observation
```lisp
(build-ancestry-observation registry world-id)
```
- **Parameters**:
  - `registry`: Must satisfy `world-registry-p`.
  - `world-id`: Identifier to look up.
- **Behavior**: 
  - Queries internal ancestry map (`chron-r2-0-a::world-registry-ancestry`).
  - Errors if no parent entry exists for the given world ID.
  - Constructs `ancestry-path` as `(cons world-id parent-world-id)`.

### build-diff-observation
```lisp
(build-diff-observation left right)
```
- **Parameters**: Two observation structures.
- **Behavior**: 
  - Dispatches based on the type of both arguments:
    - If both are `world-observation`: compares all world fields.
    - If both are `registry-observation`: compares registry fields.
    - If both are `ancestry-observation`: compares ancestry fields.
    - If types match but are not recognized observation pairs: returns no changes.
    - If types differ: sets `changed-p` to true and `changed-fields` to `(:type)`.
  - Returns a new `diff-observation` containing the list of differing field symbols.

## Public API: Describers

Convenience aliases that delegate directly to the corresponding builder functions.

| Function | Delegates To | Purpose |
|----------|--------------|---------|
| `describe-world` | `build-world-observation` | Snapshot a world entity. |
| `describe-registry` | `build-registry-observation` | Snapshot registry state. |
| `describe-ancestry` | `build-ancestry-observation` | Snapshot lineage for a world ID. |
| `describe-diff` | `build-diff-observation` | Compute diff between two observations. |

## Implementation Notes
- **Immutability**: Observations are vectors with read-only slots. Accessors return deep-copies of mutable primitive trees to prevent aliasing issues.
- **Data Boundary**: Builders accept only primitive snapshot values or domain objects; they do not expose internal world/registry mutation capabilities.
- **Error Handling**: All builders signal errors if required preconditions (type checks, existence checks) are violated.