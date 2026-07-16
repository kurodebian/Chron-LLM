# Causal Graph Core Data Model Specification v1.0

## Chron-R2.0-A Graph Runtime Core

---

# 1. Overview

## 1.1 Purpose

本モジュールは Chron-R2.0-A における **Causal Graph Runtime Core のデータモデル層**を定義する。

責務:

* 因果 Node 表現
* 因果 Edge 表現
* 因果 Graph コンテナ
* Node lookup
* Node 登録
* Edge 登録
* Graph integrity 保証

を提供する。

---

# 2. Architectural Position

```text
              History / WAL

                    |
                    |
                    v

             Causal Event

                    |
                    v

          +----------------+
          | Causal Graph   |
          +----------------+

             /          \

            v            v

        causal-node   causal-edge


                    |
                    v

          causal-subgraph

                    |
                    v

            Replay / Analysis
```

---

# 3. Design Principle

Chron-R2.0-A において:

```text
Truth = History/WAL
```

である。

Causal Graph は:

```text
History の構造化 Projection
```

として存在する。

つまり:

```text
History

↓

Causal Graph

↓

Analysis
```

の関係になる。

---

# 4. Package Context

```lisp
(in-package :chron-r2-0-a)
```

本コードは Graph Runtime Core namespace に属する。

---

# 5. Data Model

全体構造:

```text
Causal Graph

{
 nodes : List<CausalNode>
 edges : List<CausalEdge>
}
```

---

# 6. causal-node Specification

## 6.1 Definition

```lisp
(defstruct
    (causal-node
      (:constructor make-causal-node
          (id type payload-ref &optional metadata)))

  id
  type
  payload-ref
  metadata)
```

---

# 7. Node Logical Model

```text
CausalNode =
{
    id,
    type,
    payload-reference,
    metadata
}
```

---

# 8. Field Specification

---

## 8.1 id

Definition:

```lisp
(id nil :read-only t)
```

---

Purpose:

Node identity.

Constraint:

```text
unique inside graph
```

---

Example:

```lisp
:event-001
```

---

Used by:

```lisp
(get-node graph id)
```

---

# 8.2 type

Definition:

```lisp
(type nil
 :type keyword
 :read-only t)
```

---

Purpose:

Node classification.

Examples:

```lisp
:event
:commit
:state
:proposal
```

---

Constraint:

Keyword only.

---

# 8.3 payload-ref

Definition:

```lisp
(payload-ref nil
 :type payload-ref
 :read-only t)
```

---

Purpose:

External payload reference.

Important:

Node itself does not contain payload.

Architecture:

```text
Node

 |
 v

Payload Reference

 |
 v

History/WAL Payload
```

---

Meaning:

Causal Graph:

```text
structure holder
```

not:

```text
data storage
```

---

# 8.4 metadata

Definition:

```lisp
(metadata nil
 :read-only t)
```

---

Purpose:

Non-authoritative auxiliary information.

Examples:

```text
timestamp

debug info

annotations
```

---

Constraint:

Metadata cannot determine causal truth.

---

# 9. causal-edge Specification

## 9.1 Definition

```lisp
(defstruct
    (causal-edge
      (:constructor make-causal-edge
          (from to type)))

  from
  to
  type)
```

---

# 10. Edge Logical Model

```text
CausalEdge =
{
    source-node,
    destination-node,
    relation-type
}
```

---

# 11. Field Specification

---

## 11.1 from

Source node id.

```lisp
(from nil :read-only t)
```

Meaning:

Cause side.

---

Example:

```text
Proposal
   |
   v
Commit
```

from:

```text
Proposal
```

---

# 11.2 to

Destination node id.

```lisp
(to nil :read-only t)
```

Meaning:

Effect side.

---

Example:

```text
Proposal → Commit
```

to:

```text
Commit
```

---

# 11.3 type

```lisp
(type nil
 :type keyword
 :read-only t)
```

---

Purpose:

Edge classification.

Current intended:

```lisp
:causal
```

---

Important:

Graph may contain future relations:

```lisp
:reference

:temporal

:semantic
```

but:

`causal-subgraph`

uses only:

```lisp
:causal
```

---

# 12. causal-graph Specification

## 12.1 Definition

```lisp
(defstruct
    (causal-graph
      (:constructor make-causal-graph
          (&key (nodes nil)
                (edges nil))))

  nodes
  edges)
```

---

# 13. Graph Model

```text
CausalGraph

    nodes
      |
      +-- causal-node


    edges
      |
      +-- causal-edge
```

---

# 14. Graph Invariants

---

## GRAPH-1 Node Identity

Every node id must be unique.

---

Violation:

```text
node A
node A
```

is forbidden.

---

## GRAPH-2 Edge Endpoint Validity

Every edge endpoint must exist.

Valid:

```text
A → B

where:

A ∈ Nodes
B ∈ Nodes
```

---

Invalid:

```text
A → X

X not in graph
```

---

## GRAPH-3 Immutability Boundary

Node fields:

```lisp
:read-only t
```

Edge fields:

```lisp
:read-only t
```

---

Meaning:

Once committed:

```text
identity cannot change
```

---

# 15. get-node Specification

## Definition

```lisp
(defun get-node (graph id)
```

---

## Purpose

Graph内からNodeを検索する。

---

Implementation:

```lisp
(find id
      (causal-graph-nodes graph)
      :key #'causal-node-id
      :test #'equal)
```

---

# 16. Search Contract

Input:

```text
graph
node-id
```

Output:

```text
causal-node
```

or:

```text
nil
```

---

Example:

```lisp
(get-node graph :node-1)
```

returns:

```text
#<CAUSAL-NODE>
```

---

# 17. add-node! Specification

## Definition

```lisp
(defun add-node! (graph node)
```

---

## Purpose

Graphへ新規Nodeを追加する。

---

# 18. Validation

## Step 1

Type check:

```lisp
(causal-node-p node)
```

---

Invalid:

```text
anything else
```

↓

Error

---

## Step 2

Duplicate check:

```lisp
(get-node graph node-id)
```

---

Existing:

```text
same id
```

↓

Error

---

## Step 3

Append

```lisp
(setf nodes ...)
```

---

# 19. Return Contract

成功:

```lisp
graph
```

自身を返す。

---

Usage:

```lisp
(add-node!
 graph
 node)
```

---

# 20. add-edge! Specification

## Definition

```lisp
(defun add-edge! (graph edge)
```

---

## Purpose

GraphへEdgeを追加する。

---

# 21. Validation

## Step 1

Edge type check:

```lisp
(causal-edge-p edge)
```

---

## Step 2

Endpoint validation

```lisp
(get-node graph from)

(get-node graph to)
```

---

Both required.

---

Invalid:

```text
A → Unknown
```

↓

Error

---

# 22. Edge Registration

Append:

```lisp
(causal-graph-edges graph)
```

---

Return:

```text
graph
```

---

# 23. Example Construction

```lisp
(let ((g (make-causal-graph)))

  (add-node!
   g
   (make-causal-node
    :proposal
    :proposal
    'payload-1))

  (add-node!
   g
   (make-causal-node
    :commit
    :commit
    'payload-2))

  (add-edge!
   g
   (make-causal-edge
    :proposal
    :commit
    :causal))

  g)
```

---

Result:

```text
proposal

   |
   | :causal
   v

commit
```

---

# 24. Relationship With causal-subgraph

Data:

```text
causal-node

+

causal-edge
```

↓

Projection:

```lisp
causal-subgraph
```

↓

Output:

```text
ancestor chain
```

---

Example:

Graph:

```text
A → B → C
```

Call:

```lisp
(causal-subgraph g 'C)
```

Result:

```text
(A B C)
```

---

# 25. Chron-OS Mapping

| Causal Graph | Chron-OS Concept           |
| ------------ | -------------------------- |
| causal-node  | Committed state/event node |
| causal-edge  | Causal transition          |
| payload-ref  | WAL reference              |
| metadata     | Observation metadata       |
| graph        | World causal projection    |

---

# 26. Determinism Contract

Given:

```text
same WAL

same commits
```

then:

```text
same causal graph
```

must be generated.

---

# 27. Persistence Relationship

Important:

この構造体自身は persistence を持たない。

正しい方向:

```text
WAL

 ↓

Graph rebuild

 ↓

CausalGraph
```

ではなく:

```text
WAL

 ↓

CausalGraph projection

 ↓

Analysis
```

---

# 28. Complexity

## get-node

Current:

[
O(N)
]

---

## add-node!

Duplicate search:

[
O(N)
]

---

## add-edge!

Endpoint validation:

[
O(2N)
]

---

# 29. Optimization Candidates

## Node Index

現在:

```text
List
```

将来:

```text
HashTable

id → node
```

---

改善:

```text
get-node

O(N)

↓

O(1)
```

---

# 30. Formal Invariants Summary

## NODE-1

Node IDs unique.

---

## NODE-2

Node identity immutable.

---

## EDGE-1

Edge endpoints must exist.

---

## EDGE-2

Edge relation immutable.

---

## GRAPH-1

Graph is valid only when:

```text
∀ edge:

from ∈ nodes

and

to ∈ nodes
```

---

# Final Specification Summary

```text
Chron-R2.0-A Causal Graph Core defines:

CausalNode
    =
    immutable causal entity reference


CausalEdge
    =
    immutable causal relation


CausalGraph
    =
    node/edge container


APIs:

get-node
    lookup

add-node!
    validated insertion

add-edge!
    validated relation insertion


Properties:

- deterministic
- WAL-compatible
- replay-compatible
- non-semantic
- non-authoritative


Role:

History/WAL
      |
      v
Causal Graph
      |
      v
Causal Analysis
```

このコードは Chron-R2.0-A の中では **「Truth（WAL）から生成される因果構造の最小ランタイム表現」** に相当し、先ほどの `causal-subgraph` の基盤データモデルになります。
