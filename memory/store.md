# Module Specification: chron-r2-0-a

## 1. Overview
The `chron-r2-0-a` package provides a foundation for content-addressable storage, causal graph structures, and world runtime management. It implements explicit memory stores (no global caches) to ensure reproducible content addressing via SHA-256 hashing of UTF-8 encoded data.

## 2. Public API
The following symbols are exported by the package `chron-r2-0-a`. Note that while many are defined in this module, others represent interfaces or types implemented elsewhere but exposed here.

### Content Addressing & Storage
*   **Types**: `payload-ref`, `payload-ref-p`
*   **Constructors**: `make-payload-ref`
*   **Accessors**: `payload-ref-hash`, `payload-ref-type`, `payload-ref-size`, `payload-ref-storage`
*   **Store Operations**: `make-memory-store`, `store-payload`, `load-payload`, `payload-exists-p`

### Causal Graph & Context (Interface)
*   **Nodes/Edges**: `causal-node`, `causal-edge`, `context-node`
*   **Graphs**: `causal-graph`, `causal-subgraph`
*   **Operations**: `add-node!`, `add-edge!`, `get-node`, `associated-evaluations`

### World Runtime (Interface)
*   **Types**: `world`, `world-registry`
*   **Operations**: `fork-world`, `replace-world-metadata!`, `kernel-commit-world!`, `replay-world`, `register-world`, `find-world`, `active-world`, `set-active-world`, `list-worlds`, `archive-world`

### Utilities
*   `prefill-state`, `canonical-prompt`, `sha256-string`

---

## 3. Data Structures

### Payload Reference (`payload-ref`)
A structure representing a reference to stored content. All fields are read-only after construction.

**Constructor**: `(make-payload-ref hash type size storage)`

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `hash` | String | `""` | The SHA-256 content address. |
| `type` | Keyword | `:text` | Content type identifier. |
| `size` | Integer (≥0) | `0` | Size in bytes of the UTF-8 encoded content. |
| `storage` | Keyword | `:memory` | Storage backend identifier. |

---

## 4. Functions & Procedures

### 4.1 Storage Management

#### `make-memory-store`
Creates an explicit, isolated storage container.
*   **Returns**: A hash table with test function `equal`.
*   **Invariant**: The store is not a global singleton; it must be passed explicitly to operations.

### 4.2 Payload Operations

#### `store-payload`
Stores content in the provided store and returns a reference.
*   **Signature**: `(store-payload store content &key (type :text) (storage :memory))`
*   **Parameters**:
    *   `store`: The hash table returned by `make-memory-store`.
    *   `content`: Any Lisp object (string or printable).
    *   `type`: Keyword specifying payload type.
    *   `storage`: Keyword specifying storage backend.
*   **Logic**:
    1.  Converts `content` to a string using `%content-string` (identity if string, otherwise `prin1-to-string`).
    2.  Computes SHA-256 hash of the UTF-8 bytes of the string.
    3.  If the hash does not exist in `store`, inserts it mapping hash -> text.
    4.  Returns a new `payload-ref` with the computed hash, type, byte size, and storage location.

#### `load-payload`
Retrieves content from the store using a reference or raw hash string.
*   **Signature**: `(load-payload store reference)`
*   **Parameters**:
    *   `store`: The memory store.
    *   `reference`: A `payload-ref` object or a hash string.
*   **Returns**: The stored content (string) or `nil` if not found.

#### `payload-exists-p`
Checks for the existence of a payload in the store.
*   **Signature**: `(payload-exists-p store reference)`
*   **Parameters**: Same as `load-payload`.
*   **Returns**: Boolean (`t` or `nil`).

### 4.3 Cryptographic Utilities

#### `sha256-string`
Computes the canonical SHA-256 hexadecimal address for a string's UTF-8 bytes.
*   **Signature**: `(sha256-string string)`
*   **Returns**: A string formatted as `"sha256:XXXXXXXX..."`.
*   **Control Flow**:
    1.  Encodes input string to UTF-8 octets (`utf8-octets`).
    2.  Pads the bit stream according to SHA-256 specification (append `0x80`, zeros, and length).
    3.  Processes data in 512-bit blocks using standard compression functions (utilizing constants `+sha256-k+` and bitwise rotation helpers `%ror`).
    4.  Formats the resulting hash vector into a hexadecimal string.

#### `utf8-octets`
Internal helper to convert a Lisp string to an array of unsigned bytes representing UTF-8 encoding.
*   **Signature**: `(utf8-octets string)`
*   **Returns**: Adjustable vector of `(unsigned-byte 8)`.

### 4.4 Internal Helpers

#### `%content-string`
Normalizes arbitrary content into a string representation for hashing.
*   **Logic**: Returns input as-is if it is a string; otherwise, uses `prin1-to-string` with standard IO syntax.