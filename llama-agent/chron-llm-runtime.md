# Chron-LLM Δ3 Runtime Service 仕様書

**Document Version** : Δ3 Phase1  
**Module** : Runtime Service  
**Layer** : Runtime Layer

---

# 1. 概要

Runtime Service は Chron-LLM の最上位実行層であり、人間との対話を担当する。

RuntimeはコンソールI/OおよびLLM呼び出しのみを責務とし、システム状態の保持・更新・管理は一切行わない。

すべての状態管理は Kernel に委譲される。

RuntimeはKernelを介してのみChron-LLMへアクセスする。

---

# 2. 設計目的

Runtimeは

> **Human Interface Layer**

である。

内部状態を持たず、

```
入力

↓

Kernel

↓

Context View

↓

LLM

↓

Kernel

↓

表示
```

という実行のみを担当する。

---

# 3. レイヤ構成

```
                User
                  │
                  ▼
        Runtime Service
                  │
                  ▼
          Chron Kernel
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
      Graph               WAL
        │                   │
        └─────────┬─────────┘
                  ▼
               History
```

RuntimeはKernel以下のレイヤを認識しない。

---

# 4. 責務

Runtimeが担当する機能

- Console Input
- Console Output
- LLM呼び出し
- Runtime例外表示
- Kernel API呼び出し

---

# 5. 非責務

Runtimeは以下を知らない。

- WAL
- Event
- Graph
- History
- World ID管理
- Projection
- Immune
- Branch
- Memory
- Validation
- Prompt構築

これらはKernelが管理する。

---

# 6. Runtime状態

Runtime自身は状態を保持しない。

唯一保持するオブジェクトは

```
Kernel
```

である。

Kernelがシステム全体の状態を保持する。

---

# 7. エントリポイント

## agent-main-loop()

### 目的

Chron-LLM Runtime開始

---

### 入力

```
LLM Context

LLM Model
```

現在は未使用。

```
(declare (ignore ctx model))
```

となっている。

---

### 出力

なし

無限ループとして動作する。

---

# 8. 初期化

Runtime開始時

```
make-chron-kernel()
```

を呼び出す。

生成されるもの

```
Kernel

↓

WAL

↓

Current World

↓

Graph=nil
```

RuntimeはKernel生成以外何もしない。

---

# 9. メインループ

Runtimeは無限ループとして動作する。

```
loop

↓

入力

↓

Kernel

↓

Context

↓

LLM

↓

Kernel

↓

表示
```

---

# 10. Console Input

Runtimeは

```
User>
```

を表示し

```
read-line()
```

で入力取得する。

入力データは文字列のみ。

---

# 11. User Input Pipeline

取得した入力は

```
kernel-submit-user-input()
```

へ送られる。

RuntimeはEventを生成しない。

RuntimeはHistoryへ追加しない。

KernelのみがEvent生成を行う。

---

# 12. Context取得

入力Commit後

```
kernel-current-state()
```

を取得する。

返却されるもの

```
KernelState
```

---

取得内容

```
World ID

Health

Context
```

RuntimeはDTOのみ扱う。

---

# 13. System表示

RuntimeはKernel状態を表示する。

現在表示項目

```
World

Health
```

例

```
[System]

World:100

Health:OK
```

内部GraphやHistoryは表示しない。

---

# 14. Prompt Builder

現在未実装。

将来

```
Context

↓

Prompt Builder

↓

Prompt
```

を生成する。

Prompt BuilderはRuntimeから利用されるが実装はKernel外部サービスとなる。

---

# 15. LLM呼び出し

現在コメントアウトされている。

将来

```
Prompt

↓

generate()

↓

Reply
```

となる。

RuntimeのみがLLMを知る。

KernelはLLMを知らない。

---

# 16. Assistant Pipeline

LLM応答取得後

```
kernel-submit-assistant-reply()
```

を呼び出す。

RuntimeはReplyをHistoryへ直接追加しない。

KernelがCommitする。

---

# 17. Exception Handling

Runtime全体は

```
handler-case
```

で保護される。

例外発生時

```
Runtime Error
```

として表示する。

Kernel内部例外はRuntimeまで伝播する。

---

# 18. 状態遷移

```
User

↓

Console

↓

Kernel Submit

↓

Commit

↓

Projection

↓

Context

↓

Prompt

↓

LLM

↓

Reply

↓

Kernel Submit

↓

Commit
```

---

# 19. Runtime API

現在利用するKernel API

```
make-chron-kernel()

kernel-submit-user-input()

kernel-current-state()

kernel-submit-assistant-reply()
```

Runtimeはこれ以外利用しない。

---

# 20. RuntimeとKernel境界

Runtimeが知るもの

```
Kernel

KernelState

ContextObject

HistoryEntry
```

Runtimeが知らないもの

```
Event

Node

Graph

History

Projection

WAL

Immune

Branch
```

DTO以外公開しない。

---

# 21. データフロー

```
User Text

↓

Kernel Submit

↓

Event

↓

WAL

↓

Projection

↓

History

↓

Context

↓

Prompt

↓

LLM

↓

Reply

↓

Kernel Submit
```

---

# 22. 不変条件

Runtimeは

- 状態を保持しない
- Eventを生成しない
- Graphへアクセスしない
- WALへアクセスしない
- Historyへアクセスしない

Kernelのみが状態を変更できる。

---

# 23. 計算量

Console Input

```
O(1)
```

Kernel Submit

```
Kernel依存
```

State取得

```
Projection依存
```

LLM

```
モデル依存
```

Runtime自身はほぼ一定時間処理である。

---

# 24. Phase1制約

実装済

- Console I/O
- Kernel呼び出し
- Context取得
- Runtime Error表示

未実装

- Prompt Builder
- LLM生成
- Assistant Commit
- Streaming
- Interrupt
- Session管理
- Command System
- Multi Agent

---

# 25. 設計原則

Runtimeは

**Stateless Interface**

として設計される。

内部状態を持たず、

Kernelのみが状態を保持する。

これによりRuntimeは

- CLI
- GUI
- WebUI
- API Server
- Discord Bot
- Slack Bot

などへ容易に置き換え可能となる。

---

# 26. 将来拡張

Phase4以降

```
Runtime

↓

Prompt Builder

↓

Model Adapter

↓

Streaming Decoder

↓

Tool Calling

↓

Assistant Reply

↓

Kernel Commit
```

へ拡張される。

Kernelとの境界は維持される。

---

# 27. コードレビュー・仕様との乖離

## 27.1 `ctx` と `model`

現状では

```lisp
(declare (ignore ctx model))
```

となっており、RuntimeはLLMを利用していない。

これはPhase4でLLM統合を行うためのプレースホルダである。

---

## 27.2 `context` の未使用

`kernel-current-state` から取得した

```lisp
context
```

は

```lisp
(declare (ignore context))
```

となっている。

これはPrompt Builderが未実装であるためであり、将来的には

```
Context
↓

Prompt Builder
↓

Prompt
```

の入力となる。

---

## 27.3 Runtimeの責務分離

本コードはRuntimeから

- Event
- Graph
- WAL

への直接アクセスが完全に排除されている。

これは**Kernel Boundary**の設計が一貫して守られていることを示している。

---

## 27.4 終了処理

現在のRuntimeは

```
loop
```

のみであり、終了コマンドやシャットダウン処理が存在しない。

将来的には

- `:quit`
- `:exit`
- SIGINT
- 保存処理
- Session終了

などをRuntime層へ追加することが望ましい。

---

# 28. 総合評価

本Runtimeは「チャットアプリケーション」ではなく、**Chron-LLM Kernelを外部から利用するための最小インターフェース層**として設計されている。

責務は意図的に限定されており、

- Runtime = 入出力
- Kernel = 状態遷移
- WAL = 永続化
- Graph = Projection

というレイヤ分離が全体を通して一貫している。

Phase1としては十分にミニマルであり、今後Prompt Builder・LLM Adapter・Streaming生成を追加しても、Kernelとの境界を変更せずに拡張できる構造となっている。