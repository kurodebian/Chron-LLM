# Graph Rollout and Attractor Detection Specification v1.0

## Deterministic Transition Execution Layer

---

# 1. Overview

## 1.1 Purpose

`next-event`, `rollout*`, `find-attractor` は、`experiment` グラフ上での **決定論的状態遷移実行**と、有限ステップ後の収束先抽出を担当する。

本モジュールは:

* Graph transition の実行
* Edge strength に基づく優先遷移選択
* State trajectory（rollout path）生成
* Attractor candidate 抽出

を提供する。

---

# 2. Architectural Position

```text id="graph-rollout-arch"

             Graph
              |
              |
              v

       next-event

              |
              v

       State Transition

              |
              v

          rollout*

              |
              v

       Trajectory Path

              |
              v

      find-attractor

              |
              v

     Attractor Candidate

              |
              v

   Basin / Cycle Analysis
```

---

# 3. Responsibility Boundary

## 3.1 Responsible

| Component      | Responsibility            |
| -------------- | ------------------------- |
| next-event     | Select next transition    |
| rollout*       | Execute finite trajectory |
| find-attractor | Return terminal state     |

---

## 3.2 Non-Responsible

| Function           | Owner           |
| ------------------ | --------------- |
| Graph creation     | graph generator |
| Edge mutation      | Kernel          |
| Event persistence  | WAL             |
| Commit             | Kernel          |
| Semantic reasoning | LLM             |

---

# 4. Transition Model

Graph is modeled as:

[
G=(V,E)
]

where:

* (V) = nodes
* (E) = directed edges

Each edge:

```text
Edge =
(
 from,
 to,
 relation,
 strength
)
```

---

# 5. next-event Specification

## 5.1 Definition

```lisp
(defun next-event (graph node-id)
```

---

## 5.2 Purpose

指定 node から出る outgoing edge のうち、最大 strength の edge を選択する。

---

# 6. Algorithm

Code:

```lisp
(defun next-event (graph node-id)
  (let ((edges
          (remove-if-not
           (lambda (e)
             (eq (edge-from e) node-id))
           (graph-edges graph))))
    (car
     (sort edges
           #'>
           :key #'edge-strength))))
```

---

## Processing

### Step 1

全 Edge 取得:

```text
graph.edges
```

---

### Step 2

from が一致する edge のみ抽出:

```text
edge.from == node-id
```

---

Example:

Graph:

```text
a1 → a2 0.9
a1 → b1 0.4
```

Input:

```text
node-id = a1
```

候補:

```text
[
 a1→a2,
 a1→b1
]
```

---

### Step 3

strength 降順ソート:

```text
0.9
0.4
```

---

### Step 4

最大 Edge を返却:

```text
a1→a2
```

---

# 7. Return Contract

## Success

Return:

```text
Edge Object
```

---

## No outgoing edge

Return:

```text
NIL
```

---

# 8. Determinism Contract

同一 Graph:

```text
G
```

同一 Node:

```text
N
```

なら:

```text
next-event(G,N)
```

は常に同一 Edge を返す。

---

# 9. rollout* Specification

## 9.1 Definition

```lisp
(defun rollout* (graph start steps)
```

---

## 9.2 Purpose

Graph transition を指定回数実行し、状態遷移履歴を生成する。

---

# 10. Input

## graph

対象 Graph。

---

## start

開始 Node ID。

例:

```text
:a1
```

---

## steps

最大遷移回数。

例:

```text
10
```

---

# 11. Algorithm

Code:

```lisp
(defun rollout* (graph start steps)
  (let ((path (list start))
        (node start))

    (dotimes (_ steps)

      (let ((e (next-event graph node)))

        (if (null e)

            (return path)

            (setf node (edge-to e)
                  path (append path (list node))))))

    path))
```

---

# 12. Execution Model

Example:

Graph:

```text
a1 → a2 → a3 → a1
```

Start:

```text
a1
```

Steps:

```text
5
```

---

Execution:

```text
step 0:

[a1]


step 1:

[a1 a2]


step 2:

[a1 a2 a3]


step 3:

[a1 a2 a3 a1]


step 4:

[a1 a2 a3 a1 a2]


step 5:

[a1 a2 a3 a1 a2 a3]
```

---

# 13. Return Value

Always returns:

```text
Node ID List
```

Example:

```lisp
(:a1 :a2 :a3 :a1 :a2)
```

---

# 14. Early Termination

If:

```text
next-event = NIL
```

then:

```text
rollout stops
```

Example:

```text
[a1 b1 c1]
```

where:

```text
c1 has no outgoing edge
```

returns:

```text
[a1 b1 c1]
```

---

# 15. find-attractor Specification

## 15.1 Definition

```lisp
(defun find-attractor (graph start steps)
```

---

## Purpose

有限 rollout の最終状態を attractor candidate として返す。

---

# 16. Algorithm

Code:

```lisp
(defun find-attractor (graph start steps)
  (car (last
        (rollout* graph start steps))))
```

---

処理:

```text
rollout

↓

path

↓

last node

↓

return
```

---

# 17. Example

Input:

```text
start:

:a1


steps:

10
```

Trajectory:

```text
:a1
:a2
:a3
:a1
:a2
...
```

Return:

```text
:a2
```

---

# 18. Relationship With Cycle Detection

Current:

```text
find-attractor
=
terminal state
```

---

Future cycle model:

```text
find-recurrent-cycle
=
terminal recurrent structure
```

---

Comparison:

| Function             | Output |
| -------------------- | ------ |
| find-attractor       | node   |
| find-recurrent-cycle | cycle  |

---

# 19. Relationship With Basin Analysis

Current flow:

```text
Node

↓

rollout*

↓

terminal node

↓

basin-map
```

---

Extended flow:

```text
Node

↓

rollout*

↓

cycle detection

↓

attractor cycle

↓

basin structure
```

---

# 20. 3Cluster Graph Example

Given:

```text
a1 → a2 → a3 → a1
```

strength:

```text
0.9
```

and:

```text
c1 → a1
0.6

c1 → b1
0.4
```

then:

```text
rollout(c1)
```

produces:

```text
c1
 |
 v
a1
 |
 v
a2
 |
 v
a3
 |
 v
a1
```

---

# 21. Formal Properties

## ROLL-1 Determinism

For fixed:

```text
Graph
Start
Steps
```

output path is deterministic.

---

## ROLL-2 Greedy Transition

Transition rule:

[
next(n)=argmax_e strength(e)
]

---

## ROLL-3 Finite Execution

Maximum transitions:

[
steps
]

---

## ROLL-4 Non-Mutation

These functions:

* do not modify graph
* do not modify nodes
* do not modify edges

---

# 22. Complexity

## next-event

Current implementation:

Edge scan:

[
O(E)
]

Sort:

[
O(k\log k)
]

where:

* (E) = total edges
* (k) = outgoing edges

---

## rollout*

For `steps = N`:

[
O(N \times next-event)
]

---

## Optimization Candidate

Pre-index:

```text
node-id → outgoing edges
```

すると:

```text
next-event
```

は:

[
O(log k)
]

または:

[
O(1)
]

になる。

---

# 23. Chron-OS Mapping

この層は Chron-OS の:

```text
State Transition Executor
```

に相当する。

対応:

| Chron-OS        | Experiment     |
| --------------- | -------------- |
| World State     | Node           |
| Event           | Edge           |
| Transition Rule | next-event     |
| Execution Trace | rollout path   |
| Attractor       | terminal/cycle |

---

# 24. Design Assessment

## Strengths

### 1. Deterministic Transition

Edge strength による選択で:

```text
同じ状態
 ↓
同じ次状態
```

を保証。

---

### 2. Analysis Friendly

生成される:

```text
path
```

は:

* replay
* cycle detection
* basin analysis

に直接利用可能。

---

### 3. Minimal Runtime Core

責務が明確:

```text
observe

not decide
```

---

# 25. Current Limitation

## 25.1 Attractor Definition

現在:

```text
attractor = last node
```

これは簡易モデル。

より厳密には:

```text
attractor =
recurrent strongly connected structure
```

が望ましい。

---

## 25.2 Tie Handling

同じ strength:

```text
0.5
0.5
```

の場合、`sort` の安定性依存。

将来:

```text
secondary ordering key
```

推奨。

---

# 26. Final Specification Summary

```text
The rollout layer provides deterministic graph execution.

next-event:
    selects strongest outgoing transition

rollout*:
    executes finite deterministic trajectory

find-attractor:
    extracts terminal state candidate


The layer is:

- deterministic
- observational
- non-mutating
- replay-compatible


It forms the execution foundation for:

Graph
 →
Trajectory
 →
Cycle
 →
Attractor
 →
Basin
```

このコードは、Chron-OS的には **「状態空間上での決定論的実行エンジン（Minimal Transition Runtime）」** に相当し、その上に `find-recurrent-cycle` と `build-basin-structure` が解析層として乗る構造になります。
