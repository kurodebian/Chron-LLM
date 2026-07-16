# Chron-LLM R2.0-B 仕様書

## World Runtime Layer Specification

---

# 1. 概要

## 目的

本モジュールは **World Runtime Layer** を定義する。

World は Chron-LLM において

> **Canonical Graph に対する独立した実行ビュー(View)**

であり、

Truth（Graph・Memory）を変更せず、

各世界線ごとに

* Head
* Projection Policy
* Metadata
* Lifecycle

のみを保持する。

Graphそのものは唯一であり、
Worldはその上に存在する軽量なビューである。

---

# 2. 設計責務

## Responsibility

World Runtime は以下のみ担当する。

* World生成
* World Fork
* Head管理
* Metadata管理
* Projection Policy保持
* Lifecycle管理
* Replay生成
* Kernel Commit境界

---

## Non Responsibility

本モジュールは以下を担当しない。

* Graph生成
* Payload保存
* Projectionアルゴリズム
* Prompt生成
* Memory管理
* Registry管理
* Scheduler
* LLM推論

---

# 3. 基本設計思想

ソースコメントより重要な設計思想が明示されている。

> Mutable values below are private cells.

つまり

**Worldは外部から直接変更できない。**

変更可能なのは

* Kernel Commit
* Metadata更新
* Lifecycle更新

のみである。

---

さらに

```text
Graph and memory references are deliberately shared,
never copied.
```

Graph

Memory

は

**絶対にコピーされない。**

---

# 4. World構造

```lisp
(defstruct world ...)
```

## 内部構造

| フィールド             | 意味                |
| ----------------- | ----------------- |
| id                | World識別子          |
| graph-ref         | Canonical Graph参照 |
| memory-ref        | Memory Store参照    |
| root-node         | Root Node         |
| head-cell         | 現在Head            |
| projection-policy | Projection設定      |
| metadata          | 任意メタ情報            |
| lifecycle         | 状態                |

---

## 内部実装

### head-cell

```lisp
(list head-node)
```

として保持される。

つまり

```text
(head)
```

という1要素リストである。

これは

```lisp
(setf (car cell) ...)
```

だけで更新できるようにするため。

---

### metadata

同様に

```lisp
(list metadata)
```

として保持。

Copy-on-write更新専用。

---

### lifecycle

同様。

```lisp
(list :created)
```

---

# 5. 公開アクセサ

## world-id

ID取得。

---

## world-graph-ref

共有Graph取得。

参照そのもの。

コピーしない。

---

## world-memory-ref

共有Memory取得。

コピーしない。

---

## world-root-node

Root取得。

---

## world-head-node

```lisp
(car head-cell)
```

を返す。

---

## world-projection-policy

```lisp
(copy-tree ...)
```

で返す。

つまり

**外部変更禁止**

---

## world-metadata

こちらも

```lisp
copy-tree
```

で返す。

---

## world-lifecycle

現在状態取得。

---

# 6. Graph整合性検証

内部関数

```lisp
%require-graph-node
```

---

## 役割

Graph内にNodeが存在するか確認する。

存在しなければ

```text
Root node must exist...
```

等の例外を送出。

---

# 7. World生成

## make-world

---

### 入力

* id
* graph
* memory
* root-node
* head-node
* projection-policy
* metadata(optional)

---

### 実行手順

① ID検証

空文字は禁止。

```
A world requires
a non-empty stable id.
```

---

② Root存在確認

```
%require-graph-node
```

---

③ Head存在確認

---

④ World生成

内部では

```
%make-world
```

を使用。

---

### コピー規則

| 項目        | コピー |
| --------- | --- |
| Graph     | ×   |
| Memory    | ×   |
| Policy    | ○   |
| Metadata  | ○   |
| Lifecycle | ○   |

---

# 8. World Fork

```
fork-world
```

---

## 目的

親Worldから子World生成。

---

コピーされるもの

```
Projection Policy
Metadata
```

---

共有されるもの

```
Graph
Memory
Root
Head
```

---

親子関係は

**Registry側が保持**

とコメントされている。

---

# 9. Metadata更新

```
replace-world-metadata!
```

---

Copy-on-write。

```
(copy-tree metadata)
```

を保存。

Graphには一切影響しない。

---

# 10. Lifecycle更新

内部関数

```
%set-world-lifecycle!
```

---

状態を書き換えるだけ。

外部公開されない。

---

# 11. Kernel Commit

最重要関数。

```
kernel-commit-world!
```

---

コメント

> The Kernel's visibility boundary

つまり

**KernelがTruthを公開する唯一の境界**

である。

---

## 入力

World

Node

---

## 検証

Node型確認

```
causal-node-p
```

失敗

```
A kernel commit
requires
a causal-node.
```

---

## ID重複確認

Graph内検索

```
get-node
```

存在した場合

```
Committed node ids
are immutable
```

---

## Commit順序

ソースコメント

```
sole R2.0-B
head advancement operation
```

つまり

Head更新はここだけ。

---

実行順序

```
add-node!

↓

head更新
```

Graphへ追加される前に

Headを書き換えることはない。

---

## 戻り値

World自身。

---

# 12. Projection Policy

内部関数

```
%policy-includes-evaluations-p
```

---

Policyから

```
:include-evaluations
```

取得。

真ならReplay対象へ含める。

---

# 13. Replay

```
replay-world
```

---

コメント

```
Pure,
deterministic
execution state
```

つまり

Replayは

**純粋関数**

である。

---

## 手順

① Policy取得

↓

② build-prefill-state呼び出し

↓

③ Prefill Hash取得

↓

④ Replay情報生成

---

内部で

```
build-prefill-state
```

へ渡す情報

```
Graph

Memory

Head

Policy
```

のみ。

---

## 出力

Replay結果

```
:world-id

:head-node

:projection-policy

:metadata

:prefill-hash
```

---

ここで重要なのは

```
Prefillそのもの
```

ではなく

```
Prefill Hash
```

のみ返すこと。

コメントでも

```
canonical replay-visible representation
```

と説明されている。

つまり

Replay結果の正体は

**Content Address**

である。

---

# 14. 不変条件（Invariants）

## I-1

World IDは空不可。

---

## I-2

Graph参照は共有。

---

## I-3

Memory参照は共有。

---

## I-4

Projection Policyはコピー。

---

## I-5

Metadataはコピー。

---

## I-6

Head更新は

```
kernel-commit-world!
```

のみ。

---

## I-7

Node ID再利用禁止。

---

## I-8

Replayは決定論。

---

## I-9

Root Nodeは変更されない。

---

## I-10

HeadはGraph上に存在するNodeのみ。

---

# 15. 状態遷移

```text
make-world
      │
      ▼
 Created
      │
      │ commit
      ▼
 Head Advance
      │
      │ replay
      ▼
 Execution State
```

---

# 16. Kernel Commitシーケンス

```text
Kernel

 │

 ▼

Validate Node

 │

 ▼

Graphへ追加

 │

 ▼

Head更新

 │

 ▼

Replay可能
```

この順序はコード中で明示されており、`add-node!` の成功後にのみ Head が更新されるため、未登録ノードを指す Head は発生しない。

---

# 17. モジュール構成

```text
                World
                   │
      ┌────────────┴────────────┐
      │                         │
      ▼                         ▼
 Shared Graph             Shared Memory
      │                         │
      └────────────┬────────────┘
                   │
            Projection Policy
                   │
                   ▼
             build-prefill-state
                   │
                   ▼
             replay-world
                   │
                   ▼
              Prefill Hash
```

---

# 18. 設計上の特徴

この実装は **「Truth と View の厳密な分離」** を中心原則としている点が特徴である。

* **Graph と Memory は共有・不変**であり、World はそれらへの参照のみを保持する。
* **World は軽量なビュー**であり、Head・Policy・Metadata・Lifecycle といった実行時状態だけを管理する。
* **Head の更新は `kernel-commit-world!` に限定**され、Graph 更新と一体化した唯一の公開境界となる。
* **Replay は `build-prefill-state` の結果をハッシュ化した内容アドレス (`prefill-hash`) を返す**ことで、内部表現に依存しない決定論的な再実行識別子を提供する。

これにより、複数の World が同一の Canonical Graph を共有しながら、それぞれ異なる実行ビューとして独立して扱えるアーキテクチャになっている。
