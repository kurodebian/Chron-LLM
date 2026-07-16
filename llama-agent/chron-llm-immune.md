# Chron-LLM Δ3 World Service / Immune Service 仕様書

**Document Version** : Δ3 Phase1  
**Module** : World Service / Immune Service  
**Layer** : World Management Layer

---

# 1. 概要

本モジュールはChron-LLMにおける**世界線(World)管理**および**健全性判定(Immune Hook)**を提供する。

World Serviceは既存世界線から新しい世界線を分岐(Stage)する責務のみを持つ。

Immune ServiceはGraph Projectionから現在の世界線状態を取得し、その世界線が健全かどうかを判定する最小APIを提供する。

本モジュールはHistory・Graph・Runtime等の上位機能を実装しない。

---

# 2. アーキテクチャ

```
                 Runtime
                     │
                     ▼
              Immune Service
                     │
                     ▼
              World Service
                     │
                     ▼
            Graph Projection
                     │
                     ▼
            Write Ahead Log
```

---

# 3. 責務

## World Service

担当する機能

- 新規世界線生成
- World ID採番
- Branch Event生成
- 親世界線参照
- Branch Stage

---

## Immune Service

担当する機能

- 世界線健全性判定
- History存在確認
- Runtime Hook

---

# 4. 非責務

本モジュールは以下を実装しない。

- Branch Commit
- Merge
- History生成
- Graph生成
- Prompt生成
- Replay
- Validation
- Runtime制御
- Recovery
- Immune修復

---

# 5. Worldの概念

## World

Worldとは因果系列(Lineage)を識別する論理単位である。

```
World

↓

Dialogue

↓

Proposal

↓

Commit
```

各世界線は独立した因果履歴を持つ。

---

## World ID

Worldは整数IDで識別される。

```
100

101

102
```

IDはWALが管理する。

```
wal-world-counter
```

から単調増加で採番される。

---

# 6. Branch Model

```
            World100
                │
                │
          Branch Event
                │
                ▼
            World101
```

Branch自体もEventである。

---

# 7. World Service

## stage-branch-world()

### 目的

既存世界線から新しい世界線をStageする。

Commitは行わない。

---

## 入力

```
Graph

WriteAheadLog

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

# 8. アルゴリズム

## Step1

World ID採番

```
world-counter++

↓

new-world-id
```

---

## Step2

親世界線取得

```
Graph

↓

Latest Node
```

取得API

```
get-latest-node-in-world()
```

---

## Step3

親Event取得

```
Node

↓

Event

↓

Node ID
```

取得できない場合

```
0
```

を使用する。

これはRoot Branchを意味する。

---

## Step4

Branch Event生成

```
stage-event
```

呼び出し。

---

## Event Kind

```
:branch
```

---

## Causal ID

```
new-world-id
```

---

## Payload

```
Parent Node ID

Parent World ID
```

---

## Event構造

```
Kind

:branch

----------------

Causal ID

New World

----------------

Payload

Parent Node

Parent World
```

---

## Step5

戻り値

```
(values

new-world-id

event)
```

---

# 9. Branch Event

Branch Eventは世界線生成を表す。

Payload

```
parent-id

parent-world
```

を保持する。

これによりBranch Treeを再構築可能となる。

---

# 10. Root Branch

親Nodeが存在しない場合

```
Parent Node

=

0
```

となる。

これはRoot Worldを意味する。

---

# 11. World Counter

World Counterは

```
Write Ahead Log
```

で管理される。

World生成毎

```
counter++
```

される。

再利用されない。

---

# 12. Graph依存

World ServiceはGraphへ直接アクセスしない。

取得は

```
get-latest-node-in-world()
```

のみ利用する。

Graph構造を知らない。

---

# 13. Immune Service

## check-immune-status()

### 目的

世界線健全性を判定する。

---

## 入力

```
Graph

World ID
```

---

## 出力

```
:ok

または

:degraded
```

---

# 14. 判定アルゴリズム

```
History取得

↓

存在？

↓

Yes

↓

OK

No

↓

Degraded
```

---

## History取得

```
clean-history()
```

を利用する。

---

## 判定条件

History取得成功

```
:ok
```

History取得失敗

```
:degraded
```

---

# 15. Immune Hook

Immune ServiceはKernel Hookとして設計されている。

現在は

```
History存在確認
```

のみ実装。

将来

```
Fault解析

Loop検出

Consistency

Recovery

Confidence

Repair
```

等へ拡張可能。

---

# 16. Event Flow

```
Parent World

↓

Latest Node

↓

Branch Event

↓

Stage

↓

Commit (Future)

↓

Graph Projection

↓

History
```

---

# 17. 状態遷移

```
Parent World

      │

      ▼

Stage Branch

      │

      ▼

Branch Event

      │

      ▼

Commit

      │

      ▼

New World
```

---

# 18. データモデル

Branch Event

```
Kind

:branch

Causal ID

World ID

Payload

Parent Node

Parent World
```

---

Immune Status

```
:ok

:degraded
```

---

# 19. 不変条件

Branch生成後

- World IDは一意である。
- Parent Worldは変更されない。
- Parent NodeはCommit済Nodeを指す。
- Branch EventはStageされるだけでCommitされない。

---

Immune判定

- Historyが存在すれば健全。
- Historyが存在しなければ劣化。

---

# 20. 計算量

World生成

```
O(1)
```

---

Parent取得

```
O(1)
```

(Hash検索)

---

History取得

```
O(depth)
```

(depth=因果チェーン長)

---

Immune判定

```
O(depth)
```

---

# 21. Phase1制約

実装済

- World ID生成
- Branch Stage
- Parent World取得
- Parent Node取得
- Health判定

未実装

- Branch Commit
- Merge
- Multi Parent
- World Tree管理
- World Metadata
- World Replay
- Automatic Recovery
- Fault Isolation
- Immune Repair
- Branch Validation

---

# 22. 設計上の考察

## World Service

本実装では、世界線は**Branch EventとしてWALへ記録される**。

そのため、世界線そのものを永続化する独立データ構造は存在せず、WALのイベント列から再構築できることが前提となっている。

これはChron-LLM全体の「WALを唯一の真実(Source of Truth)とする」設計思想と一致する。

---

## Immune Service

Immune Serviceは現段階ではHistoryの有無のみで健全性を判定する最小実装である。

将来的には、

- Fault Event解析
- 因果整合性検査
- 信頼度評価
- 自己修復
- 世界線選択

などの高度なImmune機構へ発展するためのKernel Hookとして位置付けられる。

---

# 23. レビュー所見（実装との対応）

コードを精査すると、いくつか仕様として明記した方がよい点がある。

## 23.1 `event-id` の実体

コメントでは

> `stage-eventは戻り値としてnode-idを返す`

とありますが、実際の `stage-event` は**Eventオブジェクト全体を返しています**。

そのため `event-id` という変数名は実装と一致しておらず、

```
branch-event
```

などの名称の方が仕様・実装の双方に整合します。

---

## 23.2 Root Parent

親が存在しない場合に

```
parent-id = 0
```

を使用しています。

仕様としては、

- 0 を Root Sentinel とする

または

- NIL を Root とする

のどちらかを正式に定義した方が将来の拡張時に曖昧さがありません。

---

## 23.3 Immune判定

現状の

```
Historyが存在する
↓

Healthy
```

はあくまで**Phase1の暫定判定**です。

Historyが存在しても、

- Faultしか存在しない
- Broken Chain
- Commit失敗

などのケースでは健全とは限らないため、将来フェーズでは判定基準を拡張することが前提となります。