# Strongly Connected Components (SCC) Analysis Specification v1.0

## Graph Topology Observation Layer

---

# 1. Overview

## 1.1 Purpose

`successors`, `predecessors`, `dfs-order`, `dfs-component`, `compute-sccs` は、`experiment` グラフ上の **Strongly Connected Component (SCC: 強連結成分)** を抽出するための純粋解析モジュールである。

本モジュールは、有向グラフの到達可能性構造を解析し、

* 循環構造
* 自己維持状態集合
* attractor候補領域
* graph topology

を検出する基礎層を提供する。

---

# 2. Architectural Position

```text
                 Graph

                   |
                   v

          SCC Analysis Layer

                   |
        +----------+----------+
        |                     |
        v                     v

   Cycle Detection       Attractor Analysis

        |                     |
        +----------+----------+

                   |
                   v

          Basin Structure
```

---

# 3. Responsibility Boundary

## 3.1 Responsible

| Function      | Responsibility                 |
| ------------- | ------------------------------ |
| successors    | outgoing transition extraction |
| predecessors  | incoming transition extraction |
| dfs-order     | graph traversal ordering       |
| dfs-component | reverse graph exploration      |
| compute-sccs  | SCC decomposition              |

---

## 3.2 Non-Responsible

| Function                | Owner            |
| ----------------------- | ---------------- |
| Graph mutation          | Runtime / Kernel |
| Transition selection    | next-event       |
| Execution               | rollout*         |
| Persistence             | WAL              |
| Semantic interpretation | LLM / Analysis   |

---

# 4. Graph Model Assumption

対象:

[
G=(V,E)
]

where:

* (V) = nodes
* (E) = directed edges

Edge:

```text
(from → to)
```

---

# 5. Helper Function Specifications

---

# 5.1 successors

## Definition

```lisp
(defun successors (graph node)
```

---

## Purpose

指定 node から出る successor node 一覧を取得する。

---

## Algorithm

```lisp
edges where:

edge.from == node

↓

map edge.to
```

---

## Example

Graph:

```text
a1 → a2
a1 → b1
```

Input:

```lisp
(successors graph :a1)
```

Output:

```lisp
(:a2 :b1)
```

---

## Contract

Returns:

```text
List<Node>
```

No mutation.

---

# 5.2 predecessors

## Definition

```lisp
(defun predecessors (graph node)
```

---

## Purpose

指定 node に入る predecessor node 一覧を取得する。

---

## Algorithm

```text
edges where:

edge.to == node

↓

map edge.from
```

---

## Example

Graph:

```text
a1 → a2
b1 → a2
```

Input:

```lisp
(predecessors graph :a2)
```

Output:

```lisp
(:a1 :b1)
```

---

# 6. DFS Order Generation

## 6.1 dfs-order

Definition:

```lisp
(defun dfs-order (graph nodes)
```

---

## Purpose

SCC decomposition 前処理として DFS finishing order を生成する。

これは Kosaraju Algorithm の第一段階。

---

# 7. Algorithm

内部:

```lisp
visited = {}

order = []
```

---

DFS:

```text
visit(node)

    mark visited

    visit successors

    push node after completion
```

---

つまり:

```text
post-order traversal
```

を生成する。

---

# 8. Example

Graph:

```text
A → B → C
```

DFS:

```text
visit A

 visit B

  visit C

finish C
finish B
finish A
```

Order:

```text
(C B A)
```

---

# 9. dfs-component

## Definition

```lisp
(defun dfs-component (graph start visited)
```

---

## Purpose

逆方向グラフを探索し、1つのSCCを取得する。

---

## Algorithm

使用:

```text
predecessor traversal
```

---

処理:

```text
start

↓

predecessors

↓

predecessors...

↓

component
```

---

# 10. Example

Graph:

```text
A → B
B → C
C → A
```

start:

```text
A
```

predecessor探索:

```text
A

← C

← B
```

結果:

```text
(A C B)
```

---

# 11. compute-sccs

## Definition

```lisp
(defun compute-sccs (graph nodes)
```

---

## Purpose

Graph全体を Strongly Connected Components に分割する。

---

# 12. Algorithm

実装:

Kosaraju Algorithm

---

## Phase 1

DFS order:

```text
G
 ↓
dfs-order
```

生成:

```text
finishing order
```

---

## Phase 2

順番に:

```text
reverse graph DFS
```

実行。

---

結果:

```text
SCC list
```

---

# 13. Execution Flow

```text
Input:

Graph

Nodes


      |

      v


dfs-order


      |

      v


visited reset


      |

      v


dfs-component


      |

      v


SCC collection
```

---

# 14. Return Format

戻り値:

```text
List of Lists
```

Example:

```lisp
(
 (:a1 :a2 :a3)

 (:b1 :b2 :b3)

 (:c1)

)
```

---

# 15. Mathematical Definition

Strongly Connected Component:

node set (C)

such that:

[
\forall u,v \in C
]

there exists:

[
u \rightarrow v
]

and:

[
v \rightarrow u
]

---

# 16. 3Cluster Graph Expected Result

対象:

```text
a1 → a2 → a3 → a1
```

and:

```text
b1 → b2 → b3 → b1
```

---

Expected:

```text
SCC-1

(a1 a2 a3)


SCC-2

(b1 b2 b3)
```

---

Bridge:

```text
c1
c2
```

Expected:

```text
singleton SCC
```

because:

```text
c → cluster

but

cluster → c
```

does not exist。

---

# 17. Relationship With Attractor Detection

Current architecture:

```text
Graph

↓

SCC

↓

Cycle Detection

↓

Attractor Candidate

↓

Basin
```

---

重要:

SCC は attractor と同一ではない。

SCC:

```text
mutual reachability
```

Attractor:

```text
stable recurrent dynamics
```

---

# 18. Relationship With find-recurrent-cycle

Comparison:

| Function             | Output           |
| -------------------- | ---------------- |
| compute-sccs         | state groups     |
| find-cycle           | observed cycle   |
| find-recurrent-cycle | trajectory cycle |

---

Example:

SCC:

```text
(a1 a2 a3)
```

Cycle:

```text
(a1 a2 a3)
```

Attractor:

```text
same cycle
```

になる場合がある。

---

# 19. Determinism Contract

Given:

```text
same graph

same nodes
```

then:

```text
same SCC partition
```

must be produced.

---

# 20. Complexity

## successors

全 edge scan:

[
O(E)
]

---

## predecessors

全 edge scan:

[
O(E)
]

---

## dfs-order

DFS:

[
O(V+E)
]

---

## dfs-component

DFS:

[
O(V+E)
]

---

## compute-sccs

Kosaraju:

[
O(V+E)
]

---

# 21. Purity Contract

`compute-sccs` comment:

```lisp
"Purely observational."
```

の通り:

禁止:

```text
Graph mutation

Node mutation

Edge mutation

State update
```

---

# 22. Chron-OS Mapping

このモジュールは Chron-OS の:

```text
Topology Analysis Layer
```

に対応する。

Mapping:

| Graph Analysis | Chron-OS                     |
| -------------- | ---------------------------- |
| Node           | State                        |
| Edge           | Event transition             |
| SCC            | Stable reachable state group |
| Cycle          | Worldline recurrence         |
| Basin          | Attractor domain             |

---

# 23. Design Assessment

## Strengths

### 1. Standard Algorithm

Kosarajuベースで:

* 実装容易
* 決定的
* 計算量明確

---

### 2. Correct Layer Separation

構造:

```text
Graph

↓

SCC

↓

Cycle

↓

Attractor

↓

Basin
```

が明確。

---

### 3. Chron-OSとの整合

SCCは:

「どの状態群が相互作用可能か」

を見る解析であり、

CommitやWorld mutationとは独立。

---

# 24. Improvement Candidates

## P1: Explicit Reverse Graph

現在:

```lisp
predecessors
```

は毎回 edge scan。

改善:

```text
Graph Index

node → incoming edges
```

---

## P2: Stable Ordering

Hash table traversal:

```text
順序保証なし
```

必要なら:

```text
sort SCC members
```

追加。

---

## P3: SCC Metadata

将来:

```lisp
(defstruct scc
  nodes
  size
  cyclic-p
  attractor-candidate-p)
```

可能。

---

# 25. Formal Invariants

## SCC-1

Every node belongs to exactly one SCC.

\[
\bigcup \mathrm{SCC}_i = V
\]

---

## SCC-2

SCCs do not overlap.

[
SCC_i \cap SCC_j=\emptyset
]

---

## SCC-3

All nodes inside SCC are mutually reachable.

---

## SCC-4

Analysis does not alter graph.

---

# Final Specification Summary

```text
compute-sccs performs deterministic topology analysis.

Input:

    Directed Graph


Process:

    DFS finishing order

        +

    Reverse graph traversal


Output:

    Partition of graph into SCCs


The module provides:

    cycle foundation
    attractor discovery support
    basin analysis input


It is:

    deterministic
    observational
    non-authoritative
    replay compatible
```

このSCC層を追加したことで、実験グラフ解析は

```
Graph
 ↓
SCC
 ↓
Cycle
 ↓
Attractor
 ↓
Basin Structure
```

という、Chron-OSの状態空間解析パイプラインとして一段完成度が上がっています。
