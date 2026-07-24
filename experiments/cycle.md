# Recurrent Cycle Detection Specification v1.0

## Rollout-Based Cycle Extraction Module

# 1. Overview

## 1.1 Purpose

`find-cycle` および `find-recurrent-cycle` は、Graph Runtime 上で生成された状態遷移列（rollout path）から **再帰的に出現する周期構造（recurrent cycle）** を抽出するための解析プリミティブである。

本モジュールの目的:

* rollout trajectory の終端周期検出
* attractor candidate の抽出
* cyclic state transition の観測
* basin analysis への入力生成

# 2. Architectural Position

```
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

# 3. Responsibility Boundary

## 3.1 Responsible

本モジュールは:

| Function                    | Responsibility |
| --------------------------- | -------------- |
| Path inspection             | ✓              |
| Cycle extraction            | ✓              |
| Recurrent pattern detection | ✓              |
| Cycle representation        | ✓              |

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

# 4. Function Specification

# 4.1 find-cycle

## Definition

```
(defun find-cycle (path)
  "Given a rollout path, extract the recurrent cycle at the end.")
```

## Purpose

Rollout path の末尾に存在する再帰部分を抽出する。

入力:

```
State trajectory
```

出力:

```
Cycle sequence
```

# 5. Input Model

## Path

想定形式:

```
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

```
[a b c a b c]
```

# 6. Algorithm

## Step 1

Path reverse:

```
(reverse path)
```

例:

Before:

```
[a b c a b c]
```

After:

```
[c b a c b a]
```

## Step 2

Get final node:

```
(last-node (car rev))
```

つまり:

```
last-node = original path end
```

例:

```
path:

[a b c a b c]

last-node:

c
```

## Step 3

Search previous occurrence

```
(position last-node (cdr rev))
```

目的:

末尾状態が過去に存在するか確認。

# 7. Cycle Extraction Logic

## Case 1: Cycle Exists

例:

入力:

```
[a b c a b c]
```

reverse:

```
[c b a c b a]
```

探索:

```
c
```

再出現:

```
index = 3
```

取得:

```
(subseq rev 0 (1+ pos))
```

結果:

```
[c b a c]
```

その後:

```
(reverse result)
```

により:

```
[c a b c]
```

となる。

## Case 2: No Cycle

例:

```
[a b c d]
```

末尾:

```
d
```

過去に存在しない。

結果:

```
(list last-node)
```

返却:

```
[d]
```

# 8. Return Contract

`find-cycle` は必ず list を返す。

## Cycle Found

```
(
 cycle start
 ...
 repeated node
)
```

## Cycle Not Found

```
(
 last-node
)
```

# 9. find-recurrent-cycle

## Definition

```
(defun find-recurrent-cycle (graph start steps)
  "Rollout and return the observed recurrent cycle (not a single node).")
```

# 10. Purpose

Graph 上で rollout を実行し、その結果から周期構造を返す。

# 11. Execution Flow

```
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

# 12. Internal Processing

## Step 1

Rollout:

```
(rollout* graph start steps)
```

生成:

例:

```
[a1 a2 a3 a1 a2 a3]
```

## Step 2

Cycle extraction:

```
(find-cycle path)
```

結果:

```
[a3 a1 a2 a3]
```

## Step 3

Order normalization:

```
(reverse ...)
```

結果:

```
[a3 a2 a1 a3]
```

※ 現在コードでは cycle order の正規化方法は `reverse` に依存する。

# 13. Example

Graph:

```
a1 → a2 → a3
↑         |
|---------|
```

Rollout:

```
[a1 a2 a3 a1 a2 a3]
```

Detected cycle:

```
[a1 a2 a3]
```

# 14. Relationship With Attractor Detection

現在の設計:

```
find-recurrent-cycle

        |

        v

cycle

        |

        v

attractor candidate
```

Attractor definition:

```
Attractor =
stable recurrent transition structure
```

# 15. Difference From Single-State Attractor

重要:

関数コメント:

```
"return the observed recurrent cycle (not a single node)"
```

が示す通り、これは:

```
旧:
attractor = node
```

ではなく:

```
新:
attractor = cycle
```

として扱う。

# 16. Data Model Compatibility

Basin layer:

```
(defstruct basin
  attractor
  nodes
  mass
  ratio)
```

との対応:

```
basin-attractor

=

cycle object
```

例:

```
(
 a1
 a2
 a3
)
```

# 17. Determinism Contract

同一:

```
graph

start

steps
```

なら:

```
same rollout

↓

same cycle
```

が保証される。

# 18. Limitations

## 18.1 Terminal Node Only Detection

現在:

```
last-node
```

のみを基準に検出。

つまり:

```
[a b c d b c d]
```

では:

期待:

```
[b c d]
```

だが、

現在:

```
d
```

基準になる可能性がある。

## 18.2 Multiple Cycle Handling

未対応:

```
a b c a b c x y z
```

複数周期。

## 18.3 Cycle Length Validation

未実装:

```
cycle length >= 2
```

などの制約。

# 19. Recommended Future Extension

## 19.1 General Cycle Detection

現在:

```
last node repetition
```

↓

改善:

```
detect repeated subsequence
```

例:

入力:

```
[a b c d b c d]
```

検出:

```
[b c d]
```

# 20. Formal Invariants

## CYCLE-1

Output is always a sequence.

```
Cycle ∈ List
```

## CYCLE-2

Cycle represents observed transition order.

## CYCLE-3

No graph mutation occurs.

```
find-cycle
=
pure analysis
```

## CYCLE-4

Cycle extraction does not affect rollout.

# 21. Chron-OS Mapping

```
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

# 22. Design Assessment

## Strengths

### Minimal implementation

* small state surface
* deterministic
* easy replay

### Correct abstraction

Attractor を:

```
single state
```

ではなく:

```
recurrent transition pattern
```

として扱っている。

これは Chron-OS の worldline / event-stream モデルと整合する。

# 23. Current Implementation Classification

| 項目                   | 評価             |
| -------------------- | -------------- |
| Layer                | Graph Analysis |
| State Mutation       | None           |
| Determinism          | Yes            |
| Persistence          | None           |
| Authority            | None           |
| Replay Compatibility | Yes            |

# Final Specification Summary

```
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
