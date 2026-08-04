```markdown
# Chron-LLM R1 Architecture Specification
## Unified Stable Interface v1.2 (Final)

**Status:** Stable / Implementation Ready  
**Scope:** Chron-LLM R1 Architecture Baseline  
**Purpose:** LLM生成過程をKernel制御下の決定的状態遷移として扱うRuntime Architectureの定義

---

# 0. Architecture Principle

Chron-LLM R1 は、

> **LLM の非決定的生成過程を、Kernel による決定的制御下の状態遷移として扱う Runtime Architecture**

である。

LLM は意思決定主体ではなく、

```

Generation Engine

```

として扱う。

制御主体は Kernel であり、Kernel は以下を担当する。

```

Observe
↓
Evaluate
↓
Decide
↓
Intervene

````

Chron-LLM の目的は、LLMの自由な生成能力を維持しながら、その生成過程を観測可能・再現可能・制御可能な計算状態へ変換することである。

---

# 1. System Overview

## Closed-loop Control Architecture

```text
llama.cpp Backend
      │
      │ Physical Event (Heartbeat)
      ▼
Physical Event Stream
      │
      │ normalize
      ▼
IR Stream
      │
      │ Chron-LLM内部時間軸の唯一の入力源
      │
      ├────────────── History / WAL / Replay
      │
      ├────────────── Causal Graph (Phase D/E)
      │
      └────────────── Observation (Phase G)
                         │
                         ▼
              Evaluation Layer
              (Ω / divergence / stagnation)
                         │
                         ▼
              PolicyRouter / Dispatcher
                         │
                         ▼
              RuntimeCommand ABI
              (唯一の制御境界)
                         │
                         ▼
              Backend Control
              (KV / Steering / Prefill)
                         │
                         ▼
                         LLM
````

---

# 2. Event Flow Contract

Chron-LLM の内部状態は以下のイベント流によって構成される。

```
Physical Event
      |
      v
IR Stream
      |
      v
Kernel State
```

---

# 2.1 Physical Event

## Backend → Kernel Input

Physical Event は Backend が発生させる生イベントである。

```lisp
(defstruct physical-event
  causal-id
  token-id
  kv-pos
  entropy
  timestamp)
```

## Responsibility

Physical Event は：

* llama.cpp が生成する
* 実際に発生した物理状態を記録する
* Kernel が直接判断には使用しない
* IR Stream 正規化の入力となる

形式：

```
Physical Reality
        |
        v
Physical Event
```

---

# 2.2 Physical Event Stream

Physical Event の連続列。

責務：

* Backend生成イベントの搬送
* 順序保持
* Kernel入力前の一次ストリーム

---

# 2.3 IR Stream

## Kernel Internal Timeline

IR Stream は Physical Event を Kernel が扱える形式へ正規化した内部イベント列である。

Chron-LLM において：

> **IR Stream は内部時間軸の唯一の入力源である**

---

## IR Streamから再構成されるもの

すべてのKernel状態は IR Stream を基準に構築される。

対象：

* History
* WAL
* Replay
* Causal Graph
* Timeline
* Worldline
* Observation
* Evaluation
* Debug World

構造：

```text
IR Stream

   |
   +---- History
   |
   +---- WAL
   |
   +---- Replay
   |
   +---- Causal Graph
   |
   +---- Observation
```

---

# 3. Implementation Roadmap

## M1 — Physical Backend

目的：

物理イベント取得経路を確立する。

実装項目：

* Heartbeat callback
* Physical Event生成
* Physical Event Stream
* IR Stream normalization
* KV truncate API
* delta-prefill API
* kv_pos同期

初期成功条件：

```
llama.cpp
    |
    v
physical-event
    |
    v
IR Stream
    |
    v
Kernel表示

[HB]
```

---

# M2 — Causal Graph (Phase D/E)

目的：

生成過程を因果構造として保持する。

主要概念：

## EventNode

生成イベント単位。

保持情報：

* causal-id
* token range
* start-kv-index
* end-kv-index
* parent relation

---

## Timeline

単一の履歴。

```
A → B → C → D
```

---

## Worldline

分岐した履歴。

```
       B
      /
A ───
      \
       C
```

---

## Rollback Point

物理状態復帰位置。

対応：

```
Rollback Point
      |
      v
KV Position
```

---

# M3 — Observation / Evaluation (Phase G)

目的：

生成状態を評価する。

Phase G は：

* 観測
* 評価
* 判定入力生成

のみを担当する。

行動決定は行わない。

---

# Sensors

## Generative Sensor

評価対象：

* entropy
* confidence
* repetition
* generation stability

---

## Semantic Sensor

評価対象：

* goal divergence
* embedding distance
* semantic drift

---

## Structural Sensor

評価対象：

* loop detection
* stagnation
* structural deviation

---

# Composite Score

状態評価値：

[
\Omega =
w_eE^2+
w_sS^2+
w_tT^2
]

用途：

```
Ω

 ↓

PolicyRouterへの判断入力
```

---

# M4 — Dispatcher / Thinking OS

目的：

計算資源と実行方針を制御する。

処理：

```text
plan-step

 ↓

RouterConfig

 ↓

Generator

 ↓

Critic

 ↓

Observation

 ↓

PolicyRouter

 ↓

RuntimeCommand

 ↓

Backend
```

---

# M5 — Debug World

目的：

Chron-LLM内部状態を可視化する。

機能：

* Causal Graph viewer
* Timeline表示
* Worldline比較
* KV位置表示
* Replay
* rollback可視化
* 手動介入

---

# 4. Phase Definitions

| Phase        | Responsibility | Components                               |
| ------------ | -------------- | ---------------------------------------- |
| Phase D/E    | 因果構造管理・物理同期    | EventNode / Causal Graph                 |
| Phase G      | 観測・評価          | Sensors / Ω                              |
| Runtime Loop | 判断・制御          | RouterConfig / Dispatcher / PolicyRouter |
| Backend      | 物理操作           | KV / Steering / Prefill                  |

---

# 5. RouterConfig

思考予算を管理する。

```lisp
(defstruct router-config
  generator-roles
  critic-role
  max-generators
  max-latency-ms
  risk-threshold)
```

---

## Control Axis

| Axis        | Meaning    |
| ----------- | ---------- |
| Diversity   | 思考候補の多様性   |
| Parallelism | 世界線数       |
| Budget      | 計算量・時間制限   |
| Risk        | rollback閾値 |

---

# 6. RuntimeCommand

## ABI Frozen / Control Boundary

RuntimeCommand は、

> 論理Kernel世界と物理Backend世界を接続する唯一の制御境界

である。

---

```lisp
(defstruct runtime-command
  (op :commit :type keyword)
  (interventions nil :type list)
  (truncate-at nil :type (or fixnum null))
  (delta-prefill nil :type (or string null))
  (payload nil)
  (metadata nil))
```

---

# metadata Policy

R1では：

```
metadata = opaque field
```

として扱う。

意味：

* Kernelは内部解釈しない
* Backendも依存しない
* 将来拡張用予約領域

利用予定：

```
world-id
causal-id
reason
```

---

# Operation

| Operation | Meaning |
| --------- | ------- |
| :commit   | 状態確定    |
| :retry    | 再生成     |
| :rollback | 過去状態復帰  |

---

# Intervention

例：

```
:grammar-mask
:temperature-down
:semantic-bias
```

---

# 7. Backend Control Layer

Backend責務：

物理状態変更。

---

## Heartbeat

生成時イベント：

```
causal-id
token-id
kv-pos
entropy
timestamp
```

---

## KV Control

```text
truncate-at N

↓

KV pointer rollback

↓

delta-prefill

↓

continue generation
```

---

## Steering

対象：

* Temperature
* Grammar Mask
* Semantic Bias

---

# 8. Frozen Boundary Definition

## Frozen

R1互換境界として固定する。

対象：

* RuntimeCommand ABI
* metadata field存在
* Physical Event → IR Stream flow
* IR Stream format
* Phase boundary
* Worldline terminology
* Backend command protocol

---

# Flexible

R1期間中変更可能。

対象：

* Sensor implementation
* Ω weights
* Router policy
* Generator strategy
* Backend内部実装
* Debug World UI

---

# 9. Final Architecture Model

Chron-LLM R1 は以下の閉ループ制御系として定義される。

```text
Generate

 ↓

Observe

 ↓

Evaluate

 ↓

Decide

 ↓

Intervene

 ↓

Generate again
```

---

# 10. R1 Completion Status

```
R0 Kernel Foundation        COMPLETE

R1 Architecture Design      COMPLETE

R1 Stable Interface         COMPLETE


M1 Physical Backend         NEXT
M2 Causal Graph
M3 Observation
M4 Dispatcher
M5 Debug World
```

---

# Final Statement

Chron-LLM R1 Architecture Specification
**Unified Stable Interface v1.2**

は、以下を満たす正式基準仕様である。

* LLM Backend と Kernel の責務分離
* Physical Event と IR Stream の時間モデル確立
* RuntimeCommand による制御境界固定
* Causal Graph による世界線管理
* Observation と Decision の分離
* 将来Backend交換可能な抽象境界

本仕様を基準として、Chron-LLM R1 は設計フェーズから実装フェーズへ移行する。
