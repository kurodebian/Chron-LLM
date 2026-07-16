# Chron-LLM R1 Runtime Core 仕様書

## Runtime Core / Validation / Kernel Transition Specification v1.0

**対象モジュール**
`chronos-r1`

**目的**

本モジュールは Chron-LLM R1 Runtime の中核となる決定的(Runtime Deterministic)実行系を提供する。

設計思想は

> **Observation ≠ Canonical**

を厳密に維持し、

```
Candidate
      ↓
Validation
      ↓
Policy
      ↓
Kernel
      ↓
Canonical
```

という一方向の権威更新を実現する。

---

# 1. アーキテクチャ

```
Backend
      │
      ▼
 Candidate
      │
      ▼
 Validation
      │
      ▼
 Policy Router
      │
      ▼
 Kernel Transition
      │
      ▼
 Canonical
      │
      ▼
 Replay
      │
      ▼
 Prompt
```

KernelのみがCanonicalを書き換えられる。

---

# 2. 設計原則

## Immutable Canonical

Canonicalは永続データ。

Commitでは

```
Canonical(old)

↓

Canonical(new)
```

を生成する。

既存Canonicalは変更されない。

---

## Single Authority

唯一状態変更できる場所

```
commit()
```

および

```
kernel-transition()
```

のみ。

Validation

Policy

Observation

はいずれも副作用を持たない。

---

# 3. 定数定義

## Source

```
:user
:assistant
:tool
:system
```

イベント発生主体。

---

## Intent

```
:append
:reflect
:tool
:memory-read
:memory-write
:recover
:summarize
```

Candidateの目的。

---

## Kernel Action

```
:accept
:reject
:defer
:retry
:retry-penalty
:abort
```

Policy RouterがKernelへ通知する命令。

---

# 4. データ構造

---

## Event

Canonicalに保存される最小イベント。

### フィールド

| 項目       | 内容   |
| -------- | ---- |
| id       | 一意ID |
| source   | 発生主体 |
| payload  | 本文   |
| metadata | 補助情報 |

読み取り専用。

---

## Candidate

Observationから生成される仮イベント。

追加情報

```
trigger
constraints
metadata
```

を保持できる。

Canonicalではない。

---

## Canonical

権威状態。

保持内容

```
history
config
memory-ref
clock
```

---

## ValidationReport

Validation結果。

保持

```
syntax violations

semantic violations

invariant violations

observations
```

---

## RuntimeCommand

KernelがRuntimeへ返す制御命令。

```
kind
data
```

---

## KernelState

Kernel内部状態。

```
canonical

deferred queue

working

faults
```

---

## Runtime

Runtime全体。

```
KernelState

next candidate id

last command
```

---

# 5. Replay

## derive()

Canonicalから派生情報を生成。

生成内容

```
Projection

Graph

Summary
```

Summaryは

```
summary-limit
```

件のみ抽出。

---

## replay()

derive()の別名。

副作用なし。

---

# 6. Prompt Builder

```
build-prompt()
```

入力

```
Derived

Memory

Config
```

生成

```
System

Summary

Memory

Assistant Header
```

Observation

Fault

Metrics

などは一切含まない。

決定的Promptである。

---

# 7. Validation

Validationは

**事実収集のみ**

であり判断しない。

---

## Syntax Validation

検査

Candidate ID

Source

Intent

Payload型

---

## Semantic Validation

検査

Memory参照存在

History参照

---

## Invariant Validation

検査

Candidate重複

Clock整合

---

## Observation Detection

現在実装

```
Echo

Stagnation

Discontinuity
```

検出。

Recommendation

```
Retry

Penalty

Abort
```

を生成する。

---

# 8. Policy Router

Validation結果からKernel Actionを選択。

優先順位

```
Syntax Error

↓

Semantic Error

↓

Fatal Invariant

↓

Recoverable Invariant

↓

Observation

↓

Accept
```

Observation複数時は

```
Abort

>

Retry Penalty

>

Retry
```

が優先。

---

# 9. Commit

唯一のCanonical更新。

検査

```
Event

Source

Payload

Event ID
```

更新内容

```
Clock++

Lamport付与

History追加

Memory更新
```

返値

```
New Canonical

Committed Event
```

---

# 10. Candidate→Event変換

```
candidate->event()
```

付加情報

```
candidate-id

intent
```

をmetadataへ追加。

---

# 11. Kernel Transition

唯一の状態遷移器。

---

## ACCEPT

```
Candidate

↓

Commit

↓

Proceed
```

Working削除。

---

## REJECT

Working削除。

Discard命令返却。

---

## DEFER

Deferred Queueへ保存。

Sleep返却。

---

## RETRY

Regenerate返却。

状態変更なし。

---

## RETRY PENALTY

Generation Policy追加。

```
temperature +0.2

top-p -0.1
```

Regenerate-with-penalty返却。

---

## ABORT

Fault生成。

Terminate返却。

---

# 12. Fault生成

Fault情報

```
id

clock

origin

cause

detector

candidate-id
```

Validation由来であることを保持。

---

# 13. Deferred Queue

```
wake-deferred()
```

Commit成功後のみ再評価。

時間経過では起床しない。

各Candidateを

```
Validate

↓

Policy

↓

Kernel
```

へ再投入。

---

# 14. Recover

```
recover()
```

CanonicalからBackend再構築情報生成。

返却

```
Derived

Memory

Prefill Prompt
```

副作用なし。

---

# 15. Worldline Branch

```
branch-worldline()
```

生成

```
Recover Candidate
```

metadata

```
causal-id
```

付与。

Branch自体も通常Commit経路を通る。

特権処理ではない。

---

# 16. Runtime API

---

## runtime-run-candidate

処理

```
Validate

↓

Policy

↓

Kernel

↓

Wake Deferred
```

返却

```
Runtime

Report

Action

Command
```

---

## runtime-submit

外部入力受付。

Candidate生成後

```
runtime-run-candidate
```

を呼ぶ。

---

## runtime-run-backend

Backend統合。

処理

```
Replay

↓

Prompt Build

↓

Generator

↓

Runtime Submit
```

Generatorは

```
Prompt

↓

Text
```

のみ返す。

Canonicalへは直接アクセスできない。

---

# 17. 状態遷移図

```text
Backend
   │
   ▼
Candidate
   │
   ▼
Validate
   │
   ▼
Policy Router
   │
   ▼
Kernel Transition
   │
   ├──────── Accept ───────► Commit ─────► Canonical
   │
   ├──────── Reject ───────► Discard
   │
   ├──────── Defer ────────► Deferred Queue
   │
   ├──────── Retry ────────► Regenerate
   │
   ├── Retry Penalty ──────► Regenerate (Penalty)
   │
   └──────── Abort ────────► Fault + Terminate
```

---

# 18. 不変条件（Invariant）

* Canonicalは不変オブジェクトとして扱われ、Commit時にのみ新しい値が生成される。
* Validationは状態変更を行わない。
* Policy Routerは評価結果からアクションを選択するのみで、副作用を持たない。
* Kernel TransitionのみがRuntime状態を変更できる。
* CommitのみがCanonicalを更新できる。
* Deferred CandidateはCommit後の再評価時のみ再実行される。
* Prompt生成はCanonical・Memory・Configのみを入力とし、ObservationやFaultを含めない。
* Backendは非権威（Non-authoritative）であり、生成テキストは必ずCandidateとしてValidationを経由する。
* Worldline Branchも通常のCandidate→Validation→Commit経路を通過し、特権的な更新経路を持たない。

---

# 19. Chron-LLM R1 における責務

| レイヤ               | 責務                  |
| ----------------- | ------------------- |
| Backend           | 非決定的テキスト生成          |
| Candidate         | 観測結果の保持             |
| Validation        | 事実収集・整合性検査          |
| Policy Router     | 実行アクション決定           |
| Kernel Transition | 状態遷移の実行             |
| Commit            | Canonical更新         |
| Replay            | Canonicalから実行状態を再構築 |
| Prompt Builder    | 決定的Prompt生成         |
| Recover           | Backend再開用コンテキスト生成  |
| Runtime           | 各コンポーネントの統合制御       |

---

# 20. 総括

本モジュールは、Chron-LLM R1 Runtime の決定的実行基盤として設計されている。非決定的なLLM出力を直接Canonicalへ反映することはなく、必ず **Candidate → Validation → Policy Router → Kernel Transition → Commit** の一方向パイプラインを経由する。これにより、Canonicalの一貫性・再現性・監査可能性を維持しつつ、Backendを交換可能な非権威コンポーネントとして扱うアーキテクチャが実現されている。
