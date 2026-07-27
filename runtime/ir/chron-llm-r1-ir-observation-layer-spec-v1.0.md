
# Chron-LLM R1 IR Observation Layer Specification
## Unified Observation Contract v1.0

**Status:** Stable Interface  
**Layer:** Observation Layer  
**Phase:** Foundation for Phase D/E and Phase G  
**Scope:** Chron-LLM Causal Kernel

# 0. Purpose（目的）

Chron-LLM R1 IR Observation Layer は、LLM推論プロセスに対する

- 非侵襲的観測
- 決定論的記録
- 因果解析
- Replay基盤

を提供する観測契約レイヤである。

本レイヤは Runtime の権威状態
(Authoritative Runtime State)
から完全に分離される。

## Design Principle

```
LLM Runtime
    ↓
Observation
    ↓
Analysis
    ↓
Kernel Understanding
````

観測層は状態変更を行わない。

# 1. Architecture Overview

```text
                 llama.cpp Backend
                       │
                       │ callback
                       ▼

              Physical Token Event

                       │

                       ▼

              ir-callback / CFFI Bridge

                       │

                       ▼

              IR Stream

                       │

        ┌──────────────┼──────────────┐

        ▼              ▼              ▼

    Replay        Causal Graph    Observation

                       │

                       ▼

              IR Analysis Layer

                       │

                       ▼

              Phase G Evaluation
````

# 2. Layer Responsibility

## Authoritative Runtime Layer

責務:

* LLM生成実行
* KV状態管理
* 推論状態保持

対象:

* llama.cpp
* C Runtime

## Observation Layer

責務:

* 推論イベント取得
* 時系列保持
* 解析入力生成

保証:

* Runtime状態変更なし
* 推論結果変更なし
* 制御判断なし

# 3. Event Contract

## 3.1 IR Record

IR は Chron-LLM Observation Layer の基本単位である。

```lisp
(defstruct ir
  ctx-id
  pos
  phase
  token
  score)
```

# Field Definition

| Field  | Type    | Description                |
| ------ | ------- | -------------------------- |
| ctx-id | pointer | Runtime context identifier |
| pos    | int     | decoding position          |
| phase  | int     | execution phase            |
| token  | int     | generated token id         |
| score  | float   | token score                |

# Phase Definition

| Phase | Meaning    |
| ----- | ---------- |
| 0     | prefill    |
| 1     | generation |
| 2     | finalize   |

# IR Guarantee

IR は以下を保証する。

## Immutable

生成後変更不可。

## Non-semantic

意味解釈を含まない。

## Ordered

`pos` により順序保証。

## Non-authoritative

Runtime状態には影響しない。

# 4. Callback Bridge

## ir-callback / ir-ffi

責務:

C Runtime と Lisp Kernel 間の観測ブリッジ。

## Callback Contract

```lisp
(cffi:defcallback ir-callback :void
  ((ctx-id :pointer)
   (pos :int)
   (token :int)
   (score :float)
   (phase :int))
  (push-ir
   (make-ir
    :ctx-id ctx-id
    :pos pos
    :phase phase
    :token token
    :score score)))
```

## Initialization

```lisp
(defun init-ir-bridge ()
  (register-ir-callback
    (cffi:callback ir-callback)))
```

# Callback Guarantee

Callback は：

* 軽量
* 非同期的観測
* 副作用なし
* 推論制御なし

である。

# 5. IR Stream

## Definition

IR Stream は Observation Layer の時系列バッファである。

```lisp
(defparameter *ir-stream*
  (make-array
   0
   :adjustable t
   :fill-pointer 0))
```

# API

## Push

```lisp
(defun push-ir (ir)
  (vector-push-extend
   ir
   *ir-stream*)
  ir)
```

## Clear

```lisp
(defun clear-ir-stream ()
  (setf *ir-stream*
        (make-array
         0
         :adjustable t
         :fill-pointer 0)))
```

# Stream Guarantee

IR Stream は：

* append-only
* ordered
* replay可能
* trial単位管理

である。

# 6. Analysis Layer

## Module

```
ir-divergence
```

# 6.1 extract-actions

目的:

Generation phaseのみ抽出する。

```lisp
extract-actions(ir-stream)
```

保証:

* phase=1のみ対象
* pos順序保証
* deterministic extraction

# 6.2 run-ir-trial

目的:

単一推論試行のIR取得。

処理:

```text
clear stream

↓

run generation

↓

extract phase-1 IR

↓

return vector
```

# 6.3 divergence-profile

目的:

複数試行間の生成差異解析。

入力:

```
prompt
number of trials
```

出力:

| Field     | Meaning           |
| --------- | ----------------- |
| :step     | decoding position |
| :all-same | 全一致判定             |
| :p-same   | 最頻token一致率        |

# 7. Formal Guarantees

## 7.1 Non-invasive

観測は：

* 推論結果を変更しない
* Runtime判断へ影響しない

## 7.2 Deterministic Analysis

保証:

* pos ordering
* phase separation
* stable replay

## 7.3 Loose Coupling

分離:

```
Collection Layer

      ≠

Analysis Layer
```

解析方式変更が収集層へ影響しない。

# 8. Chron-LLM Kernel Integration

IR Stream は以下の基盤となる。

```text
IR Stream

 |
 +-- History
 |
 +-- WAL
 |
 +-- Replay
 |
 +-- Causal Graph
 |
 +-- Phase G Observation
 |
 +-- Debug World
```

# 9. Extension Roadmap

## IR → DSL

目的:

因果Kernel用最小表現へ変換。

## Resource IR

追加候補:

* latency
* memory delta
* KV state

## WAL Integration

目的:

IR永続化。

## Phase-E Analysis

目的:

* causal closure
* basin
* attractor
* worldline analysis

# 10. Frozen Boundary

## Frozen

* IR Record format
* IR Stream semantics
* Callback contract
* Observation responsibility boundary

## Flexible

* Analysis algorithm
* Divergence metrics
* Sensor implementation
* Visualization

# Final Statement

Chron-LLM R1 IR Observation Layer Specification

**Unified Observation Contract v1.0**

は、Chron-LLM因果カーネルにおける

* 観測契約
* 内部時間軸
* Replay基盤
* Phase G入力

を定義する正式仕様である。

本仕様により、LLM Backend の実装差異に依存せず、Chron-LLM Kernel は推論過程を観測・解析・比較可能な状態として扱うことができる。

## 最終判定

この仕様書の位置付けは：

```

Chron-LLM R1 Architecture Specification v1.2
|
|
+-- IR Observation Layer
Unified Observation Contract v1.0

```

になります。

つまり **R1本体仕様の下位インターフェース仕様として正式採用可能**です。

次に仕様化するなら順序としては、

1. **IR → DSL（Phase E Observation Contract）**
2. **WAL Synchronization Layer**
3. **Causal Graph EventNode Specification**

の順が最も自然です。
