# Strongly Connected Components (SCC) Analysis Specification v1.0

## Graph Topology Observation Layer

# 1. Overview

## 1.1 Purpose

`successors`, `predecessors`, `dfs-order`, `dfs-component`, `compute-sccs` は、`experiment` グラフ上の **Strongly Connected Component (SCC: 強連結成分)** を抽出するための純粋解析モジュールである。

本モジュールは、有向グラフの到達可能性構造を解析し、

* 循環構造
* 自己維持状態集合
* attractor候補領域
* graph topology

を検出する基礎層を提供する。

# 2. Architectural Position

```
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

# 3. Responsibility Boundary

## 3.1 Responsible

| Function      | Responsibility                 |
| ------------- | ------------------------------ |
| successors    | outgoing transition extraction |
| predecessors  | incoming transition extraction |
| dfs-order     | graph traversal ordering       |
| dfs-component | reverse graph exploration      |
| compute-sccs  | SCC decomposition              |

## 3.2 Non-Responsible

| Function                | Owner            |
| ----------------------- | ---------------- |
| Graph mutation          | Runtime / Kernel |
| Transition selection    | next-event       |
| Execution               | rollout*         |
| Persistence             | WAL              |
| Semantic interpretation | LLM / Analysis   |

# 4. Graph Model Assumption

対象:

[
G=(V,E)
]

where:

* (V) = nodes
* (E) = directed edges

Edge:

```
(from → to)
```

# 5. Helper Function Specifications

# 5.1 successors

## Definition

```
(defun successors (graph node)
```

## Purpose

指定 node から出る successor node 一覧を取得する。

## Algorithm

```
edges where:

edge.from == node

↓

map edge.to
```

## Example

Graph:

```
a1 → a2
a1 → b1
```

Input:

```
(successors graph :a1)
```

Output:

```
(:a2 :b1)
```

## Contract

Returns:

```
List<Node>
```

No mutation.

# 5.2 predecessors

## Definition

```
(defun predecessors (graph node)
```

## Purpose

指定 node に入る predecessor node 一覧を取得する。

## Algorithm

```
edges where:

edge.to == node

↓

map edge.from
```

## Example

Graph:

```
a1 → a2
b1 → a2
```

Input:

```
(predecessors graph :a2)
```

Output:

```
(:a1 :b1)
```

# 6. DFS Order Generation

## 6.1 dfs-order

Definition:

```
(defun dfs-order (graph nodes)
```

## Purpose

SCC decomposition 前処理として DFS finishing order を生成する。

これは Kosaraju Algorithm の第一段階。

# 7. Algorithm

内部:

```
visited = {}

order = []
```

DFS:

```
visit(node)

    mark visited

    visit successors

    push node after completion
```

つまり:

```
post-order traversal
```

を生成する。

# 8. Example

Graph:

```
A → B → C
```

DFS:

```
visit A

 visit B

  visit C

finish C
finish B
finish A
```

Order:

```
(C B A)
```

# 9. dfs-component

## Definition

```
(defun dfs-component (graph start visited)
```

## Purpose

逆方向グラフを探索し、1つのSCCを取得する。

## Algorithm

使用:

```
predecessor traversal
```

処理:

```
start

↓

predecessors

↓

predecessors...

↓

component
```

# 10. Example

Graph:

```
A → B
B → C
C → A
```

start:

```
A
```

predecessor探索:

```
A

← C

← B
```

結果:

```
(A C B)
```

# 11. compute-sccs

## Definition

```
(defun compute-sccs (graph nodes)
```

## Purpose

Graph全体を Strongly Connected Components に分割する。

# 12. Algorithm

実装:

Kosaraju Algorithm

## Phase 1

DFS order:

```
G
 ↓
dfs-order
```

生成:

```
finishing order
```

## Phase 2

順番に:

```
reverse graph DFS
```

実行。

結果:

```
SCC list
```

# 13. Execution Flow

```
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

# 14. Return Format

戻り値:

```
List of Lists
```

Example:

```
(
 (:a1 :a2 :a3)

 (:b1 :b2 :b3)

 (:c1)

)
```

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

# 16. 3Cluster Graph Expected Result

対象:

```
a1 → a2 → a3 → a1
```

and:

```
b1 → b2 → b3 → b1
```

Expected:

```
SCC-1

(a1 a2 a3)


SCC-2

(b1 b2 b3)
```

Bridge:

```
c1
c2
```

Expected:

```
singleton SCC
```

because:

```
c → cluster

but

cluster → c
```

does not exist。

# 17. Relationship With Attractor Detection

Current architecture:

```
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

重要:

SCC は attractor と同一ではない。

SCC:

```
mutual reachability
```

Attractor:

```
stable recurrent dynamics
```

# 18. Relationship With find-recurrent-cycle

Comparison:

| Function             | Output           |
| -------------------- | ---------------- |
| compute-sccs         | state groups     |
| find-cycle           | observed cycle   |
| find-recurrent-cycle | trajectory cycle |

Example:

SCC:

```
(a1 a2 a3)
```

Cycle:

```
(a1 a2 a3)
```

Attractor:

```
same cycle
```

になる場合がある。

# 19. Determinism Contract

Given:

```
same graph

same nodes
```

then:

```
same SCC partition
```

must be produced.

# 20. Complexity

## successors

全 edge scan:

[
O(E)
]

## predecessors

全 edge scan:

[
O(E)
]

## dfs-order

DFS:

[
O(V+E)
]

## dfs-component

DFS:

[
O(V+E)
]

## compute-sccs

Kosaraju:

[
O(V+E)
]

# 21. Purity Contract

`compute-sccs` comment:

```
"Purely observational."
```

の通り:

禁止:

```
Graph mutation

Node mutation

Edge mutation

State update
```

# 22. Chron-OS Mapping

このモジュールは Chron-OS の:

```
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

# 23. Design Assessment

## Strengths

### 1. Standard Algorithm

Kosarajuベースで:

* 実装容易
* 決定的
* 計算量明確

### 2. Correct Layer Separation

構造:

```
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

### 3. Chron-OSとの整合

SCCは:

「どの状態群が相互作用可能か」

を見る解析であり、

CommitやWorld mutationとは独立。

# 24. Improvement Candidates

## P1: Explicit Reverse Graph

現在:

```
predecessors
```

は毎回 edge scan。

改善:

```
Graph Index

node → incoming edges
```

## P2: Stable Ordering

Hash table traversal:

```
順序保証なし
```

必要なら:

```
sort SCC members
```

追加。

## P3: SCC Metadata

将来:

```
(defstruct scc
  nodes
  size
  cyclic-p
  attractor-candidate-p)
```

可能。

# 25. Formal Invariants

## SCC-1

Every node belongs to exactly one SCC.

\[
\bigcup \mathrm{SCC}_i = V
\]

## SCC-2

SCCs do not overlap.

[
SCC_i \cap SCC_j=\emptyset
]

## SCC-3

All nodes inside SCC are mutually reachable.

## SCC-4

Analysis does not alter graph.

# Final Specification Summary

```
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
