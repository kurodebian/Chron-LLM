# Basin Structure Analysis Specification v1.0

## 1. Overview

### 1.1 Purpose

`experiment` パッケージ内の Basin Structure Analysis は、状態遷移グラフ上における **attractor（吸引状態）への収束構造**を解析し、各 attractor に属する basin（吸引領域）の構造情報を生成する。

本モジュールの目的:

* graph state space の収束先分類
* attractor ごとの basin 集約
* basin size（質量）計測
* 状態空間における安定領域分析

---

# 2. Architectural Position

## 2.1 Analysis Pipeline

```text
 id="basin-flow"

        Graph
          |
          |
          v

+----------------------+
| find-attractor       |
| state trajectory     |
+----------------------+

          |
          |

    Attractor ID

          |
          v

+----------------------+
| build-basin-map      |
| grouping             |
+----------------------+

          |
          v

+----------------------+
| build-basin-structure|
| statistics           |
+----------------------+

          |
          v

 Basin Structure
```

---

# 3. Responsibility Boundary

## 3.1 Responsible

本モジュールは:

| Responsibility          | Status |
| ----------------------- | ------ |
| attractor grouping      | ✓      |
| basin construction      | ✓      |
| basin mass calculation  | ✓      |
| basin ratio calculation | ✓      |

---

## 3.2 Non-Responsible

本モジュールは:

| Function                      | Owner          |
| ----------------------------- | -------------- |
| graph generation              | Graph Runtime  |
| state transition              | Kernel         |
| attractor discovery algorithm | find-attractor |
| policy decision               | Runtime        |
| commit                        | Kernel         |
| History persistence           | WAL            |

---

# 4. Data Model

## 4.1 Basin Structure

```lisp
(defstruct basin
  attractor
  nodes
  mass
  ratio)
```

---

## Logical Model

```text
Basin

{
    attractor : terminal state
    nodes     : member states
    mass      : number of states
    ratio     : normalized size
}
```

---

# 5. Basin Fields Specification

---

# 5.1 attractor

## Definition

```lisp
(basin-attractor basin)
```

---

## Purpose

収束先となる attractor state。

Example:

```text
state-A
```

---

## Contract

同一 attractor を持つ node 群は同一 basin に属する。

---

# 5.2 nodes

## Definition

```lisp
(basin-nodes basin)
```

---

## Purpose

この basin に含まれる graph nodes。

Example:

```text
[
 node1
 node5
 node9
]
```

---

# 5.3 mass

## Definition

```lisp
(basin-mass basin)
```

---

## Purpose

Basin の状態数。

計算:

```text
mass = |nodes|
```

---

Example:

```text
nodes:

[A B C D]

mass:

4
```

---

# 5.4 ratio

## Definition

```lisp
(basin-ratio basin)
```

---

## Purpose

全探索状態数に対する basin 占有率。

Formula:

[
ratio=\frac{mass}{total_nodes}
]

---

Example:

```text
total nodes = 100

basin nodes = 25

ratio = 0.25
```

---

# 6. Function Specification

---

# 6.1 build-basin-map

## Definition

```lisp
(defun build-basin-map (graph nodes steps)
```

---

## Purpose

各 node の attractor を探索し、attractor 単位で node を分類する。

---

## Input

### graph

状態遷移グラフ。

想定:

```text
Node → Next Node
```

---

### nodes

解析対象 node list。

Example:

```lisp
(
 n1
 n2
 n3
)
```

---

### steps

探索上限。

用途:

* attractor search depth
* trajectory limit

---

# 7. Algorithm

Pseudo code:

```text
create empty table

for each node:

    attractor =
        find-attractor(graph,node,steps)

    append node
    to attractor bucket

return table
```

---

## Equivalent

```lisp
(map node)

       |

       v

(find-attractor)

       |

       v

attractor → nodes
```

---

# 8. Output Format

戻り値:

```text
Hash Table
```

構造:

```text
{
 attractor-A :
     (node1 node5 node8)

 attractor-B :
     (node2 node3)

}
```

---

# 9. Properties

## 9.1 Grouping Guarantee

同一 attractor:

```text
A(node1)=A(node2)
```

なら:

```text
node1,node2 ∈ same basin
```

---

## 9.2 Coverage

理想状態:

```text
all nodes
=
union of all basin nodes
```

---

# 10. build-basin-structure

## Definition

```lisp
(defun build-basin-structure
    (basin-map total-nodes))
```

---

## Purpose

Basin map を統計情報付き Basin object に変換する。

---

# 11. Algorithm

Pseudo:

```text
create result list

for each:

    attractor
    nodes


    mass =
        length(nodes)


    ratio =
        mass / total-nodes


    create basin object


append

return result
```

---

# 12. Output

例:

```lisp
(
 #<BASIN attractor=A mass=30 ratio=0.3>

 #<BASIN attractor=B mass=70 ratio=0.7>
)
```

---

# 13. Complete Analysis Flow

```text
 id="complete-basin"

Graph

 |

Nodes

 |

find-attractor

 |

Basin Map

 |

build-basin-structure

 |

[
 Basin{
   attractor
   nodes
   mass
   ratio
 }
]
```

---

# 14. Mathematical Model

State space:

[
S={s_1,s_2,...,s_n}
]

Transition:

[
f:S\rightarrow S
]

Attractor:

[
A_i
]

Basin:

[
B_i={s | f^k(s)\rightarrow A_i}
]

Basin ratio:

[
R_i=\frac{|B_i|}{|S|}
]

---

# 15. Chron-LLM / Chron-OS Mapping

この解析層は Chron-LLM の Phase-E Trace Analysis に対応する。

位置:

```text
 id="chron-map"

History/WAL

      |
      v

Event Stream

      |
      v

Graph Runtime

      |
      v

Trajectory

      |
      v

Attractor Analysis

      |
      v

Basin Structure
```

---

# 16. Relation to Deterministic Kernel

重要:

Basin Analysis は状態変更を行わない。

分類:

| 項目               | 状態 |
| ---------------- | -- |
| Read Graph       | ✓  |
| Generate Metrics | ✓  |
| Modify World     | ✗  |
| Commit           | ✗  |
| Affect Scheduler | ✗  |

---

# 17. Current Implementation Review

## Strengths

### 1. Clean Separation

`build-basin-map`

責務:

```text
classification
```

`build-basin-structure`

責務:

```text
measurement
```

分離されている。

---

### 2. Deterministic

同一:

* graph
* nodes
* steps

なら:

同一 basin structure。

---

### 3. Minimal State

保持するもの:

```text
analysis result only
```

---

# 18. Potential Improvements

## P0: Empty Graph Handling

現在:

```lisp
(/ mass total-nodes)
```

は:

```text
total-nodes = 0
```

でエラー。

推奨:

```lisp
(assert (> total-nodes 0))
```

---

## P1: Basin Ordering

現在:

```lisp
result
```

は hash iteration order 依存。

必要なら:

```text
sort by ratio descending
```

を追加。

---

## P2: Stable Basin ID

現在:

```text
attractor object identity
```

依存。

将来:

```text
basin-id
```

追加可能。

---

# 19. Formal Invariants

## BASIN-1

Every node belongs to exactly one basin.

```text
∀ node ∈ Nodes

∃! Basin
```

---

## BASIN-2

Basin mass equals node count.

```text
mass = length(nodes)
```

---

## BASIN-3

All basin ratios sum to approximately 1.

[
\sum ratio_i = 1
]

---

## BASIN-4

Analysis is observational.

```text
Basin Analysis
≠
Runtime Transition
```

---

# Final Specification Summary

```text
Basin Structure Analysis computes the topology of state-space convergence.

Input:
    Graph
    Nodes
    Transition depth

Process:
    Node → Attractor classification
    Attractor → Basin grouping
    Basin → Statistical structure

Output:
    Basin objects

Each Basin contains:
    attractor
    member nodes
    mass
    ratio

The analysis is:
    deterministic
    observational
    non-authoritative
    replay-compatible
```

この実装は Chron-OS の **Graph Runtime → Attractor → Basin Structure Analysis Layer** として、Phase-E相当の解析プリミティブになっています。
