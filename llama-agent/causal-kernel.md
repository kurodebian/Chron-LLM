# Chron-LLM Δ3 Phase A–D リファレンス実装 仕様書

**Document Version** : Δ3 Phase A–D Prototype  
**Module** : Reference Causal Kernel Prototype  
**Purpose** : Chron-LLM 因果カーネルの概念実証 (Proof of Concept)

---

# 1. 概要

本モジュールは Chron-LLM Δ3 の最初期リファレンス実装であり、

- Event ABI
- Write Ahead Log
- Stage / Commit
- Graph Projection
- Clean History
- Branch Simulation

までを一つのファイルで実装したプロトタイプである。

これは後に

- WAL Service
- Graph Service
- Kernel
- World Service

へ分離された設計の原型となる。

---

# 2. 設計目的

本コードは

```
LLMの非決定性

↓

因果イベント化

↓

永続化

↓

Replay可能

↓

History抽出
```

が成立することを検証するためのPoCである。

---

# 3. モジュール構成

```
Phase A
    Event ABI

Phase B
    WAL

Phase C
    Graph

Phase D
    Graph Projection

Simulation
```

---

# 4. アーキテクチャ

```
LLM

↓

Event

↓

Write Ahead Log

↓

Graph Projection

↓

History

↓

Simulation
```

Graphは永続化されない。

---

# 5. Event ABI

## event

```
Index

Clock

Causal ID

Kind

Payload
```

---

### index

WAL内位置

---

### clock

Commit順序

---

### causal-id

世界線ID

---

### kind

イベント種類

---

### payload

Property List

---

# 6. Event設計

Header

```
Index

Clock

World
```

Payload

```
Text

Target

Metadata
```

HeaderはKernel管理を想定している。

---

# 7. WAL

## write-ahead-log

保持情報

```
Storage

Clock

Stage Queue
```

---

### storage

永続Event

```
Vector<Event>
```

---

### clock

単調増加論理時計

---

### staged-events

Commit待機Event

---

# 8. WAL API

実装されるAPI

```
append-event

stage-event

discard-staged

commit-staged
```

---

# 9. append-event()

即時Commit。

処理

```
Clock++

↓

Event生成

↓

Storage追加
```

Stageを経由しない。

---

# 10. stage-event()

目的

仮Event生成

処理

```
Speculative Clock

↓

Stage Queue
```

Clockは

```
wal-clock+1
```

を仮設定する。

Commit時に再設定される。

---

# 11. discard-staged()

Stage Queue破棄。

```
Rollback
```

相当。

---

# 12. commit-staged()

Stage Queue

↓

Commit

↓

Clock再採番

↓

Storage追加

↓

Stage削除

---

Commit順

```
reverse
```

を利用する。

これは

```
push
```

で逆順に格納されるためである。

---

# 13. Graph

## causal-node

Graph上Node

保持情報

```
ID

Event

Class

Clock

World
```

---

# 14. Node Class

determine-node-class()

分類

Dialogue

```
:user-message

:assistant-reply
```

---

Tool

```
tool-call-start

tool-call-timeout

tool-call-abort

tool-call-commit
```

---

Fault

```
structural-fault

tool-fault
```

---

Meta

その他

---

# 15. Graph構造

保持

```
Nodes

Edges

Parent Map
```

Nodes

```
Hash
```

Edges

```
Vector
```

Parents

```
Hash
```

---

# 16. Projection

lift-to-graph()

目的

```
WAL

↓

DAG
```

生成

---

# 17. Projectionアルゴリズム

各Event

↓

Node生成

↓

Temporal Edge

↓

Causal Edge

↓

Healthy更新

---

# 18. Temporal Edge

```
Last Node

↓

Current Node
```

全Eventを時間順接続。

---

# 19. Causal Edge

```
同一World

↓

最後のHealthy

↓

Current
```

Faultは継承しない。

---

# 20. Healthy Table

Hash

```
World

↓

Latest Healthy Node
```

Projection中のみ保持。

---

# 21. Clean History

clean-history()

目的

```
世界線

↓

健全履歴
```

抽出。

---

# 22. History抽出

処理

```
最新Healthy

↓

Parent

↓

Parent

↓

Root
```

Dialogueのみ返す。

---

# 23. Fault処理

Fault Node

↓

History除外

↓

継承停止

これにより

```
Clean History
```

が生成される。

---

# 24. Simulation

run-causal-kernel-simulation()

目的

Chron Kernel動作検証。

---

# 25. シミュレーションシナリオ

開始

```
World100
```

---

User

```
こんにちは
```

---

Assistant

```
好調
```

---

Tool Start

```
Blender
```

---

Tool Timeout

---

Assistant生成開始

↓

Stage

↓

途中破綻

↓

Discard

↓

Fault

↓

Branch

↓

World101

↓

Retry Reply

↓

Commit

---

# 26. Branch

```
100

↓

101
```

Branch後

Assistantは

```
World101
```

へ保存。

---

# 27. Debug API

dump-wal()

WAL表示。

---

dump-clean-history()

History表示。

---

# 28. 出力

Simulation終了後

```
WAL

↓

Graph

↓

History100

↓

History101
```

表示。

---

# 29. データフロー

```
User

↓

Event

↓

WAL

↓

Projection

↓

History

↓

Console
```

---

# 30. 状態遷移

```
Dialogue

↓

Tool

↓

Timeout

↓

Stage

↓

Discard

↓

Fault

↓

Branch

↓

Retry

↓

Commit
```

---

# 31. 不変条件

Commit後

```
Clock増加

Index増加

History再構築可能
```

Fault

```
History継承停止
```

---

# 32. 計算量

Append

```
O(1)
```

---

Stage

```
O(1)
```

---

Commit

```
O(n)
```

---

Projection

```
O(n)
```

---

History

```
O(depth)
```

---

# 33. この実装の特徴

本実装では

```
Fault

↓

Branch

↓

Recovery
```

というChron-LLM最大の特徴を最初に実証している。

LLMが途中まで生成した内容は

```
Stage
```

にのみ存在し、

構造破綻を検知すると

```
Discard
```

される。

そのため永続履歴は常に健全状態のみ保持する。

---

# 34. Phase A–Dで確立された設計

このPoCから後のΔ3実装へ継承された主要概念は以下である。

- Event ABI
- WAL中心アーキテクチャ
- Stage → Commitモデル
- Graph Projection
- Temporal Edge
- Causal Edge
- Clean History
- Fault Isolation
- Branch Recovery

現在のChron-LLMではこれらが個別サービスへ分割されている。

---

# 35. コードレビュー・設計評価

## 35.1 優れている点

このPoCは非常に小さなコード量で、

- WAL
- Projection
- Fault Isolation
- Branch

というChron-LLMの根幹概念を検証しています。

「LLMの途中生成は永続化せず、Commit済みイベントのみが真実である」という思想は、この時点ですでに明確です。

---

## 35.2 後の実装との相違点

この実装では以下が1ファイルに集約されています。

- Event ABI
- WAL
- Graph
- Projection
- Simulation

後のΔ3では

```
chron-llm-wal.lisp
chron-llm-graph.lisp
chron-llm-world.lisp
chron-llm-kernel.lisp
chron-llm-runtime.lisp
```

へ責務分離されています。

---

## 35.3 `index` を Node ID として利用

`lift-to-graph()` では

```lisp
(node-id (ev-index event))
```

としており、WALインデックスをNode識別子にしています。

後の実装では

```
node-id
```

が独立採番されるよう改善され、WAL配置と論理ノード識別子が分離されました。

---

## 35.4 `clean-history()` の探索

最新ノード探索は

```lisp
maximize id
```

による全探索です。

後の実装では

```
Latest Healthy Table
```

をGraphへ保持することで、世界線ごとの最新ノード取得を高速化する設計へ発展しています。

---

# 36. 歴史的意義

このコードはChron-LLMにおける**最初の完全な因果カーネル試作**と言える実装です。

後続のΔ3アーキテクチャで導入された

- Kernel Boundary
- World Service
- Projection Service
- DTO
- Runtime分離

などは、本実装で検証された設計を整理・一般化したものです。

その意味で、本コードはChron-LLM全体の設計思想を形にしたリファレンス・プロトタイプとして位置付けられます。