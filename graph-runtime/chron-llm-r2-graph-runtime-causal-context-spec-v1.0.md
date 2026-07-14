# Chron-LLM R2 Graph Runtime Specification
## Causal Graph / Projection / Prefill Reconstruction Contract v1.0

**Status:** Stable Candidate  
**Version:** v1.0  
**Layer:** R2 Graph Runtime Layer  
**Package:** `chron-r2-0-a`  
**Scope:**  
- Causal Graph Representation
- Causal Ancestry Resolution
- Context Projection
- Evaluation Attachment
- Deterministic Prefill Reconstruction

**Relation:**


Upstream:
R1 Kernel Core
Canonical State / Event Stream

Downstream:
LLM Backend Prefill
Phase E Causal DSL Runtime
Worldline Execution


---

# 0. Purpose（目的）

R2 Graph Runtime Layer は、R1 Kernel によって管理される正史状態を、LLM 実行に必要な **因果コンテキスト** へ変換する実行基盤である。

本レイヤは以下の責務を持つ。

- Causal Graph の保持
- 因果祖先探索
- Canonical Context の射影
- Evaluation 情報の任意統合
- Deterministic Prompt Reconstruction
- Prefill State の生成

R2 Graph Runtime は Canonical 状態そのものを変更せず、既存の因果構造から実行用状態を再構成する。

---

# 1. Architecture Overview

         R1 Canonical State
                |
                v

        Causal Graph Runtime

    +-----------+------------+
    |                        |
    v                        v

causal-subgraph() project-context()

    |                        |
    +-----------+------------+

                |
                v

          Context Nodes

                |
                v

      canonical-prompt()

                |
                v

         Prefill State

                |
                v

          LLM Backend

---

# 2. Core Design Principles

## 2.1 Non-destructive Projection

Graph Runtime は読み取り専用の投影処理を行う。

保証：

- Graph は変更されない
- Payload は参照取得のみ
- Projection は純粋な再構成処理

---

## 2.2 Causal Separation

Graph Edge は種類によって意味を分離する。

現在定義される Edge:

| Type | Meaning |
|---|---|
| `:causal` | 因果関係 |
| `:eval` | 評価・フィードバック関係 |

---

## 2.3 Deterministic Reconstruction

同一 Graph、同一 Store、同一 Prompt Builder から生成される Prefill は同一となる。


Graph
+
Payload Store
+
Prompt Builder

    |
    v

Prefill Hash


---

# 3. Causal Graph Model

## 3.1 Causal Node

```lisp
(defstruct
    (causal-node
       (:constructor make-causal-node
           (id type payload-ref &optional metadata)))
  id
  type
  payload-ref
  metadata)
Fields
Field	Type	Description
id	Object	Node identifier
type	Keyword	Node semantic type
payload-ref	Payload Reference	External content reference
metadata	Any	Additional causal metadata
Guarantee

causal-node は immutable object として扱う。

:read-only t

により生成後の変更を禁止する。

4. Causal Edge Model
(defstruct
    (causal-edge
       (:constructor make-causal-edge
           (from to type)))
  from
  to
  type)
Fields
Field	Description
from	Source node
to	Destination node
type	Edge semantic
5. Causal Graph
(defstruct
    (causal-graph
       (:constructor make-causal-graph
           (&key nodes edges)))
  nodes
  edges)
Structure
Causal Graph

Nodes:
    N1
    N2
    N3

Edges:

N1 --:causal--> N2
N2 --:eval----> E1
6. Graph API
6.1 Node Lookup
(defun get-node (graph id))
Contract

指定 ID の Node を取得する。

存在しない場合：

nil

を返す。

6.2 Node Addition
(defun add-node! (graph node))
Validation

保証：

node は causal-node である
duplicate idは禁止

Violation:

Duplicate node id
6.3 Edge Addition
(defun add-edge! (graph edge))
Validation

保証：

edge は causal-edge
from node が存在
to node が存在
7. Causal Subgraph Resolution
causal-subgraph
(defun causal-subgraph
    (graph target-id))
Purpose

Target Node に至る因果祖先を抽出する。

対象 Edge:

:type :causal

のみ。

Algorithm
target
 |
 v

incoming :causal edge

 |
 v

parent

 |
 v

root

探索後：

root → ... → target

の順序で返却。

Guarantee
deterministic ordering
cycle safe
non-destructive
causal relation only
8. Context Projection Layer
Context Node
(defstruct
    (context-node
       (:constructor make-context-node
           (id type content feedbacks)))
  id
  type
  content
  feedbacks)
Role

Causal Node を LLM Context 用形式へ変換する中間表現。

Fields
Field	Description
id	Original node id
type	Node type
content	Loaded payload
feedbacks	Evaluation payload
9. Evaluation Association
associated-evaluations
(defun associated-evaluations
    (graph node-id))
Purpose

Node から outgoing :eval edge を探索する。

Example:

Node A

 |
 :eval

 v

Evaluation Node
Guarantee
insertion order preserved
causal relationには影響しない
10. Context Projection
project-context
(defun project-context
    (graph store target-id
           &key include-evaluations))
Processing
target-id

 ↓

causal-subgraph

 ↓

causal nodes

 ↓

load payload

 ↓

context-node
Evaluation Inclusion

Default:

include-evaluations = nil

の場合：

causal facts only

となる。

true の場合：

causal facts
 +
evaluation feedback

を含む。

11. Prefill Reconstruction Layer
Prefill State
(defstruct
    (prefill-state
       (:constructor make-prefill-state
           (context target-id hash)))
  context
  target-id
  hash)
Fields
Field	Description
context	Projected context
target-id	Reconstruction target
hash	Prompt identity
12. Canonical Prompt Builder
canonical-prompt
(defun canonical-prompt
    (context))
Output Format
(prompt
 (:node ID
  :type TYPE
  :content CONTENT
  :feedback FEEDBACK))
Guarantee
deterministic serialization
machine-readable format
replay compatible
13. Prefill State Construction
build-prefill-state
(defun build-prefill-state
    (graph store target-id
           &key include-evaluations
                prompt-builder))
Pipeline
Graph

 ↓

project-context

 ↓

Prompt Builder

 ↓

SHA256

 ↓

Prefill State
Validation

Prompt Builder:

Must return:

string

Otherwise:

Prompt builder must return a string
14. Runtime Guarantees
14.1 Deterministic Reconstruction

同一入力:

Graph
Store
Prompt Builder
Target ID

から同一:

Prefill Hash

を生成する。

14.2 Causal Integrity

Prefill Context は：

:causal

Edge のみを基礎とする。

14.3 Evaluation Isolation

Evaluation は optional metadata として扱う。

CAUSAL STATE

+

OPTIONAL EVALUATION

であり、正史因果とは分離される。

15. Frozen Boundary
Frozen
causal-node structure
causal-edge semantics
causal-subgraph behavior
context projection contract
prefill-state identity
Flexible
payload storage backend
prompt-builder format
additional edge types
evaluation schema
16. Module Dependency
graph.lisp
      |
      v

causal.lisp

      |
      v

projection.lisp

      |
      v

prefill.lisp
Final Statement

Chron-LLM R2 Graph Runtime Specification
Causal Graph / Projection / Prefill Reconstruction Contract v1.0

は、R1 Kernel の Canonical State を LLM 実行可能な因果コンテキストへ変換する Runtime Boundary を定義する。

本レイヤは：

因果グラフ保持
因果祖先解決
Context Projection
Prompt Reconstruction
Prefill Identity

を提供し、Chron-LLM における決定的な世界線再構成基盤となる。