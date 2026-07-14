# Chron-LLM Runtime Architecture Specification
# R0/R1 Unified Execution & Observation Contract v1.0

**Status:** Frozen Baseline  
**Version:** v1.0  
**Architecture:** Chron-LLM R1  
**Scope:** Runtime Execution / Observation Boundary

---

# 0. Architecture Overview

Chron-LLM は以下の3層で構成される。

                User
                 |
                 v

    +-------------------------+
    | R0 Session Execution    |
    | Execution Contract     |
    +-------------------------+

                 |
                 v

    +-------------------------+
    | R1 IR Observation       |
    | Observation Contract   |
    +-------------------------+

                 |
                 v

    +-------------------------+
    | Causal Kernel           |
    | Phase D/E/F/G           |
    +-------------------------+

                 |
                 v

    llama.cpp Backend

---

# 1. Core Architecture Principle

Chron-LLM は、

> LLM の非決定的生成過程を、Kernelによる観測可能な状態遷移として扱う Runtime Architecture

である。

責務：

| Layer | Role |
|-|-|
| R0 | Conversation Execution |
| R1 | Generation Observation |
| Kernel | Causal Computation |

LLM は：


Decision Maker
ではなく

Generation Engine


として扱われる。

---

# 2. R0 Session Execution Layer

## Purpose

R0 は対話実行の基底Runtimeである。

責務：

- Session管理
- History管理
- Prompt生成
- llama.cpp呼び出し
- Execution Trace生成

非責務：

- Token観測
- 因果判断
- rollback
- KV操作

---

# 3. R0 Architecture


User Input

|
v

start-chat

|
v

chat()

|
+-------------+
|             |
v             v

History Prompt
Layer Projection

|
v

llama-run

|
v

Trace Layer


---

# 4. R0 Data Model


## Session

```lisp
(defstruct session
  model
  history)
History Event
(defstruct history-event
  role
  content)
History
(defstruct history
  (events
    (make-array 0
                :adjustable t
                :fill-pointer 0)))

保証：

ordered
append-oriented
snapshot可能
conversation state表現
5. R0 Trace Contract
(defstruct r0-trace
  user-text
  prompt
  raw
  parsed
  history-before
  history-after
  prompt-length
  response-length)

Trace目的：

Debug
Execution comparison
Reconstruction

注意：

R0 Trace は

「完全決定論Replay」

ではなく、

「実行状態再構成」

を提供する。

6. R1 IR Observation Layer
Purpose

LLM生成過程をtoken単位で観測する。

R1は：

非侵襲
非権威
append-only

の観測契約である。

7. Physical Event

Backendから発生する生イベント。

(defstruct physical-event
  causal-id
  token-id
  kv-pos
  entropy
  timestamp)

責務：

llama.cpp

↓

Physical Event Stream

8. IR Stream Contract

Physical EventをKernel内部形式へ正規化する。

Physical Event

      |
      v

Normalize

      |
      v

IR Stream

IRはChron-LLM内部時間軸の唯一の入力。

9. IR Data Model
(defstruct ir
  ctx-id
  pos
  phase
  token
  score)

保証：

immutable
ordered
semantic-free
non-authoritative
10. IR Observation Pipeline
llama.cpp

   |
   v

physical-event

   |
   v

ir-callback

   |
   v

ir-stream

   |
   +-------------+
   |             |
   v             v

Replay       Analysis

             |
             v

        Divergence
        Sensors
11. IR Analysis
extract-actions

生成phaseのみ抽出。

divergence-profile

複数試行比較。

出力：

Field	Meaning
step	token位置
all-same	完全一致
p-same	一致確率
12. Kernel Connection

R0/R1 はKernelへ直接介入しない。

入力：

R0 Trace

+

IR Stream

↓

Kernel

Kernelが担当：

Causal Graph
Worldline
Rollback
Policy Decision
13. RuntimeCommand Boundary

KernelからBackendへの唯一の制御境界。

(defstruct runtime-command
  op
  interventions
  truncate-at
  delta-prefill
  payload
  metadata)

Operation:

op	meaning
:commit	state commit
:retry	regenerate
:rollback	restore
14. Frozen Boundary
Frozen
R0
session structure
history-event
trace contract
R1
physical-event flow
IR format
observation boundary
Kernel
RuntimeCommand ABI
Phase boundary
15. Flexible

変更可能：

prompt template
backend implementation
sensor algorithm
Ω calculation
visualization
16. Final Architecture Position
Chron-LLM

+-----------------------------+
| R0 Session Execution        |
| Conversation Runtime        |
+-----------------------------+

             |

+-----------------------------+
| R1 IR Observation           |
| Generation Measurement      |
+-----------------------------+

             |

+-----------------------------+
| Causal Kernel               |
| Deterministic Control       |
+-----------------------------+

             |

+-----------------------------+
| llama.cpp Backend           |
| Physical Execution          |
+-----------------------------+
Final Statement

Chron-LLM Runtime Architecture
R0/R1 Unified Execution & Observation Contract v1.0

は、Chron-LLMにおける

実行
観測
因果制御

の境界を正式定義する基盤仕様である。

R0 は「何を実行したか」を記録する。

R1 は「どのように生成されたか」を観測する。

Kernel は「次に何を許可するか」を決定する。

この三層分離により、LLMの非決定性を保持したまま、決定的な因果制御システムとして拡張可能になる。