# Chron-LLM R1 パッケージ仕様書

## `chronos-r1` Package Interface Specification v1.0

**対象モジュール**

`package.lisp`

**パッケージ名**

```lisp
chronos-r1
```

---

# 1. 概要

本モジュールは Chron-LLM R1 Runtime の**公開インターフェース（Public ABI）**を定義する。

このファイル自体には実装は存在せず、

* 名前空間の定義
* 外部公開シンボル
* モジュール境界

のみを規定する。

実装は他ファイルへ委譲される。

---

# 2. パッケージ定義

```lisp
(defpackage :chronos-r1
  (:use :cl)
  ...)
```

## 使用パッケージ

| Package     | 用途      |
| ----------- | ------- |
| Common Lisp | 標準ライブラリ |

他ライブラリへの依存は存在しない。

---

# 3. モジュール構成

公開APIは大きく5層へ分類される。

```text
Domain Model

↓

Pure Operations

↓

Kernel

↓

Runtime

↓

Self Test
```

---

# 4. Domain API

Runtime内で使用される基本データ構造。

---

## Event

Canonicalへ保存される最終イベント。

公開API

```text
event
event-p
make-event
event-id
event-source
event-payload
event-metadata
```

役割

* Canonical Historyの構成単位
* Commit対象
* Immutable

---

## Candidate

未確定イベント。

公開API

```text
candidate
candidate-p
make-candidate

candidate-id
candidate-source
candidate-trigger
candidate-intent
candidate-payload
candidate-constraints
candidate-metadata
```

役割

* Observation結果
* Validation対象
* Commit前状態

---

## Canonical

Runtime唯一の権威状態。

公開API

```text
canonical
canonical-p
make-canonical

canonical-history
canonical-config
canonical-memory-ref
canonical-clock
```

保持内容

* History
* Config
* Memory
* Clock

---

## Kernel State

Kernel内部状態。

公開API

```text
kernel-state
make-kernel-state

kernel-state-canonical
kernel-state-deferred-queue
kernel-state-working
kernel-state-faults
```

役割

Kernel実行状態保持。

---

## Validation Report

Validation結果。

公開API

```text
validation-report
validation-report-p

validation-report-candidate-id

validation-report-syntax-violations

validation-report-semantic-violations

validation-report-invariant-violations

validation-report-observations
```

役割

Validationが収集した事実のみ保持。

---

## Runtime Command

KernelからRuntimeへの制御命令。

公開API

```text
runtime-command
runtime-command-p

runtime-command-kind

runtime-command-data
```

役割

KernelとRuntimeの通信。

---

# 5. Pure Operation API

副作用を持たない関数群。

---

## derive

```text
derive
```

役割

Canonicalから派生情報生成。

---

## replay

```text
replay
```

役割

決定的Replay。

---

## build-prompt

```text
build-prompt
```

役割

Backendへ渡すPrompt生成。

---

## validate

```text
validate
```

役割

Candidate検査。

副作用なし。

---

## policy-router

```text
policy-router
```

役割

Validation結果からKernel Action決定。

---

## recover

```text
recover
```

役割

Backend再構築情報生成。

---

# 6. Authoritative Boundary API

唯一状態変更を許可するAPI群。

---

## commit

```text
commit
```

役割

Canonical更新。

Chron-LLMにおける唯一の権威更新境界。

---

## kernel-transition

```text
kernel-transition
```

役割

Kernel状態遷移。

Action実行。

---

## wake-deferred

```text
wake-deferred
```

役割

Deferred Queue再評価。

---

## branch-worldline

```text
branch-worldline
```

役割

新しい世界線生成。

Branch Candidate作成。

---

# 7. Runtime Facade

Runtime利用者向け公開API。

---

## Runtime生成

```text
make-runtime

runtime-p
```

---

## Runtime状態取得

```text
runtime-state

runtime-next-candidate-id

runtime-last-command
```

---

## Runtime操作

```text
runtime-submit

runtime-run-candidate

runtime-run-backend
```

役割

Backendとの統合。

---

# 8. Self Test

公開API

```text
chronos-r1-self-test
```

役割

Runtime全体のリファレンス検証。

設計上、

* Commit
* Validation
* Kernel
* Runtime

が正常に動作することを確認するための自己診断エントリポイントである。

---

# 9. API分類一覧

| カテゴリ            | 公開API                                                                         |
| --------------- | ----------------------------------------------------------------------------- |
| Domain          | event, candidate, canonical, kernel-state, validation-report, runtime-command |
| Pure Functions  | derive, replay, build-prompt, validate, policy-router, recover                |
| Kernel Boundary | commit, kernel-transition, wake-deferred, branch-worldline                    |
| Runtime         | make-runtime, runtime-submit, runtime-run-candidate, runtime-run-backend      |
| Inspection      | runtime-state, runtime-next-candidate-id, runtime-last-command                |
| Testing         | chronos-r1-self-test                                                          |

---

# 10. 依存関係

```text
Common Lisp
        │
        ▼
Package Interface
        │
        ▼
Domain Types
        │
        ▼
Pure Operations
        │
        ▼
Kernel
        │
        ▼
Runtime
```

パッケージ定義自身は他モジュールへ依存しない。

---

# 11. 公開境界（Public ABI）

本パッケージは Chron-LLM R1 Runtime の**唯一の外部公開インターフェース**として機能する。

### 外部から利用可能

* Domainオブジェクトの生成・参照
* Validation実行
* Prompt生成
* Runtime実行
* Kernel操作
* Worldline分岐
* Self Test

### 外部から直接利用できないもの

以下はエクスポートされておらず、内部実装として隠蔽される。

* 補助ユーティリティ関数
* Validation内部アルゴリズム
* Candidate→Event変換処理
* Fault生成処理
* Observation検出器
* Prompt生成内部補助関数
* Kernel内部状態更新の詳細実装

---

# 12. 設計上の特徴

* **単一の名前空間**：`chronos-r1` により Runtime 全体の公開APIを一元管理する。
* **明確な責務分離**：Domain、Pure Operations、Kernel、Runtime をカテゴリごとに公開し、層構造を反映している。
* **最小公開原則**：内部補助関数は非公開とし、必要最小限のシンボルのみをエクスポートする。
* **権威境界の明示**：`commit` と `kernel-transition` を公開することで、状態変更の正規経路を明確化している。
* **テスト容易性**：`chronos-r1-self-test` を公開することで、実装全体の整合性確認を外部から実行できる。
* **安定ABI志向**：公開シンボルを固定することで、他モジュールや将来の実装変更から利用者を保護するインターフェースとして機能する。
