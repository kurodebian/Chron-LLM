# IR (Intermediate Representation) Specification v1.0

## 1. Overview

### 1.1 Purpose

`ir` package defines the **Intermediate Representation (IR)** used as the immutable observation record emitted from the runtime callback layer.

IR is a **pure observational data structure**.

Its purpose is:

* capture one decoding event
* preserve runtime emission order
* provide deterministic analysis input
* enable replay and divergence analysis
* separate inference observation from kernel authority

# 2. Architectural Position

## 2.1 Runtime Data Flow

```text
+-----------------------+
|     LLM Backend       |
|    llama.cpp / C++    |
+-----------+-----------+
            |
            |
      token emission
            |
            v
+-----------------------+
|   IR Callback Layer   |
|    ir-callback        |
+-----------+-----------+
            |
            |
            v
+-----------------------+
|          IR           |
| observation record    |
+-----------+-----------+
            |
            |
            v
+-----------------------+
| Analysis / Runtime    |
| divergence / trace    |
+-----------------------+
```

# 3. Package Definition

## 3.1 Package Declaration

```lisp
(defpackage :ir
  (:use :cl)
  (:export
   #:make-ir
   #:ir-p
   #:ir-ctx-id
   #:ir-pos
   #:ir-phase
   #:ir-token
   #:ir-score))
```

# 4. Package Responsibility

## 4.1 Responsible

`ir` provides:

| Responsibility               | Status |
| ---------------------------- | ------ |
| IR object definition         | ✓      |
| IR construction              | ✓      |
| IR type identification       | ✓      |
| Field access                 | ✓      |
| Observation transport format | ✓      |

## 4.2 Non-Responsible

`ir` does not perform:

| Function            | Owner          |
| ------------------- | -------------- |
| Token generation    | LLM Backend    |
| Sampling            | llama.cpp      |
| Interpretation      | Analysis Layer |
| Policy decision     | Kernel         |
| Commit              | Kernel         |
| History persistence | WAL/History    |
| Prompt generation   | Runtime        |

# 5. IR Data Model

## 5.1 Structure Definition

```lisp
(defstruct ir
  ctx-id
  pos
  phase
  token
  score)
```

# 6. IR Object Contract

An IR instance represents:

> A single decoding observation emitted by the runtime at a specific position.

Formal model:

```text
IR =
(
 context-id,
 position,
 phase,
 token,
 score
)
```

# 7. Field Specification

# 7.1 ctx-id

## Definition

```lisp
(ir-ctx-id ir)
```

## Type

Implementation-defined.

Recommended:

```text
integer
uuid
opaque identifier
```

## Purpose

Runtime context identifier.

Identifies the inference execution context producing the observation.

Examples:

```text
ctx-001
ctx-002
```

## Contract

MUST:

* remain stable during one decoding execution
* distinguish independent inference contexts

MUST NOT:

* encode semantic meaning
* represent user/session identity

# 7.2 pos

## Definition

```lisp
(ir-pos ir)
```

## Purpose

Sequential decoding position.

Example:

```text
token0 -> pos 0
token1 -> pos 1
token2 -> pos 2
```

## Contract

`pos` provides deterministic ordering.

Given:

```text
IR-A.pos < IR-B.pos
```

then:

```text
IR-A emitted before IR-B
```

## Importance

This field guarantees:

```
callback emission order
        |
        v
deterministic replay order
```

# 7.3 phase

## Definition

```lisp
(ir-phase ir)
```

## Purpose

Runtime phase identifier.

## Standard Values

| Value | Meaning    |
| ----- | ---------- |
| 0     | Prefill    |
| 1     | Generation |
| 2     | Finalize   |

## Phase Model

```text
Prompt
 |
 v
Prefill
 |
 v
Generation
 |
 v
Finalize
```

## Contract

Phase is observational metadata.

It MUST NOT:

* trigger runtime transition
* control decoding
* affect commit

# 7.4 token

## Definition

```lisp
(ir-token ir)
```

## Purpose

Generated token identifier.

## Type

Implementation-defined.

Typical:

```text
integer token id
```

Example:

```text
token = 198
```

## Contract

Represents:

```
what was emitted
```

Does not represent:

```
what it means
```

# 7.5 score

## Definition

```lisp
(ir-score ir)
```

## Purpose

Token score information.

Examples:

* log probability
* likelihood
* sampler score

## Type

Implementation-defined.

Typical:

```text
float
```

Example:

```text
-0.234
```

## Contract

Score is raw observation only.

IR MUST NOT:

* rank tokens
* select candidates
* perform sampling

# 8. Immutability Model

## Logical Immutability

Although Common Lisp `defstruct` objects are technically mutable, IR has an architectural immutability contract.

Meaning:

After creation:

```text
IR created
   |
   v
fields fixed
   |
   v
analysis only
```

## Mutation Prohibited

Forbidden:

```lisp
(setf (ir-token obj) new-token)
```

after emission.

# 9. Deterministic Replay Contract

IR supports replay through ordered observation.

Input:

```text
IR Stream
```

Example:

```text
[
 IR(pos=0 token=100),
 IR(pos=1 token=101),
 IR(pos=2 token=102)
]
```

Replay:

```text
sort by pos

↓

process sequentially
```

Result:

same observation sequence.

# 10. IR Stream Model

Multiple IR objects form an observation stream.

```text
IR Stream

[
 IR0,
 IR1,
 IR2,
 ...
]
```

Properties:

| Property           | Guarantee |
| ------------------ | --------- |
| Ordering           | pos       |
| Context separation | ctx-id    |
| Phase tracking     | phase     |
| Token record       | token     |
| Score capture      | score     |

# 11. Relationship With Kernel

## Authority Boundary

```text
              IR

              |
              |
       Observation Only

              |
              v

          Kernel

              |
              |
       Review / Commit
```

IR cannot:

* modify state
* create events
* commit history
* alter worldline

# 12. Relationship With History/WAL

## Storage Policy

IR itself is not Truth.

Architecture:

```text
IR
 |
 v
Analysis
 |
 v
Proposal
 |
 v
Commit
 |
 v
History/WAL
```

Truth:

```
History/WAL
```

Not:

```
IR
```

# 13. Replay and Analysis Usage

Possible consumers:

| Consumer            | Usage                    |
| ------------------- | ------------------------ |
| divergence analyzer | compare decode paths     |
| trace analyzer      | reconstruct emission     |
| benchmark           | measure runtime behavior |
| evaluator           | score observation        |
| debugging           | inspect callbacks        |

# 14. API Specification

## Constructor

```lisp
(make-ir
 :ctx-id ...
 :pos ...
 :phase ...
 :token ...
 :score ...)
```

Creates one observation record.

## Predicate

```lisp
(ir-p object)
```

Returns:

```text
true
```

if object is IR.

## Accessors

```lisp
(ir-ctx-id x)

(ir-pos x)

(ir-phase x)

(ir-token x)

(ir-score x)
```

# 15. Formal Invariants

## IR-1 Observation Purity

IR MUST represent observation only.

```
IR ∉ Runtime State
```

## IR-2 No Semantic Layer

IR MUST NOT contain:

```
meaning
intent
decision
policy
```

## IR-3 Ordering Preservation

IR MUST preserve:

```
callback emission order
```

through:

```
pos
```

## IR-4 Replay Compatibility

Given identical IR stream:

```
same analysis result
```

must be obtainable.

# 16. Chron-LLM Mapping

Current architecture:

```text
LLM
 |
 | token emission
 v
IR Callback

 |
 v

IR

 |
 v

Observation

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

# 17. Design Evaluation

## Current Status

**IR Minimal Observation ABIとして成立**

Strengths:

* very small state surface
* deterministic replay possible
* LLM independence
* analysis isolation
* kernel authority preserved

## Future Extension Candidates

追加する場合は慎重に分離する。

Possible:

```text
timestamp
sampler-id
temperature
top-k
top-p
backend-version
```

ただし:

```
Observation metadata
```

としてのみ追加する。

禁止:

```
semantic interpretation
policy result
commit information
```

# Final Specification Summary

```text
IR is an immutable observational record emitted by the runtime callback.

IR records:
    context
    order
    phase
    token
    score

IR does not:
    decide
    interpret
    mutate
    commit

IR exists only to connect:
    Non-deterministic LLM execution

to:

    Deterministic Kernel analysis pipeline
```

このIR定義は、Chron-LLM設計における **「LLMの非決定性をKernelが観測可能な形式へ変換する最小ABI」** として整合しています。
