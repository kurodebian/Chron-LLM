# Chron-LLM R0 Runtime

# History Module Specification v1.0

**Status:** Frozen Reference Specification

**Layer:** R0 History Layer

**Package:** `chronos-r0.history`

---

# 1. 概要

本モジュールは **Chron-LLM R0** の会話履歴（History）管理を担当する。

責務は以下に限定される。

* 会話イベントの保持
* 会話履歴の保持
* イベント追加
* 履歴コピー
* 履歴サイズ取得

本モジュールは純粋なデータ管理層であり、LLM・Prompt・Runtime・Kernel には依存しない。

---

# 2. アーキテクチャ上の位置

```text
User / Assistant

        │

        ▼

History Event

        │

        ▼

History

        │

        ▼

Prompt Projection
```

History は R0 Runtime の唯一の対話履歴ストレージである。

---

# 3. 公開 API

## データ構造

```text
history
history-event
```

## コンストラクタ

```text
make-history
make-history-event
```

## アクセサ

```text
history-events
history-event-role
history-event-content
```

## 操作

```text
history-append
history-size
history-copy
```

---

# 4. データモデル

## History Event

### 概要

1回の会話イベントを表す最小単位。

### 構造

| フィールド   | 型  | 説明   |
| ------- | -- | ---- |
| role    | 任意 | 発話主体 |
| content | 任意 | 発話内容 |

### 現在の利用値

role は通常

```text
:user
:assistant
```

が使用される。

将来的には

```text
:system
:tool
```

などへ拡張可能である。

---

## History

### 概要

会話イベント列。

### 構造

```text
History

└── Events(Vector)
```

events は

```lisp
(make-array
 0
 :adjustable t
 :fill-pointer 0)
```

で生成される。

---

# 5. History Storage

History は

**Adjustable Vector**

を採用している。

特徴

* 可変長
* O(1) 末尾追加（平均）
* 添字アクセス高速

---

## 内部構造

```text
History

events

↓

+-----+-----+-----+
| e0  | e1  | e2  |
+-----+-----+-----+
```

---

# 6. make-history

## 目的

空の履歴を生成する。

---

### 初期状態

```text
Events = []
```

---

### 出力

```text
History
```

---

# 7. make-history-event

## 目的

履歴イベント生成。

---

### 入力

| 引数      | 内容   |
| ------- | ---- |
| role    | 発話主体 |
| content | 発話内容 |

---

### 出力

```text
History Event
```

---

# 8. history-copy

## 概要

History の複製を生成する。

---

### 実装

```lisp
(copy-seq
 (history-events h))
```

を利用する。

---

### コピー範囲

コピーされるもの

```text
History

↓

Events Vector
```

コピーされないもの

```text
History Event 本体
```

つまり

**シャローコピー**である。

---

### データフロー

```text
History A

Events

↓

copy-seq

↓

History B
```

Event オブジェクトは共有される。

---

### 用途

主に

* Trace
* Snapshot

取得で利用される。

---

# 9. history-append

## 概要

History の末尾へイベント追加。

---

### 実装

```lisp
(vector-push-extend
 e
 (history-events h))
```

---

### 動作

```text
Before

e0
e1

↓

Append(e2)

↓

e0
e1
e2
```

---

### 戻り値

History 自身

```text
History
```

を返す。

---

# 10. history-size

## 概要

履歴件数取得。

---

### 実装

```lisp
(length
 (history-events h))
```

---

### 戻り値

```text
Integer
```

---

# 11. データフロー

```text
make-history

      │

      ▼

History

      │

      ▼

history-append

      │

      ▼

History

      │

      ├─────────────┐
      ▼             ▼

history-size   history-copy
```

---

# 12. 状態遷移

```text
Empty

↓

Append(User)

↓

Append(Assistant)

↓

Append(User)

↓

Append(Assistant)
```

History は単純な追記型であり、削除・更新操作は存在しない。

---

# 13. 時間計算量

| 操作                 | 計算量     |
| ------------------ | ------- |
| make-history       | O(1)    |
| make-history-event | O(1)    |
| history-append     | 平均 O(1) |
| history-size       | O(1)    |
| history-copy       | O(n)    |

---

# 14. 不変条件（Invariants）

* `History` はイベント列のみを保持する。
* イベントの順序は追加順に保持される。
* `history-append` は常に末尾へ追加する。
* `history-size` はイベント数と一致する。
* `history-copy` はイベントベクタのみを複製し、イベントオブジェクト自体は共有する（シャローコピー）。
* `History` モジュールは Prompt・LLM・Runtime・Kernel・Trace を参照しない。
* 本モジュールは会話履歴の保存・取得のみを責務とし、履歴内容の解釈や加工は行わない。

---

# 15. 設計上の特徴

## 単方向追記モデル

History は **Append Only** を基本方針とし、イベントの削除・更新・並べ替え機能を持たない。これにより会話履歴の時系列が常に保持される。

## データ層への責務限定

History は純粋なストレージ層であり、Prompt 生成・LLM 推論・Trace 記録などの上位ロジックを一切含まない。これにより他モジュールとの結合度を最小限に抑えている。

## スナップショット対応

`history-copy` を提供することで、Runtime や Trace は履歴の状態を安全に記録できる。ただしイベント本体は共有されるため、イベントを不変オブジェクトとして扱う設計が前提となる。

## 将来の拡張性

現在の `history-event` は `role` と `content` のみを保持する最小構造であるが、将来的には以下のようなメタデータを追加しても API を維持しやすい構成となっている。

* タイムスタンプ
* Event ID
* Causal ID
* Token 数
* Source
* Metadata
* Worldline 情報

これにより、R0 のシンプルな履歴モデルから、R1 以降の因果ランタイムへの発展が可能となる。
