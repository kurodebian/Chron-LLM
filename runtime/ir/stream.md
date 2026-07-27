# IR Stream Specification v1.0

## 1. Overview

### 1.1 Purpose

`ir-stream` package provides an in-memory collection layer for IR (Intermediate Representation) observations emitted from the runtime callback pipeline.

The module acts as a **temporary observation buffer** between:

* runtime callback emission
* IR analysis layer
* divergence / trace / replay tooling

It stores ordered IR objects during one decoding execution.

# 2. Architectural Position

## 2.1 Data Flow

```text
+-------------------------+
|      LLM Backend        |
|    llama.cpp / C++      |
+------------+------------+
             |
             |
       token callback
             |
             v
+-------------------------+
|      ir-callback        |
+------------+------------+
             |
             |
             v
+-------------------------+
|          IR             |
|  immutable observation  |
+------------+------------+
             |
             |
             v
+-------------------------+
|       ir-stream         |
| temporary IR buffer     |
+------------+------------+
             |
             |
             v
+-------------------------+
|   Analysis Layer        |
| trace/divergence/replay |
+-------------------------+
```

# 3. Package Definition

## 3.1 Package Declaration

```lisp
(defpackage :ir-stream
  (:use :cl
        :ir)
  (:export
   #:*ir-stream*
   #:push-ir
   #:clear-ir-stream))
```

# 4. Package Responsibility

## 4.1 Responsibilities

`ir-stream` provides:

| Function                   | Purpose                            |
| -------------------------- | ---------------------------------- |
| IR observation buffering   | Store emitted IR objects           |
| Order preservation         | Maintain callback arrival sequence |
| Run isolation              | Clear state between executions     |
| Analysis input preparation | Provide deterministic stream       |

## 4.2 Non-Responsibilities

`ir-stream` does not perform:

| Function                | Owner            |
| ----------------------- | ---------------- |
| IR generation           | Runtime callback |
| Token decoding          | LLM backend      |
| Semantic interpretation | Analysis         |
| Proposal generation     | Kernel           |
| Commit                  | Kernel           |
| Persistence             | WAL/History      |
| Policy decisions        | Runtime          |

# 5. Core Data Structure

## 5.1 Stream Definition

```lisp
(defparameter *ir-stream*
  (make-array 0
              :adjustable t
              :fill-pointer 0))
```

## 5.2 Internal Representation

The stream is an adjustable Common Lisp vector.

Logical model:

```text
IR Stream =
[
  IR(0),
  IR(1),
  IR(2),
  ...
]
```

# 6. Stream Properties

## 6.1 Ordering Guarantee

IR insertion order is preserved.

Example:

```text
callback sequence:

IR-A
IR-B
IR-C


stream:

[
 IR-A,
 IR-B,
 IR-C
]
```

## 6.2 Deterministic Analysis

Given identical callback emission:

```text
Input:

IR sequence A


Analysis Result:

Result A
```

The stream provides stable ordering for replay and comparison.

## 6.3 Non-Authoritative State

The stream is temporary runtime state.

Authority model:

```text
+----------------+
| History / WAL  |
|    Truth       |
+----------------+

        ▲

        |

+----------------+
| ir-stream      |
| Observation    |
+----------------+
```

`*ir-stream*` is never the source of truth.

# 7. Global Stream Variable

## 7.1 Symbol

```lisp
*ir-stream*
```

## 7.2 Purpose

Stores IR observations belonging to the current decoding execution.

## 7.3 Lifetime

Lifecycle:

```text
create

↓

decode start

↓

push IR events

↓

analysis

↓

clear

↓

next run
```

# 8. API Specification

# 8.1 push-ir

## Definition

```lisp
(defun push-ir (ir)
  (vector-push-extend ir *ir-stream*)
  ir)
```

## Purpose

Append one IR observation to the active stream.

## Signature

```lisp
(push-ir ir-object)
```

## Input

### ir

Expected:

```lisp
(ir-p ir)
```

must return:

```text
T
```

## Processing

Algorithm:

```text
receive IR

↓

append to vector

↓

return same IR
```

## Return Value

Returns the inserted IR object.

Example:

```lisp
(let ((x (make-ir ...)))
  (eq x
      (push-ir x)))
```

Result:

```text
T
```

## Ordering Contract

If:

```text
push-ir(A)
push-ir(B)
push-ir(C)
```

then:

```text
stream =
[
 A,
 B,
 C
]
```

# 8.2 clear-ir-stream

## Definition

```lisp
(defun clear-ir-stream ()
  (setf *ir-stream*
        (make-array 0
                    :adjustable t
                    :fill-pointer 0))

  *ir-stream*)
```

## Purpose

Reset observation buffer before a new decoding run.

## Operation

Before:

```text
*ir-stream*

[
 IR1,
 IR2,
 IR3
]
```

After:

```text
*ir-stream*

[
]
```

## Return Value

Returns the newly created empty stream.

# 9. Execution Lifecycle

## 9.1 Single Generation Run

```text
clear-ir-stream

        |
        v

LLM decode start

        |
        v

callback emits token

        |
        v

make-ir

        |
        v

push-ir

        |
        v

repeat

        |
        v

analysis

        |
        v

clear-ir-stream
```

# 10. Deterministic Replay Model

The stream provides:

```text
Ordered IR Collection
```

not:

```text
State Snapshot
```

Replay:

```text
IR Stream

[
 IR(pos=0),
 IR(pos=1),
 IR(pos=2)
]

        |

        v

Sequential processing

        |

        v

Same observation order
```

# 11. Relationship With IR

## IR Layer

Role:

```text
Single observation
```

Example:

```text
IR
{
 token=123
 pos=5
 phase=1
}
```

## IR Stream Layer

Role:

```text
Collection of observations
```

Example:

```text
[
 IR0,
 IR1,
 IR2
]
```

Relationship:

```text
One IR
    |
    v
IR Stream
    |
    v
Analysis
```

# 12. Relationship With Kernel

## Boundary

```text
LLM

 |
 v

IR

 |
 v

IR Stream

 |
 v

Analysis

 |
 v

Proposal

 |
 v

Review

 |
 v

Commit

 |
 v

History
```

`ir-stream` has:

```text
Observation authority: YES

State mutation authority: NO

Commit authority: NO
```

# 13. Memory Model

## Current Implementation

Storage:

```text
RAM only
```

Persistence:

```text
NONE
```

## Memory Lifetime

Bounded by:

```text
one decoding run
```

## Explicit Reset Requirement

The caller must execute:

```lisp
(clear-ir-stream)
```

between runs.

# 14. Threading Considerations

## Current Status

Not thread-safe.

Reason:

```lisp
*ir-stream*
```

is a global mutable vector.

Potential future design:

```text
Thread
 |
 v
Context-local IR Stream
```

Example:

```lisp
dynamic binding

*ir-stream*
```

or:

```text
ctx-id → stream
```

# 15. Error Conditions

## 15.1 Invalid IR Object

Input:

```lisp
(push-ir "not-ir")
```

Current behavior:

```text
accepted
```

because no type validation exists.

Recommended future:

```lisp
(assert (ir-p ir))
```

before insertion.

## 15.2 Accidental Cross-run Contamination

Cause:

```text
missing clear-ir-stream
```

Result:

```text
previous run observations mixed
```

# 16. Formal Invariants

## IR-S1 Ordering

For all:

```text
push-ir(A)
before
push-ir(B)
```

then:

```text
position(A) < position(B)
```

in stream.

## IR-S2 Ephemeral State

`ir-stream` MUST NOT become authoritative storage.

## IR-S3 Semantic Neutrality

Stream MUST NOT:

* classify IR
* interpret tokens
* alter observations

## IR-S4 Run Isolation

Each decoding execution SHOULD start with:

```lisp
clear-ir-stream
```

# 17. Chron-LLM Mapping

Current architecture:

```text
          LLM
           |
           |
    token emission
           |
           v

      ir-callback

           |
           v

          IR

           |
           v

      ir-stream

           |
           v

   divergence-analysis
   trace-analysis

           |
           v

       Proposal

           |
           v

       Review

           |
           v

       Commit

           |
           v

       History/WAL
```

# 18. Design Assessment

## Current Status

**Minimal IR Observation Bufferとして成立**

Advantages:

* implementation simplicity
* deterministic ordering
* low overhead
* clear authority separation
* replay-friendly

## Important Future Improvements

### P0: Type Validation

追加:

```lisp
(assert (ir-p ir))
```

### P1: Context Isolation

現在:

```text
global stream
```

将来:

```text
ctx-id → stream
```

### P2: Stream Snapshot API

追加候補:

```lisp
(snapshot-ir-stream)
```

目的:

* immutable analysis input
* replay archive
* divergence comparison

# Final Specification Summary

```text
ir-stream is a temporary ordered observation buffer.

It stores:
    IR objects emitted during one runtime execution.

It guarantees:
    insertion order
    deterministic analysis input
    semantic neutrality

It does not:
    interpret
    decide
    persist
    commit

Truth remains:
    History/WAL

IR Stream remains:
    observational workspace only
```

この実装は、Chron-LLMの設計原則である

**「LLMの非決定的実行 → 観測(IR) → 決定論的Kernel処理」**

における、観測ストリーム層として正しく分離されています。
