# Recurrent Cycle Detection Specification v1.0

## Rollout-Based Cycle Extraction Module

---

# 1. Overview

## 1.1 Purpose

`find-cycle` および `find-recurrent-cycle` は、Graph Runtime 上で生成された状態遷移列（rollout path）から **再帰的に出現する周期構造（recurrent cycle）** を抽出するための解析プリミティブである。

本モジュールの目的:

* rollout trajectory の終端周期検出
* attractor candidate の抽出
* cyclic state transition の観測
* basin analysis への入力生成

---

# 2. Architectural Position

```text
 id="cycle-position"

        Graph

          |
          v

      rollout*

          |
          v

   State Transition Path

          |
          v

   find-cycle

          |
          v

 Recurrent Cycle

          |
          v

 find-attractor

          |
          v

 Basin Analysis
```

---

# 3. Responsibility Boundary

## 3.1 Responsible

本モジュールは:

| Function                    | Responsibility |
| --------------------------- | -------------- |
| Path inspection             | ✓              |
| Cycle extraction            | ✓              |
| Recurrent pattern detection | ✓              |
| Cycle representation        | ✓              |

---

## 3.2 Non-Responsible

本モジュールは:

| Function                | Owner          |
| ----------------------- | -------------- |
| State transition        | `next-event`   |
| Rollout execution       | `rollout*`     |
| Graph mutation          | Kernel         |
| Commit                  | Kernel         |
| Persistence             | WAL            |
| Semantic interpretation | Analysis layer |

---

# 4. Function Specification

---

# 4.1 find-cycle

## Definition

```lisp
(defun find-cycle (path)
  "Given a rollout path, extract the recurrent cycle at the end.")
```

---

## Purpose

Rollout path の末尾に存在する再帰部分を抽出する。

入力:

```text
State trajectory
```

出力:

```text
Cycle sequence
```

---

# 5. Input Model

## Path

想定形式:

```text
path =
[
 s0
 s1
 s2
 ...
 sn
]
```

例:

```text
[a b c a b c]
```

---

# 6. Algorithm

## Step 1

Path reverse:

```lisp
(reverse path)
```

例:

Before:

```text
[a b c a b c]
```

After:

```text
[c b a c b a]
```

---

## Step 2

Get final node:

```lisp
(last-node (car rev))
```

つまり:

```text
last-node = original path end
```

例:

```text
path:

[a b c a b c]

last-node:

c
```

---

## Step 3

Search previous occurrence

```lisp
(position last-node (cdr rev))
```

目的:

末尾状態が過去に存在するか確認。

---

# 7. Cycle Extraction Logic

## Case 1: Cycle Exists

例:

入力:

```text
[a b c a b c]
```

reverse:

```text
[c b a c b a]
```

探索:

```text
c
```

再出現:

```text
index = 3
```

取得:

```lisp
(subseq rev 0 (1+ pos))
```

結果:

```text
[c b a c]
```

---

その後:

```lisp
(reverse result)
```

により:

```text
[c a b c]
```

となる。

---

## Case 2: No Cycle

例:

```text
[a b c d]
```

末尾:

```text
d
```

過去に存在しない。

結果:

```lisp
(list last-node)
```

返却:

```text
[d]
```

---

# 8. Return Contract

`find-cycle` は必ず list を返す。

---

## Cycle Found

```text
(
 cycle start
 ...
 repeated node
)
```

---

## Cycle Not Found

```text
(
 last-node
)
```

---

# 9. find-recurrent-cycle

## Definition

```lisp
(defun find-recurrent-cycle (graph start steps)
  "Rollout and return the observed recurrent cycle (not a single node).")
```

---

# 10. Purpose

Graph 上で rollout を実行し、その結果から周期構造を返す。

---

# 11. Execution Flow

```text
Input:

graph
start node
step limit


        |

        v


rollout*

        |

        v


path

        |

        v


find-cycle

        |

        v


reverse

        |

        v


cycle
```

---

# 12. Internal Processing

## Step 1

Rollout:

```lisp
(rollout* graph start steps)
```

生成:

例:

```text
[a1 a2 a3 a1 a2 a3]
```

---

## Step 2

Cycle extraction:

```lisp
(find-cycle path)
```

結果:

```text
[a3 a1 a2 a3]
```

---

## Step 3

Order normalization:

```lisp
(reverse ...)
```

結果:

```text
[a3 a2 a1 a3]
```

※ 現在コードでは cycle order の正規化方法は `reverse` に依存する。

---

# 13. Example

Graph:

```text
a1 → a2 → a3
↑         |
|---------|
```

---

Rollout:

```text
[a1 a2 a3 a1 a2 a3]
```

---

Detected cycle:

```text
[a1 a2 a3]
```

---

# 14. Relationship With Attractor Detection

現在の設計:

```text
find-recurrent-cycle

        |

        v

cycle

        |

        v

attractor candidate
```

---

Attractor definition:

```text
Attractor =
stable recurrent transition structure
```

---

# 15. Difference From Single-State Attractor

重要:

関数コメント:

```text
"return the observed recurrent cycle (not a single node)"
```

が示す通り、これは:

```text
旧:
attractor = node
```

ではなく:

```text
新:
attractor = cycle
```

として扱う。

---

# 16. Data Model Compatibility

Basin layer:

```lisp
(defstruct basin
  attractor
  nodes
  mass
  ratio)
```

との対応:

```text
basin-attractor

=

cycle object
```

例:

```text
(
 a1
 a2
 a3
)
```

---

# 17. Determinism Contract

同一:

```text
graph

start

steps
```

なら:

```text
same rollout

↓

same cycle
```

が保証される。

---

# 18. Limitations

## 18.1 Terminal Node Only Detection

現在:

```lisp
last-node
```

のみを基準に検出。

つまり:

```text
[a b c d b c d]
```

では:

期待:

```text
[b c d]
```

だが、

現在:

```text
d
```

基準になる可能性がある。

---

## 18.2 Multiple Cycle Handling

未対応:

```text
a b c a b c x y z
```

複数周期。

---

## 18.3 Cycle Length Validation

未実装:

```text
cycle length >= 2
```

などの制約。

---

# 19. Recommended Future Extension

## 19.1 General Cycle Detection

現在:

```text
last node repetition
```

↓

改善:

```text
detect repeated subsequence
```

---

例:

入力:

```text
[a b c d b c d]
```

検出:

```text
[b c d]
```

---

# 20. Formal Invariants

## CYCLE-1

Output is always a sequence.

```text
Cycle ∈ List
```

---

## CYCLE-2

Cycle represents observed transition order.

---

## CYCLE-3

No graph mutation occurs.

```text
find-cycle
=
pure analysis
```

---

## CYCLE-4

Cycle extraction does not affect rollout.

---

# 21. Chron-OS Mapping

```text
Event History

      |
      v

Graph

      |
      v

Trajectory

      |
      v

Recurrent Cycle

      |
      v

Attractor

      |
      v

Basin Structure
```

---

# 22. Design Assessment

## Strengths

### Minimal implementation

* small state surface
* deterministic
* easy replay

---

### Correct abstraction

Attractor を:

```text
single state
```

ではなく:

```text
recurrent transition pattern
```

として扱っている。

これは Chron-OS の worldline / event-stream モデルと整合する。

---

# 23. Current Implementation Classification

| 項目                   | 評価             |
| -------------------- | -------------- |
| Layer                | Graph Analysis |
| State Mutation       | None           |
| Determinism          | Yes            |
| Persistence          | None           |
| Authority            | None           |
| Replay Compatibility | Yes            |

---

# Final Specification Summary

```text
find-cycle extracts recurrent terminal cycles from rollout paths.

find-recurrent-cycle combines:

    Graph rollout
          +
    Cycle extraction

to produce:

    observed recurrent transition structure


The returned cycle represents:

    attractor candidate

not:

    a single terminal node.
```

この実装は、前段の `find-attractor` → `build-basin-map` → `build-basin-structure` の入口になる **Cycle-based Attractor Detector** として位置付けられます。
