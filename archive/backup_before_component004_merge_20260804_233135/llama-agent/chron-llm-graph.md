# Chron-LLM Δ3 Graph Projection Service 仕様書

**Document Version** : Δ3 Phase1  
**Module** : Graph Projection Service  
**Layer** : Projection Layer

---

# 1. 概要

## 1.1 目的

Graph Projection Service は、Write Ahead Log(WAL)に永続化されたイベント列から因果グラフ(Causal Graph)を再構築するサービスである。

本サービスはイベントを解釈して状態遷移を計算するのではなく、WALに存在するCommit済みイベント列を読み取り、Graph Projectionを生成することのみを責務とする。

GraphはProjectionであり、真実(Source of Truth)ではない。

唯一の真実はWALである。

---

# 2. アーキテクチャ上の位置付け

```
                     Runtime
                         │
                         ▼
                  Prompt Builder
                         │
                         ▼
                     History
                         │
                         ▼
                Graph Projection
                         │
                         ▼
                  Write Ahead Log
```

GraphはWALからいつでも再構築可能である。

Graphは永続化対象ではない。

---

# 3. 責務

Graph Projection Serviceは以下のみを担当する。

- WALからGraph再構築
- Node生成
- Temporal Edge生成
- Causal Edge生成
- Parent Lookup Table構築
- Latest Healthy Node管理
- History Projection

---

# 4. 非責務

本サービスは以下を行わない。

- Event Validation
- Immune判定
- Prompt生成
- History Summary生成
- Replay制御
- Runtime管理
- Branch管理
- Merge
- WAL更新

Projectionは常にCommit済イベントを前提とする。

---

# 5. 基本概念

## Projection

Graphは保存対象ではない。

```
WAL

↓

Projection

↓

Graph
```

Graphは必要時に再構築される。

---

## Source of Truth

```
Truth = WAL

Graph = Cache / Projection
```

Graphは削除可能である。

削除後もWALから完全復元できる。

---

# 6. Graph Reconstruction

## rebuild-graph-from-wal()

### 目的

Commit済WALからGraphを再構築する。

### 入力

```
WriteAheadLog
```

### 出力

```
CausalGraph
```

### 処理

```
lift-to-graph()
```

を呼び出すだけのFacadeである。

---

# 7. Projection Algorithm

## lift-to-graph()

### 目的

WALイベント列をGraphへ射影する。

---

## 初期状態

Graph生成

```
graph
```

Temporal Cursor

```
last-temporal-id=nil
```

Healthy Table

```
causal-id
      ↓
latest healthy node
```

Global Healthy

```
global-last-healthy-id=nil
```

---

## イベント処理

WALを先頭から順番に走査する。

```
for event in WAL
```

各イベントについて

```
Node生成

↓

Temporal Edge

↓

Causal Edge

↓

Healthy Table更新

↓

Cursor更新
```

を行う。

---

# 8. Node Construction

## add-node-to-graph()

### 入力

```
Graph
Event
```

### 出力

```
CausalNode
```

---

## Node構成

```
Node ID

Clock

Class

Event

Causal ID
```

---

## Node Class

Node種別は

```
determine-node-class()
```

により決定される。

Projectionではイベント内容を解釈しない。

---

## 登録

```
graph.nodes

node-id

↓

node
```

HashTableへ登録される。

---

# 9. Temporal Edge

Temporal Edgeは

```
Commit順序
```

を表現する。

生成規則

```
previous node

↓

current node
```

Edge種別

```
:temporal
```

生成条件

```
前ノード存在
```

---

## 性質

Temporal Edgeは必ず一本の線形系列となる。

```
1

↓

2

↓

3

↓

4
```

---

# 10. Causal Edge

Causal Edgeは

```
因果継承
```

を表現する。

生成規則

```
Parent

↓

Current
```

Edge種別

```
:causal
```

---

## Parent探索

Parentは

```
find-parent-node-id()
```

によって取得される。

探索順

```
同一Causal ID

↓

Global Healthy

↓

nil
```

---

## Parent Lookup

```
causal-id

↓

last healthy node
```

をHashTableで管理する。

---

# 11. Healthy Table

Healthy Tableは

```
Fault以外
```

のみ記録する。

```
Fault

×

Healthy

○
```

登録条件

```
Node Class != :fault
```

---

## 更新内容

```
causal-id

↓

latest healthy node
```

同時に

```
global-last-healthy-id
```

も更新される。

---

# 12. Temporal Cursor

Cursorは

```
最後に処理したNode
```

を保持する。

毎イベント

```
last-temporal-id

=

current node
```

となる。

---

# 13. Parent Lookup

## find-parent-node-id()

### 入力

```
causal-id

Healthy Table

Fallback
```

### 出力

```
Parent Node ID
```

---

### 探索

```
Healthy Table

↓

Found

↓

Return

Else

↓

Fallback
```

---

# 14. Parent取得

## get-parent-node-id()

Graph内Parent取得

```
child

↓

parent
```

HashTable検索のみ。

---

# 15. Edge Operations

## add-edge()

Edge生成

入力

```
kind

from

to
```

Edge生成後

```
graph.edges
```

へ追加される。

---

## add-causal-edge()

処理

```
Edge生成

↓

Parent Table更新
```

Parent Table

```
child

↓

parent
```

---

# 16. History Query

## graph-history()

### 目的

GraphからDialogue Historyを取得する。

---

### 入力

```
Graph

World ID
```

---

### アルゴリズム

取得開始

```
latest healthy node
```

↓

Parentを辿る

↓

Root到達

↓

終了

---

### History対象

Node Class

```
:dialogue
```

のみHistoryへ追加する。

他Nodeは通過する。

---

### 結果

```
Newest

↓

...

↓

Oldest
```

となる。

---

# 17. Latest Healthy

Graphには

```
World

↓

Latest Healthy Node
```

のLookup Tableを保持する。

検索は

```
O(1)
```

となる。

---

# 18. データ構造

Graph

```
Nodes(Hash)

Edges(Vector)

Parents(Hash)

Latest Healthy(Hash)
```

Node

```
ID

Clock

Class

Event

Causal ID
```

Edge

```
Kind

From

To
```

---

# 19. 計算量

Graph Reconstruction

```
O(n)
```

n=WALイベント数

---

Node Lookup

```
O(1)
```

---

Parent Lookup

```
O(1)
```

---

Latest Healthy Lookup

```
O(1)
```

---

History Query

```
O(depth)
```

depth=因果チェーン長

---

# 20. 不変条件

Projection終了後

## Node

全Commit Eventに対応するNodeが存在する。

---

## Temporal Edge

全NodeはCommit順に接続される。

---

## Parent

Parent Tableは最新Parentを保持する。

---

## Healthy Table

Fault Nodeは登録されない。

---

## Projection

GraphはWALのみから完全再構築可能。

---

# 21. Phase1制約

実装済

- Projection
- Node生成
- Temporal Edge
- Causal Edge
- Parent Lookup
- Healthy Table
- History Query

未実装

- Branch Projection
- Merge Projection
- Multi World
- Graph Cache
- Incremental Projection
- Validation
- Immune Integration
- History Service分離

---

# 22. Backward Compatibility

## clean-history()

旧API互換のため存在する。

実装

```
clean-history()

↓

graph-history()
```

将来的には削除予定。

---

# 23. 設計思想

Graph Projection Serviceは「イベントの意味」を解釈しない。

ProjectionはCommit済イベントを因果グラフへ写像するだけであり、Validation・Immune・History・Runtimeなどの高次処理はすべて上位レイヤに委譲される。

この責務分離により、

- WALは唯一の永続化層
- Graphは再構築可能なProjection
- HistoryはGraph上のビュー
- RuntimeはHistoryを利用する実行層

という明確なレイヤ構造が維持される。

Graphは常にWALから決定論的に再生成できるため、永続化や同期を必要とせず、Replay・Branch・History・Knowledgeなどの上位機能の基盤となる。