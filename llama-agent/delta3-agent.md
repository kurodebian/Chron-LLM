# Chron-LLM Δ3 Stateful Reset / Agent Runtime 仕様書

**Document Version** : Δ3 Experimental Prototype  
**Module** : Stateful Reset / Agent Runtime  
**Layer** : Runtime + Agent Memory Layer

---

# 1. 概要

本モジュールは Chron-LLM における

- Stateful Reset
- Agent Identity Recovery
- Long Context Recovery
- KV Cache Reset
- Agent Runtime

の概念実証 (PoC) を目的とした試作実装である。

通常のLLMはKV Cacheを失うと会話状態も失われる。

本実装では

```
KV Reset

↓

Identity Prompt

↓

Agent State

↓

Memory Reconstruction

↓

Continue
```

という手順によって状態を復元する。

---

# 2. 設計目的

本モジュールは

```
LLM

↓

長時間動作

↓

KV満杯

↓

Reset

↓

継続実行
```

を実現することを目的とする。

---

# 3. アーキテクチャ

```
                 Runtime
                     │
                     ▼
              Agent Runtime
                     │
      ┌──────────────┴──────────────┐
      ▼                             ▼
 State Manager                 Reset Manager
      │                             │
      ▼                             ▼
 Agent State                 KV Cache
      │                             │
      └──────────────┬──────────────┘
                     ▼
                 llama.cpp
```

---

# 4. 責務

本モジュールが担当するもの

- Agent状態保持
- Identity Prompt生成
- KV Reset
- Context再投入
- Reset判定
- Agent Loop

---

# 5. 非責務

本モジュールは以下を担当しない。

- WAL
- Graph
- Replay
- History
- Branch
- Prompt Builder
- Memory Search
- Projection

---

# 6. Runtime State

## *n-past*

現在のKV使用長

```
Past Tokens
```

---

## *system-prompt*

Agent Identity

```
あなたは優秀なエンジニアAI、Δ3です。
```

Reset後最初に投入される。

---

# 7. Agent State

## chron-agent-state

Agentの論理状態を保持する。

---

### goal

現在目標

---

### context

現在状況

---

### todo

作業予定

---

### issues

課題一覧

---

# 8. 初期Agent

起動時

```
Goal

リセット機構の初回テスト
```

---

Context

```
テスト環境
```

---

TODO

```
REPL確認
```

---

# 9. Agent Prompt

## format-agent-state-to-prompt()

Agent状態

↓

Prompt

変換

例

```
Goal

TODO
```

のみ出力する。

---

# 10. KV Reset

## my-llama-reset-kv()

現在

Stub実装。

目的

```
KV Cache

↓

Physical Clear
```

---

# 11. Tokenize

## my-llama-tokenize()

現在

Stub

固定

```
101

102

103
```

返却。

---

# 12. Decode

## my-llama-decode()

現在

Stub。

```
Decode

↓

n-past

↓

Console
```

表示。

---

# 13. Stateful Reset

## perform-stateful-reset()

本モジュールの中心機能。

---

### Step1

Reset開始

```
Reset Sequence
```

表示。

---

### Step2

KV物理削除

```
my-llama-reset-kv()
```

---

### Step3

```
*n-past*

=

0
```

---

### Step4

Identity Prompt投入

```
System Prompt

↓

Tokenize

↓

Decode

↓

n-past更新
```

---

### Step5

Agent State投入

```
Goal

TODO

↓

Prompt

↓

Tokenize

↓

Decode
```

---

### Step6

```
n-past更新
```

---

### Step7

Reset終了

```
Memory Rebuild Complete
```

表示。

---

# 14. Reset Pipeline

```
KV Reset

↓

n-past=0

↓

Identity

↓

Agent State

↓

Decode

↓

Continue
```

---

# 15. KV Usage

## get-kv-usage()

現在

Stub

```
0.86
```

固定。

将来

```
llama.cpp

↓

実測
```

予定。

---

# 16. Reset判定

## should-trigger-reset-p()

KV使用率取得

↓

85%以上

↓

Reset要求

---

閾値

```
85%
```

---

# 17. Summary Update

## update-agent-state-from-summary()

目的

```
Response

↓

Summary

↓

Agent更新
```

現在

Stub

TODO追加のみ。

---

更新内容

```
要約に基づく次の行動へ移行
```

をTODO先頭へ追加。

---

# 18. Recovery Log

## print-reset-recovery-log()

表示内容

```
Goal

Next TODO

Ready
```

Agent復旧確認。

---

# 19. Generation

## my-llama-generate()

現在

Stub

入力

↓

返答生成

---

# 20. Agent Runtime

## agent-main-loop()

対話Runtime。

---

起動

```
Δ3

起動
```

表示。

---

# 21. Runtime Command

## :quit

終了。

---

## :reset

強制Reset。

---

その他

通常Generation。

---

# 22. 通常Pipeline

```
User

↓

Generate

↓

Response

↓

KV確認

↓

Reset?

↓

Continue
```

---

# 23. 自動Reset

応答終了

↓

KV確認

↓

85%以上

↓

Summary

↓

Reset

↓

Continue

---

# 24. 状態遷移

```
Generate

↓

KV増加

↓

Threshold

↓

Summary

↓

Reset

↓

Identity

↓

Goal

↓

Continue
```

---

# 25. Agent Memory

保持されるもの

```
Goal

Context

TODO

Issues
```

Reset後

再投入される。

---

# 26. Memory Reconstruction

```
Identity

+

Goal

+

TODO

↓

LLM

↓

同一人格
```

を維持する。

---

# 27. 不変条件

Reset後

```
Identity

保持
```

Goal

保持

TODO

保持

n-past

再計算

---

# 28. 計算量

Reset

```
O(System Prompt

+

Agent State)
```

---

Summary

```
O(summary)
```

---

Runtime

```
O(Response)
```

---

# 29. Phase制約

実装済

- Agent State
- Stateful Reset
- Identity Prompt
- Auto Reset
- Recovery

未実装

- Summary生成
- Memory検索
- WAL保存
- Graph更新
- Replay
- Branch
- DTO
- Kernel統合

---

# 30. 設計思想

本モジュールでは

```
KV Cache

≠

Memory
```

という思想を採用する。

KVは

```
高速作業領域
```

Memoryは

```
Agent状態
```

である。

Resetとは

```
KV破棄

↓

Memory再投入
```

に過ぎない。

---

# 31. 将来構想

Chron-LLMでは

```
Summary

↓

WAL

↓

Graph

↓

History

↓

Memory

↓

Prompt

↓

Reset
```

となる予定。

Agent StateはKernel管理へ移行する。

---

# 32. コードレビュー・設計評価

## 32.1 優れている点

この試作で最も重要なのは、

> **「KVキャッシュを記憶そのものと見なさない」**

という設計思想です。

Agentの継続性を

- Goal
- TODO
- Context

という論理状態で再構築する発想は、後のChron-LLMにおけるKernel・Memory・History分離の原型となっています。

---

## 32.2 グローバル状態

以下はすべてグローバル変数です。

- `*n-past*`
- `*system-prompt*`
- `*current-agent-state*`

単一AgentのPoCとしては問題ありませんが、

- 複数Agent
- 並列Session

へ対応するには `chron-agent-state` や `n-past` をKernelまたはSessionオブジェクトへ保持する構成が望まれます。

---

## 32.3 Summary

`update-agent-state-from-summary()` は現在TODOを追加するだけのStubです。

将来的には

```
Conversation

↓

Summary

↓

Goal更新

↓

TODO更新

↓

Issue更新
```

という永続的なAgent State更新へ発展させる設計が自然です。

---

## 32.4 Reset Trigger

KV使用率85%でResetする設計はシンプルですが、

実運用では

- コンテキスト長
- 要約コスト
- 生成品質低下
- 推論速度

なども考慮した複合判定へ発展させる余地があります。

---

# 33. Chron-LLMとの関係

このコードは現在のChron-LLMから見ると**Stateful Resetの原型実装**です。

後続アーキテクチャでは、

```
Agent State
    ↓
History
    ↓
WAL
    ↓
Graph
    ↓
Kernel DTO
    ↓
Prompt Builder
```

という構成へ発展しており、本コードの「Goalを再投入して継続する」という考え方は、より一般化された**Kernelによる論理状態復元**へと昇華されています。

そのため、この実装は現在のChron-LLMにおける **Memory Service / Prompt Builder / Reset機構** の設計的起源として位置付けることができます。