# Causal Subgraph Extraction Specification v1.0

## Chron-R2.0-A Graph Runtime Core

---

# 1. Overview

## 1.1 Purpose

`causal-subgraph` は、Chron-R2.0-A Graph Runtime Core における **因果祖先グラフ抽出プリミティブ**である。

指定された target node を起点として、`:CAUSAL` edge のみを逆方向探索し、target に至る因果履歴を root → target の順序で返却する。

---

# 2. Architectural Position

```text
                 Graph Runtime

                       |
                       |
                       v

              causal-subgraph

                       |
                       v

          Causal Ancestry Projection

                       |
                       v

              History / Replay

                       |
                       v

            Worldline Analysis
```

---

# 3. Responsibility Boundary

## 3.1 Responsible

`causal-subgraph` は以下を担当する。

| Responsibility                 | Status |
| ------------------------------ | ------ |
| Target ancestry extraction     | ✓      |
| Causal edge filtering          | ✓      |
| Root-first ordering            | ✓      |
| Deterministic graph projection | ✓      |

---

## 3.2 Non-Responsible

本関数は以下を行わない。

| Function                    | Owner         |
| --------------------------- | ------------- |
| Node creation               | Graph Runtime |
| Edge creation               | Commit Layer  |
| State mutation              | Kernel        |
| WAL persistence             | History/WAL   |
| Policy decision             | Runtime       |
| Causal inference generation | Commit logic  |

---

# 4. Function Definition

```lisp
(defun causal-subgraph (graph target-id)
  "Return target's causal ancestry, root first, using only :CAUSAL edges.")
```

---

# 5. Input Specification

## 5.1 graph

型:

```text
Causal Graph
```

想定:

```text
Graph
 ├── Nodes
 └── Causal Edges
```

---

## 5.2 target-id

対象となる終端 node identifier。

例:

```lisp
:node-42
```

意味:

> この node が成立するまでの因果経路を取得する。

---

# 6. Output Specification

戻り値:

```text
List<Node>
```

順序:

```text
Root
 ↓
Ancestor
 ↓
...
 ↓
Target
```

---

例:

Graph:

```text
A --causal--> B
B --causal--> C
C --causal--> D
```

実行:

```lisp
(causal-subgraph graph 'D)
```

結果:

```text
(A B C D)
```

---

# 7. Algorithm

## 7.1 Overview

アルゴリズム:

```text
Target

 ↓

Find incoming :CAUSAL edges

 ↓

Visit parents recursively

 ↓

Collect nodes

 ↓

Reverse ordering

 ↓

Root-first result
```

---

# 8. Detailed Execution

## Step 1: Target Validation

```lisp
(unless (get-node graph target-id)
  (error "Unknown target node: ~S" target-id))
```

---

Contract:

存在しない node:

```text
ERROR
```

を返す。

---

理由:

因果祖先探索の基点が存在しないため。

---

# 9. Visited Management

```lisp
(let ((seen (make-hash-table :test #'equal))
      (ordered nil))
```

---

## seen

役割:

探索済み node 管理。

目的:

* cycle 防止
* 重複探索防止

---

Example:

```text
A → B
A → C
B → D
C → D
```

D の祖先探索:

```text
A
B
C
D
```

A を二重訪問しない。

---

# 10. Recursive Traversal

内部関数:

```lisp
(labels ((visit (id)
```

---

# 11. Visit Algorithm

Pseudo:

```text
visit(node)

 if already seen:
     return

 mark seen

 for each causal edge:

     if edge.to == node:

          visit(edge.from)


 append node
```

---

# 12. Edge Direction Model

重要:

探索方向:

```text
Graph direction:

A → B → C


Traversal:

C
↑
B
↑
A
```

つまり:

通常 edge:

```text
cause → effect
```

に対して、

探索:

```text
effect → cause
```

を行う。

---

# 13. Causal Edge Filtering

条件:

```lisp
(and
 (eq (causal-edge-type edge) :causal)
 (equal (causal-edge-to edge) id))
```

---

意味:

対象 node に入る edge のうち、

```text
edge.type = :causal
```

だけを見る。

---

除外される例:

```text
:reference

:semantic

:temporal

:observation
```

---

# 14. Ordering Logic

内部:

```lisp
(push (get-node graph id) ordered)
```

---

これは DFS post-order。

例:

```text
A → B → C
```

探索:

```text
C
↓
B
↓
A
```

push:

```text
C
B
A
```

---

最後:

```lisp
(nreverse ordered)
```

結果:

```text
A
B
C
```

---

# 15. Formal Model

Causal Graph:

[
G_c=(V,E_c)
]

where:

[
E_c \subseteq E
]

---

Target:

[
t \in V
]

---

Causal ancestry:

[
Anc(t)=
{v | v \rightarrow^* t}
]

---

Output:

[
[Root,...,t]
]

---

# 16. Example

## Graph

```text
        Input

          |
          |
          v

       Decision

          |
          |
          v

       Action

          |
          |
          v

       Result
```

---

Call:

```lisp
(causal-subgraph graph 'Result)
```

---

Return:

```text
(
 Input
 Decision
 Action
 Result
)
```

---

# 17. Relationship With History/WAL

Chron-R2.0-Aでは:

```text
History/WAL
      |
      |
      v

Committed Nodes

      |
      |
      v

Causal Graph
```

---

`causal-subgraph` は:

```text
History Projection
```

であり、

Historyそのものではない。

---

# 18. Relationship With Replay

Replay:

```text
Root

 ↓

Commit sequence

 ↓

Target state
```

を再構築するための最小因果経路を取得可能。

---

用途:

* deterministic replay
* debugging
* explanation
* state reconstruction

---

# 19. Determinism Contract

同一:

```text
graph

target-id
```

なら:

同一:

```text
causal ancestry
```

を返す。

---

条件:

* graph immutable
* edge ordering stable

---

# 20. Complexity

## Current Implementation

各 node:

```lisp
(dolist (edge (causal-graph-edges graph))
```

で全 edge scan。

---

Worst case:

[
O(V \times E)
]

---

# 21. Optimization Candidate

## Incoming Edge Index

現在:

```text
node
 |
 v
scan all edges
```

改善:

```text
node
 |
 v
incoming causal edge table
```

---

結果:

[
O(V+E)
]

相当。

---

# 22. Cycle Handling

現在:

```lisp
seen
```

により停止する。

例:

```text
A → B → C
↑       |
+-------+
```

探索:

```text
C
↓
B
↓
A
```

A再訪:

```text
skip
```

---

# 23. Semantic Guarantees

## CSG-1 Causal Purity

返却される経路は:

```text
:CAUSAL edge only
```

で構成される。

---

## CSG-2 Target Inclusion

必ず:

```text
target ∈ result
```

---

## CSG-3 Root Ordering

結果:

```text
cause first
effect last
```

---

## CSG-4 Non Mutation

Graph:

```text
unchanged
```

---

# 24. Chron-R2.0-A Mapping

```text
          Event Commit

              |
              v

        Causal Edge

              |
              v

          Causal Graph

              |
              v

     causal-subgraph

              |
              v

      Causal History View
```

---

# 25. Design Assessment

## Strengths

### 1. Correct causal direction

因果グラフでは:

```text
cause → effect
```

だが、

探索は:

```text
effect → cause
```

を行う必要がある。

この実装は正しい。

---

### 2. History/WALとの整合性

Chron-OS設計の:

```text
Truth = History/WAL
```

に対して、

これは:

```text
History → causal projection
```

として機能する。

---

### 3. Replay Compatibility

因果祖先列が得られるため:

```text
node reconstruction
```

に利用可能。

---

# 26. Future Extensions

## P1: Causal Slice

追加候補:

```lisp
(causal-slice graph targets)
```

複数 target の共通祖先抽出。

---

## P2: Causal Depth

追加:

```text
node depth from root
```

---

## P3: Causal Proof Object

現在:

```text
List<Node>
```

将来:

```lisp
(defstruct causal-proof
  nodes
  edges
  depth)
```

---

# Final Specification Summary

```text
causal-subgraph extracts the deterministic causal ancestry
of a target node.

Input:

    Graph
    Target Node


Process:

    Reverse traverse only :CAUSAL edges


Output:

    Root-first causal chain


Properties:

    deterministic
    observational
    replay-compatible
    non-mutating


Role in Chron-R2.0-A:

    History/WAL
        ↓
    Causal Graph
        ↓
    Causal Projection
        ↓
    Replay / Analysis
```

この関数は Chron-R2.0-A の設計上、**「Commitされた世界状態から、その状態を成立させた因果履歴だけを抽出する最小Projection API」** に相当します。
