# Context Projection Specification v1.0

## Chron-R2.0-A Prompt Context Construction Layer

---

# 1. Overview

## 1.1 Purpose

`context-node`, `associated-evaluations`, `project-context` は、Chron-R2.0-A における **Causal Graph → LLM Context Projection Layer** を定義する。

本モジュールの責務:

* Causal Graph 上の因果履歴取得
* Payload Store から実データ取得
* Context Node 形式への変換
* Optional Evaluation Knowledge の付加
* Prefill State 生成前の純粋な Context View 作成

---

# 2. Architectural Position

```text id="context-layer"

                 History / WAL

                      |
                      |
                      v

               Payload Store

                      |
                      v

              Causal Graph

                      |
                      v

             causal-subgraph

                      |
                      v

          Causal Ancestry Nodes

                      |
                      v

           project-context

                      |
                      v

             Context Nodes

                      |
                      v

          canonical-prompt

                      |
                      v

             LLM Prefill
```

---

# 3. Design Principle

Chron-R2.0-A の基本境界:

```text
History/WAL
    =
Truth
```

```text
Graph
    =
Structure Projection
```

```text
Context
    =
LLM View
```

である。

したがって `project-context` は:

* Truth を変更しない
* Graph を変更しない
* LLM 用 View を生成する

だけを担当する。

---

# 4. Responsibility Boundary

## 4.1 Responsible

| Component              | Responsibility             |
| ---------------------- | -------------------------- |
| context-node           | LLM input representation   |
| associated-evaluations | Evaluation edge lookup     |
| project-context        | Graph → Context projection |

---

## 4.2 Non-Responsible

| Function              | Owner            |
| --------------------- | ---------------- |
| Payload persistence   | Store/WAL        |
| Causal graph mutation | Graph Runtime    |
| Prompt serialization  | canonical-prompt |
| Generation            | LLM              |
| Commit                | Kernel           |

---

# 5. context-node Specification

## 5.1 Definition

```lisp
(defstruct
    (context-node
      (:constructor make-context-node
          (id type content feedbacks)))

  id
  type
  content
  feedbacks)
```

---

# 6. Logical Model

```text
ContextNode =
{
    id,
    type,
    content,
    feedbacks
}
```

---

# 7. Field Specification

---

# 7.1 id

Definition:

```lisp
(id nil :read-only t)
```

---

Purpose:

Original causal node identity.

対応:

```text
context-node.id
        |
        v
causal-node.id
```

---

用途:

* Trace correlation
* Replay verification
* Prompt identity

---

# 7.2 type

Definition:

```lisp
(type nil
 :type keyword
 :read-only t)
```

---

Purpose:

Context node classification.

Examples:

```lisp
:event
:commit
:proposal
:state
```

---

# 7.3 content

Definition:

```lisp
(content ""
 :type string
 :read-only t)
```

---

Purpose:

Payload materialized from store.

取得:

```lisp
(load-payload store payload-ref)
```

---

重要:

Context Node:

```text
payload value
```

を保持する。

しかし:

```text
causal-node
```

は:

```text
payload-ref
```

のみ保持する。

---

# 7.4 feedbacks

Definition:

```lisp
(feedbacks nil
 :type list
 :read-only t)
```

---

Purpose:

Optional evaluation knowledge.

例:

```text
[
 "accepted"
 "score:0.8"
 "review result"
]
```

---

Default:

```lisp
nil
```

---

# 8. associated-evaluations Specification

## 8.1 Definition

```lisp
(defun associated-evaluations (graph node-id)
```

---

## Purpose

指定 node に接続された evaluation node を取得する。

対象 Edge:

```lisp
:eval
```

のみ。

---

# 9. Algorithm

```lisp
(loop for edge in (causal-graph-edges graph)

      when
      (
        edge.type == :eval

        AND

        edge.from == node-id
      )

      collect edge.to)
```

---

# 10. Direction Model

Evaluation relation:

```text
Node

 |
 | :eval
 v

Evaluation Node
```

---

探索:

```text
source → evaluation
```

方向。

---

# 11. Ordering Contract

コメント:

> Evaluation nodes reached through an outgoing :EVAL edge, in insertion order.

---

つまり:

Graph Edge List:

```text
[
 A → E1
 A → E2
 A → E3
]
```

の場合:

返却:

```text
[
 E1
 E2
 E3
]
```

---

# 12. Return Contract

成功:

```text
List<CausalNode>
```

---

対象無し:

```lisp
nil
```

---

# 13. project-context Specification

## 13.1 Definition

```lisp
(defun project-context
    (graph store target-id
     &key
     (include-evaluations nil))
```

---

# 14. Purpose

Target Node の causal ancestry を LLM 用 Context View に変換する。

---

# 15. Input

---

## graph

Causal Graph。

---

## store

Payload Storage。

役割:

```text
payload-ref

↓

payload
```

変換。

---

## target-id

Context projection target。

---

## include-evaluations

Optional。

Default:

```lisp
nil
```

---

意味:

Evaluation knowledge を Context に含めるか。

---

# 16. Execution Pipeline

```text
target-id

    |

    v

causal-subgraph

    |

    v

causal nodes

    |

    v

load payload

    |

    v

context-node

    |

    v

Context List
```

---

# 17. Detailed Algorithm

## Step 1

Causal ancestry extraction:

```lisp
(causal-subgraph graph target-id)
```

---

Result:

```text
[
root
...
target
]
```

---

## Step 2

Each causal-node conversion:

```lisp
make-context-node
```

---

Mapping:

```text
causal-node.id
        ↓
context-node.id


causal-node.type
        ↓
context-node.type


payload-ref
        ↓
load-payload
        ↓
content
```

---

# 18. Payload Loading

Code:

```lisp
(or
 (load-payload store
                (causal-node-payload-ref node))
 "")
```

---

Contract:

Payload missing:

```text
empty string
```

として扱う。

---

# 19. Evaluation Inclusion Logic

## Disabled

Default:

```lisp
include-evaluations=nil
```

結果:

```text
feedbacks=nil
```

---

## Enabled

```lisp
include-evaluations=t
```

処理:

```text
Node

 ↓

associated-evaluations

 ↓

load payload

 ↓

feedback list
```

---

Example:

Graph:

```text
Answer

 |
 | :eval
 v

Review
```

Context:

```text
ContextNode

{
 content="Answer"

 feedbacks=
 [
  "Review"
 ]
}
```

---

# 20. Non-Destructive Contract

コメント:

> Non-destructively combine causal facts with opt-in evaluation knowledge.

---

保証:

変更しない:

```text
causal graph

payload store

history

nodes
```

---

生成のみ:

```text
context-node list
```

---

# 21. Relationship With Prefill State

Full pipeline:

```text
Causal Graph

      |
      v

project-context

      |
      v

Context Nodes

      |
      v

canonical-prompt

      |
      v

Prompt Hash

      |
      v

Prefill State
```

---

# 22. Relationship With Knowledge Model

Chron-LLM architecture:

```text
Knowledge ∈ History
```

である。

この層:

```text
History

↓

Context Projection
```

であり、

Knowledge storage ではない。

---

# 23. Determinism Contract

同一:

```text
Graph

Store

target-id

include-evaluations
```

なら:

同一:

```text
Context List
```

を生成する。

---

# 24. Complexity

## causal-subgraph

依存。

---

## associated-evaluations

現在:

[
O(E)
]

---

## project-context

Context node 数:

[
N
]

として:

[
O(N \times E)
]

---

# 25. Optimization Candidates

## 25.1 Evaluation Edge Index

現在:

```text
scan all edges
```

改善:

```text
node-id

↓

eval edges
```

---

## 25.2 Payload Cache

大量 Context:

現在:

```text
payload-ref

↓

load
```

毎回。

改善:

```text
payload-ref

↓

cached payload
```

---

# 26. Semantic Boundary

重要な分離:

```text
Causal Node
    |
    | reference
    v

Payload Store


    |
    v

Context Node


    |
    v

Prompt
```

---

つまり:

```text
Graph = structure

Store = truth payload

Context = LLM view
```

---

# 27. Chron-OS Mapping

| Component       | Chron-OS Role                   |
| --------------- | ------------------------------- |
| causal-node     | Committed event/state reference |
| payload-ref     | WAL pointer                     |
| payload store   | Truth storage                   |
| context-node    | Prompt projection object        |
| feedbacks       | Evaluation projection           |
| project-context | View builder                    |

---

# 28. Design Assessment

## Strengths

### 1. Truth/View Separation

正しく:

```text
History ≠ Prompt
```

を維持している。

---

### 2. Evaluation Isolation

評価情報は:

```text
optional knowledge
```

として扱われる。

つまり:

```text
Evaluation ≠ Cause
```

が保持される。

---

### 3. LLM Boundary Correctness

LLMへ渡るもの:

```text
Context View
```

であり、

直接:

```text
Graph
WAL
```

ではない。

---

# 29. Potential Future Extensions

## Context Metadata

追加候補:

```lisp
context-node
 timestamp
 source
 confidence
```

---

## Evaluation Weight

現在:

```text
feedbacks=list
```

将来:

```lisp
(
 evaluation
 score
 source
)
```

---

## Prompt Budget Control

追加:

```text
project-context

↓

token budget filter
```

---

# Final Specification Summary

```text
project-context converts causal history
into an immutable LLM context view.


Pipeline:

Causal Graph
      |
      v
Causal Ancestry
      |
      v
Payload Resolution
      |
      v
Context Nodes
      |
      v
Prompt Builder


Properties:

- deterministic
- non-destructive
- history-backed
- evaluation optional
- replay compatible


Role:

History/WAL
      |
      v
Causal Projection
      |
      v
LLM Prefill Boundary
```

この層によって Chron-R2.0-A は、

```
Truth (History/WAL)
        ↓
Structure (Causal Graph)
        ↓
View (Context)
        ↓
Prompt
        ↓
LLM
```

という責務分離を明確に実現しています。
