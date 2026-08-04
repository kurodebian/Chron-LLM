# Chron-LLM Δ3 Kernel 仕様書

**Document Version** : Δ3 Phase1  
**Module** : Kernel  
**Layer** : Runtime / Kernel Boundary

# 1. 概要

Chron Kernel は Runtime と Chron-LLM内部システムを分離する境界(Boundary Layer)である。

KernelはRuntimeから入力を受け取り、

- Event生成
- WAL Commit
- Graph Projection更新
- Immune判定
- Runtime向けContext生成

までを一貫して管理する。

RuntimeはGraph・History・WALを直接操作しない。

Kernelのみがシステム状態を変更できる。

# 2. アーキテクチャ

```
                Runtime
                    │
                    │ DTO
                    ▼
             Chron Kernel
                    │
     ┌──────────────┼──────────────┐
     ▼              ▼              ▼
    WAL         Graph          Immune
     │              │              │
     └──────────────┴──────────────┘
                    │
                Kernel State
```

# 3. 設計思想

Kernelは

**唯一の状態変更責任者
(Single State Mutation Authority)**

である。

RuntimeはKernel APIのみ利用する。

```
Runtime

×

直接WAL操作

×

Graph操作

×

History操作

○

Kernel API
```

# 4. Kernel責務

Kernelが担当する機能

- Event受付
- Commit Pipeline
- Projection更新
- History取得
- Health判定
- Runtime DTO生成
- World管理
- Context構築

# 5. 非責務

Kernelは以下を担当しない。

- LLM推論
- Prompt組立
- Token管理
- Sampling
- Validation
- Memory Search
- Graph生成ロジック
- WAL実装
- Historyアルゴリズム

# 6. DTO

KernelはRuntimeへDTOのみ公開する。

Runtimeは内部Node/Eventを知らない。

# 7. history-entry

## 目的

Runtime用History表現

### フィールド

|名称|型|内容|
|----|---|----|
|kind|Symbol|イベント種別|
|text|String|表示テキスト|
|clock|Integer|Commit Clock|

### 特徴

Nodeは公開しない。

RuntimeはEvent構造を知らない。

# 8. context-object

LLM非依存コンテキスト

### system-prompt

将来Prompt Builder用

現在未使用

### history

DTO化されたHistory

```
List<HistoryEntry>
```

### memory-context

Memory Service予約

### metadata

将来拡張用

# 9. kernel-state

Runtimeへ公開される現在状態

### world-id

現在世界線

### health

```
:ok

:degraded
```

### context

Context Object

# 10. Kernel Container

## chron-kernel

Kernel全体を管理するコンテナ

```
Kernel
├── WAL
├── Graph
└── Current World
```

## WAL

唯一の永続化層

## Graph

Projection Cache

再構築可能

## Current World

Runtimeは世界線を知らない。

Kernelのみ保持する。

初期値

```
100
```

## 将来追加

```
Memory

Summary

Scheduler

Listeners
```

# 11. Kernel生成

## make-chron-kernel()

生成内容

```
Kernel
↓
WAL生成
↓
Graph=nil
```

Graphは初回Commit後生成される。

# 12. History DTO Builder

## %history->dto()

目的

Projection Node

↓

Runtime DTO

変換

### 入力

```
Graph History
```

### 出力

```
History Entry List
```

### 抽出項目

```
Kind

Text

Clock
```

Payloadから

```
:text
```

を取得する。

存在しない場合

```
""
```

を返す。

# 13. Context Builder

## kernel-build-context-view()

目的

Runtime向けContext生成

### History取得

```
Graph
↓
graph-history()
↓
DTO変換
```

### Memory

Phase4以降

### Metadata

未実装

# 14. Projection更新

## refresh-projections()

処理

```
WAL
↓
rebuild-graph-from-wal()
↓
Kernel Graph更新
```

Projectionは毎Commit後更新される。

# 15. Health

## kernel-health()

Graph存在

↓

check-immune-status()

↓

Health返却

Graph未生成

↓

:ok

# 16. Commit Pipeline

## %kernel-commit-event()

Kernel唯一のCommit処理

### 入力

```
Kind

Payload
```

### Pipeline

```
Stage Event
↓
Commit
↓
Projection更新
↓
State生成
```

### 詳細

#### Step1

Stage

```
stage-event()
```

#### Step2

Commit

```
commit-staged()
```

#### Step3

Projection更新

```
refresh-projections()
```

#### Step4

Kernel State生成

```
kernel-current-state()
```

#### エラー

Commit失敗時

```
Kernel commit failed.
```

例外送出。

# 17. Public API

## kernel-submit-user-input()

目的

ユーザー入力受付

生成Event

```
:user-message
```

Payload

```
:text
```

## kernel-submit-assistant-reply()

目的

Assistant応答受付

生成Event

```
:assistant-reply
```

Payload

```
:text
```

## kernel-current-state()

現在状態取得

返却

```
Kernel State
```

# 18. World Management

## kernel-create-world()

目的

新しい世界線生成

### 手順

```
現在世界取得
↓
World Counter++
↓
Branch Event Commit
↓
Current World変更
↓
新World返却
```

### Branch Event

```
Kind

:branch
```

Payload

```
Parent World
```

### World切替

Commit後

```
Current World

↓

New World
```

へ更新。

# 19. Runtimeとの境界

Runtimeが利用可能

```
submit-user

submit-assistant

current-state

create-world
```

Runtimeが利用不可

```
stage-event

commit

graph

history

projection

immune

wal
```

# 20. 状態遷移

```
Runtime
↓
Kernel API
↓
Stage
↓
Commit
↓
Projection
↓
Health
↓
DTO
↓
Runtime
```

# 21. DTO変換

内部

```
Node
↓
Event
↓
HistoryEntry
```

Runtime

```
HistoryEntryのみ
```

# 22. 不変条件

Commit成功後

- WALへ保存済
- Graph最新
- Projection最新
- History取得可能
- Health最新
- DTO最新

Runtime

- Node非公開
- Event非公開
- Graph非公開
- WAL非公開

# 23. 計算量

Commit

```
O(1)
```

（WAL）

Projection

```
O(n)
```

n=WALサイズ

History生成

```
O(depth)
```

DTO生成

```
O(history)
```

Health

```
O(depth)
```

# 24. Phase1制約

実装済

- Kernel Boundary
- DTO
- Commit Pipeline
- Projection更新
- History取得
- Health
- World生成

未実装

- Memory
- Prompt Builder
- Scheduler
- Listener
- Summary
- Incremental Projection
- Validation Hook
- Transaction
- Async Commit

# 25. レイヤ構造

```
Runtime
↓
Kernel API
↓
Kernel
↓
Projection
↓
Graph
↓
Write Ahead Log
```

KernelはRuntimeとPersistenceの唯一の境界である。

# 26. 設計原則

KernelはChron-LLM全体の**唯一の状態遷移管理者**である。

RuntimeはDTOのみを扱い、Kernel内部構造には一切アクセスしない。

Kernelは、

- Event生成
- Commit
- Projection更新
- Health判定
- DTO生成

を一つのトランザクションとして実行することで、Runtimeから見た状態の一貫性を保証する。

ProjectionやHistoryはすべてCommit済WALから再構築されるため、Kernel自身はGraphを永続化せず、Projection Cacheとして管理する。

# 27. コードレビュー・仕様との乖離

## 27.1 `kernel-create-world()` の整合性

この関数では

```lisp
(incf (wal-world-counter wal))
```

で `new-world` を採番した後、

```lisp
(%kernel-commit-event
 kernel
 :branch
 (list :parent-world parent-world))
```

を呼び出しています。

しかし `%kernel-commit-event` は **現在の `kernel-current-world` を `causal-id` として使用**するため、Branch Eventは**新しいWorldではなく親Worldに紐付いてコミット**されます。

### 改善案

- Branch Event生成時に `new-world` を明示的に指定できるAPIへ変更する。
- もしくは `kernel-current-world` を切り替えてからCommitする。

## 27.2 Projection更新コスト

現在は

```
Commit毎
↓
WAL全件
↓
Graph再構築
```

となっています。

これは

```
O(n)
```

であり、イベント数増加に比例してコストが増大します。

Phase2以降では

- Incremental Projection
- Dirty Projection
- Append Projection

などの導入を想定した方がスケーラビリティが向上します。

## 27.3 `context-object.system-prompt`

DTOには `system-prompt` フィールドがありますが、本コード内では一度も設定されていません。

現状では予約フィールドであり、Prompt Builder導入時にKernelから生成される設計であることを仕様へ明記しておくことが望まれます。

## 27.4 Commit Pipeline

現状のCommit Pipelineは

```
Stage
↓
Commit
↓
Projection
↓
DTO
```

という同期処理です。

この構成は単純で決定論的ですが、将来的に

- Validation
- Listener
- Event Notification
- Summary更新
- Memory更新

などを追加する場合は、

```
Stage
↓
Validation
↓
Commit
↓
Projection
↓
Post Commit Hooks
↓
DTO
```

という拡張ポイントを設ける設計が自然です。