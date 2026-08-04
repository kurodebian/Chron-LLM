# Chron-LLM Δ3 Write Ahead Log (WAL) 仕様書

**Document Version** : Δ3 Phase1  
**Module** : Write Ahead Log  
**Layer** : Persistence Primitive

---

# 1. 概要

## 1.1 目的

Write Ahead Log（以下 WAL）は、Chron-LLM における最小単位の永続化機構である。

WALはイベントを生成・保持・コミットする責務のみを持ち、履歴管理やグラフ構築などの高次機能は担当しない。

Chron-LLM全体では最下層に位置するPersistence Primitiveであり、上位レイヤはすべてWAL上に構築される。

---

# 2. 設計方針

## Design Philosophy

WALは以下の原則を満たす。

- 最小責務
- 決定論
- Append Only
- 単調増加Clock
- 一意Node ID
- Stage → Commit の二段階更新

WAL自身はイベントの意味を理解しない。

イベントを保存することだけを責務とする。

---

# 3. 責務

WALが担当するもの

- Event生成
- Stage管理
- Commit
- Batch Commit
- Rollback(Stageのみ)
- Event永続化
- Clock管理
- Node ID管理
- World ID管理

---

# 4. 非責務

以下はWALでは実装しない。

- History
- Graph
- Branch管理
- Merge
- Runtime
- Prompt
- LLM
- Immune
- Memory Search
- Event Validation
- Causal Validation

これらは将来レイヤで実装される。

---

# 5. クラス構成

## write-ahead-log

```
write-ahead-log
 ├── storage
 ├── staged-events
 ├── clock
 ├── node-counter
 └── world-counter
```

---

## 5.1 storage

### 目的

Commit済イベントを保存する。

### 型

```
Adjustable Vector
```

### 初期容量

```
64
```

### 性質

Append Only

削除は行わない。

---

## 5.2 staged-events

### 目的

Commit前イベントを一時保持する。

### 型

```
Adjustable Vector
```

### 初期容量

```
8
```

### 性質

Commitされるまで永続化されない。

---

## 5.3 clock

### 目的

Commit順序を保証する単調増加Clock

### 初期値

```
0
```

### 更新タイミング

commit-event実行時

```
clock++
```

---

## 5.4 node-counter

### 目的

全Eventに対する一意Node ID生成

### 初期値

```
1000
```

生成時

```
node-counter++
```

---

## 5.5 world-counter

### 目的

将来のBranch(Lineage)識別

### 初期値

```
100
```

Phase1では未使用。

---

# 6. Event Lifecycle

```
             make-event
                  │
                  ▼
             stage-event
                  │
         staged-events
          │          │
 rollback │          │ commit
          ▼          ▼
      discard    commit-event
                      │
                      ▼
                   storage
```

---

# 7. Validation

## invariant-check-p

### 目的

Commit前不変条件検査

### 入力

```
WAL
Events
```

### 出力

```
Boolean
```

### 現在

```
常に true
```

---

## 将来追加予定

- Duplicate Detection
- Event Validation
- Clock Validation
- Node Validation
- Causal Validation
- World Validation

---

# 8. Commit Primitive

## commit-event()

### 責務

単一EventをCommitする。

### 入力

```
WAL
Event
```

### 処理

#### Step1

Clock更新

```
clock++
```

#### Step2

EventへClock設定

```
event.clock = clock
```

#### Step3

Storageへ追加

```
storage.push(event)
```

#### Step4

Event返却

---

### 更新対象

```
clock
storage
event.clock
```

---

# 9. Immediate Commit

## append-event()

### 目的

Stageを介さず即時Commitする。

### 処理

```
make-event
     │
     ▼
commit-event
```

### Event生成

```
node-id
causal-id
kind
payload
```

Node IDは自動採番。

---

# 10. Stage

## stage-event()

### 目的

Commit前イベント生成

### 処理

```
make-event
      │
      ▼
staged-events.push
```

### 特徴

この時点では

```
clock未設定
```

である。

---

# 11. Rollback

## discard-staged()

### 処理

```
fill-pointer = 0
```

Stage内容を破棄する。

Storageには影響しない。

---

## rollback-stage()

現在実装

```
rollback
=
discard
```

将来

UndoやTransactionへ拡張可能。

---

# 12. Batch Commit

## commit-staged()

### 目的

Stage済イベントをまとめてCommit

---

### アルゴリズム

```
Invariant Check

↓

foreach Event

↓

commit-event

↓

Committed Vector生成

↓

Stage削除
```

---

### 戻り値

```
(values
 success
 committed-events)
```

success

```
t
```

committed-events

```
Vector<Event>
```

---

# 13. Utility

## clear-wal()

### 目的

初期状態へ戻す。

主用途

- Unit Test
- Integration Test

---

### 初期化対象

Storage

```
[]
```

Stage

```
[]
```

Clock

```
0
```

Node Counter

```
1000
```

World Counter

```
100
```

---

# 14. State Machine

```
                +-----------+
                |   Stage   |
                +-----------+
                 |         |
     rollback    |         | commit
                 |         |
                 ▼         ▼
          +------------+  +--------------+
          | Discarded  |  |  Committed   |
          +------------+  +--------------+
```

---

# 15. 不変条件

Commit完了後は以下を保証する。

## Clock

```
Clockは単調増加
```

---

## Node ID

```
Node IDは一意
```

---

## Storage

```
Storage順
=
Commit順
```

---

## Stage

Commit後

```
Stageは空
```

---

## Event

Commit済EventはStorageのみに存在する。

---

# 16. 計算量

append-event

```
O(1)
```

---

stage-event

```
O(1)
```

---

commit-event

```
O(1)
```

---

commit-staged

```
O(n)
```

n = Stage Event数

---

clear-wal

```
O(1)
```

（fill-pointerのみ変更）

---

# 17. Phase1制約

実装済

- Stage
- Commit
- Batch Commit
- Rollback
- Clock
- Node ID
- Memory WAL

未実装

- Validation
- Persistent Storage(File)
- History
- Graph
- Branch
- Merge
- Replay
- Immune
- Runtime
- Prompt
- Search

---

# 18. レイヤ構成

```
+-----------------------+
| Runtime               |
+-----------------------+

+-----------------------+
| Prompt Builder        |
+-----------------------+

+-----------------------+
| Proposal / Review     |
+-----------------------+

+-----------------------+
| History (Future)      |
+-----------------------+

+-----------------------+
| Graph (Future)        |
+-----------------------+

+-----------------------+
| Write Ahead Log       |
|  Stage                |
|  Commit               |
|  Clock                |
|  Node Allocation      |
+-----------------------+
```

---

# 19. インターフェース

## Public API

|関数|概要|
|----|----|
|`append-event`|即時Commit|
|`stage-event`|Stage追加|
|`commit-staged`|Batch Commit|
|`rollback-stage`|Stage Rollback|
|`discard-staged`|Stage破棄|
|`clear-wal`|初期化|

---

# 20. 将来拡張

Phase2

- Event Validation
- Invariant Rule
- Duplicate Detection
- Causal Validation

Phase3

- Persistent File WAL
- Replay
- Crash Recovery

Phase4

- Branch
- Merge
- World Management

Phase5

- History
- Graph
- Knowledge Layer

---

# 21. Chron-LLMにおける位置付け

WALはChron-LLM全体の**唯一の永続化プリミティブ**である。

すべての状態変化はEventとしてWALへ記録され、上位レイヤ（History・Graph・Knowledge・Runtime）はそのEvent列を解釈して構築される。

したがって、WALはイベントの意味を解釈せず、「順序付けられたイベント列を決定論的に保存する」ことのみを責務とする。

この責務の限定により、Chron-LLMは各レイヤを疎結合に保ち、Replay・Branch・History・Knowledgeなどの機能を上位層で段階的に構築できるアーキテクチャとなっている。