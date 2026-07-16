# Chron-LLM Δ3 World Service 仕様書

**Document Version** : Δ3 Phase1  
**Module** : World Service  
**Layer** : World Management Layer

---

# 1. 概要

## 1.1 目的

World Service は Chron-LLM における**世界線（World）管理サービス**である。

本モジュールは、

- 世界線の分岐（Branch）
- 世界線の検索（Query）

のみを責務とする。

世界線自体は独立した永続オブジェクトではなく、**WALに記録される Branch Event により定義される論理概念**である。

---

# 2. アーキテクチャ上の位置付け

```
                    Runtime
                        │
                        ▼
                  Kernel Service
                        │
                        ▼
                 World Service
                 ├──────────────┐
                 ▼              ▼
          Graph Projection      WAL
```

World Service は

- Graphから現在状態を取得する
- WALへBranch Eventを生成する

という仲介層である。

---

# 3. 設計思想

World は状態ではなく

```
Event
```

によって生成される。

つまり

```
World

≠ Object

World

= Branch Eventの系列
```

である。

そのためWorld情報もReplayによって完全復元可能である。

---

# 4. 責務

本サービスが担当する機能

- 新規World生成
- World ID採番
- Branch Event生成
- Parent Node取得
- Parent World管理
- World検索
- 最新Node取得

---

# 5. 非責務

本サービスは以下を担当しない。

- Branch Commit
- Merge
- History構築
- Graph構築
- Validation
- Replay
- Runtime管理
- Immune判定
- Prompt生成
- Memory管理

---

# 6. Worldの概念

Worldとは

```
独立した因果系列
```

を識別する論理IDである。

各Worldは

```
World ID

↓

Dialogue

↓

Proposal

↓

Commit
```

という因果列を持つ。

---

# 7. World Identifier

Worldは整数で識別される。

```
100

101

102
```

生成元

```
wal-world-counter
```

特徴

- 単調増加
- 再利用しない
- 一意

---

# 8. Branching Model

```
          World100
              │
              │
        Branch Event
              │
              ▼
          World101
```

Branch自体もWAL Eventである。

---

# 9. stage-branch-world()

## 目的

既存Worldから新しいWorldを生成する。

Commitは行わず

```
Stage
```

のみ行う。

---

## 入力

```
Graph

Write Ahead Log

Parent World ID
```

---

## 出力

```
(values

 New World ID

 Branch Event)
```

---

# 10. Branch生成アルゴリズム

## Step1

World ID採番

```
world-counter++

↓

new-world-id
```

---

## Step2

親World検索

```
get-latest-node-in-world()
```

実行

---

## Step3

親Node取得

```
Latest Node

↓

Event

↓

Node ID
```

---

## Root World

親Nodeが存在しない場合

```
Parent Node

=

0
```

とする。

これはRoot Branchを意味する。

---

## Step4

Branch Event生成

```
stage-event()
```

呼び出し

---

### Kind

```
:branch
```

---

### Causal ID

```
New World ID
```

---

### Payload

```
Parent Node

Parent World
```

---

## Step5

戻り値

```
(values

new-world-id

event-node-id)
```

StageされたBranch Eventが返される。

---

# 11. Branch Event構造

Branch Eventは以下の情報を持つ。

```
Kind

:branch

-------------------

Causal ID

World ID

-------------------

Payload

Parent Node

Parent World
```

これにより

```
Branch Tree
```

を復元できる。

---

# 12. World Query

## get-latest-node-in-world()

### 目的

指定Worldに属する

```
最新かつ健全
```

なNodeを返す。

---

## 入力

```
Graph

World ID
```

---

## 出力

```
Causal Node

または

NIL
```

---

# 13. World検索アルゴリズム

Graph内Node全体を走査する。

```
for node in Graph
```

各Nodeについて

```
World一致

↓

Faultでない

↓

最新IDなら更新
```

を実行する。

---

## 判定条件

### World一致

```
Node.CausalID

==

WorldID
```

---

### Fault除外

```
Node.Class

!=

:fault
```

---

### 最新判定

```
NodeID

>

LatestID
```

なら更新。

---

# 14. 最新判定

本実装では

```
Node ID
```

を時系列順序として利用する。

これは

```
WAL

↓

Node Counter
```

が単調増加することを前提としている。

---

# 15. Root World

該当Worldが存在しない場合

```
NIL
```

を返す。

Branch生成側では

```
Parent ID

=

0
```

として扱われる。

---

# 16. データフロー

```
Parent World

↓

Latest Node Search

↓

Parent Node

↓

Branch Event

↓

Stage

↓

Commit (Kernel)
```

---

# 17. 状態遷移

```
World100

      │

      ▼

Branch

      │

      ▼

Stage

      │

      ▼

Commit

      │

      ▼

World101
```

---

# 18. データモデル

## World

```
World ID

Latest Node

Parent World
```

---

## Branch Event

```
Kind

:branch

Causal ID

Payload
```

---

# 19. 計算量

## World生成

```
O(1)
```

---

## Parent Node取得

```
O(n)
```

Graph全体を走査する。

n = Node数

---

## Branch Stage

```
O(1)
```

---

# 20. 不変条件

Branch生成後

- World IDは一意
- Parent Worldは変更されない
- Parent NodeはCommit済Node
- Branch EventはStageのみ
- Root Parentは0

---

World Query

- Fault Nodeは返さない
- 同一World中で最新Nodeのみ返す

---

# 21. Phase1制約

実装済

- Branch Stage
- World生成
- Parent検索
- 最新Node取得

未実装

- Branch Commit
- Merge
- Multi Parent
- World Metadata
- World Tree
- Replay
- Incremental Index
- Branch Validation

---

# 22. 設計原則

World Serviceは

```
World生成
```

と

```
World検索
```

のみを担当する。

HistoryやGraph構築はGraph Serviceへ委譲し、

永続化はWALへ委譲する。

これにより

```
World

↓

Graph

↓

WAL
```

という責務分離が維持される。

---

# 23. 将来拡張

Phase2以降

```
World Tree

↓

Branch Metadata

↓

Merge

↓

Replay

↓

Snapshot

↓

Incremental World Index
```

を追加予定。

---

# 24. コードレビュー・設計評価

## 24.1 改善点

このバージョンでは旧実装より責務が明確になっており、

- `Immune Service` が完全に分離された
- `World Query` が World Service に統合された

ため、モジュール構成として自然になっています。

---

## 24.2 `event-node-id` の命名

`stage-event` の戻り値は実際には **Eventオブジェクト**です。

したがって

```lisp
(let ((event-node-id
       (stage-event ...)))
```

という名前は実装と一致していません。

仕様としては

```text
branch-event
```

または

```text
staged-event
```

の方が適切です。

---

## 24.3 最新Node探索の計算量

現在の

```lisp
get-latest-node-in-world()
```

は

```
Graph全走査

↓

最新Node決定
```

となるため **O(n)** です。

将来的には Graph に

```
World ID

↓

Latest Node
```

というインデックスを持たせれば

```
O(1)
```

で取得できます。

---

## 24.4 Node IDによる最新判定

現在は

```lisp
Node ID > Latest ID
```

で最新を判定しています。

これは **Node ID が生成順＝Commit順である**ことを前提にしています。

設計としては問題ありませんが、仕様では「最新」の基準を **Node ID** ではなく **Commit Clock** と定義した方が、将来Node IDの生成方式が変わっても意味論が保たれます。

---

# 25. 総合評価

本モジュールは **「世界線の生成」と「世界線の検索」** に責務を限定した非常にミニマルな設計となっています。

特に、

- Worldは独立オブジェクトではなく **Branch Eventで表現する**
- Graphは検索のみ担当する
- WALが唯一の永続化層である

というChron-LLM全体のアーキテクチャ方針と整合しています。

一方で、現状の検索は線形探索であるため、Phase2以降では **Worldインデックス** や **Latest Nodeキャッシュ** の導入が有力な拡張ポイントとなります。