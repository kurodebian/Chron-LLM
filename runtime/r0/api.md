# Chron-LLM R0 Runtime

# Start Entry Specification v1.0

**Status:** Frozen Reference Specification

**Layer:** R0 Entry Layer

**Package:** `chronos-r0`

---

# 1. 概要

このファイルは **Chron-LLM R0** の最上位エントリポイントを定義する。

責務は極めて限定されており、

* Runtime生成
* Chat Loop実行

を実装せず、

**チャットシステムへの起動委譲のみ**

を行う。

---

# 2. アーキテクチャ上の位置

```
User

  │

  ▼

start-chat
  │

  ▼

chronos-r0.chat:start-chat

  │

  ▼

Chat Runtime
```

本ファイルは

**Facade**

としてのみ存在する。

---

# 3. Package

```
chronos-r0
```

このパッケージに属する。

---

# 4. 公開API

```
start-chat
```

のみを提供する。

---

# 5. 関数仕様

## start-chat

```
(start-chat)
```

### 役割

R0チャットシステムを起動する。

---

### 実装

```
(defun start-chat ()
    (chronos-r0.chat:start-chat))
```

---

### 動作

関数自身は

* Runtime生成しない
* Prompt生成しない
* Session生成しない
* History生成しない

単純に

```
chronos-r0.chat:start-chat
```

へ処理を委譲する。

---

# 6. 責務

この層の責務は

```
Entry Point
```

のみである。

つまり

```
起動要求

↓

Chat Runtimeへ転送
```

のみ行う。

---

# 7. 非責務

このモジュールは以下を一切実装しない。

## Prompt構築

×

---

## History管理

×

---

## Session管理

×

---

## Runtime生成

×

---

## Replay

×

---

## Commit

×

---

## Validation

×

---

## Policy

×

---

## LLM呼び出し

×

---

## World管理

×

---

## Graph管理

×

---

## Memory管理

×

---

# 8. 入出力仕様

入力

```
なし
```

出力

```
chronos-r0.chat:start-chat
```

の戻り値をそのまま返す。

戻り値を加工しない。

---

# 9. 呼び出し契約

```
start-chat()

↓

chronos-r0.chat:start-chat()
```

以外の副作用を持たない。

---

# 10. データフロー

```
Application

     │

     ▼

start-chat

     │

     ▼

chronos-r0.chat:start-chat

     │

     ▼

Chat Runtime
```

---

# 11. 境界

本モジュールは

```
Application Layer
```

と

```
Chat Runtime
```

との境界である。

```
Application
    │
    ▼
Entry
    │
    ▼
Runtime
```

---

# 12. 設計原則

## Thin Entry

本モジュールは

**薄いエントリポイント**

として設計されている。

処理を保持しない。

---

## Delegation

全責務を

```
chronos-r0.chat
```

へ委譲する。

---

## Stable API

アプリケーションは

```
start-chat
```

のみ知っていればよい。

内部実装が変更されても

APIは維持される。

---

# 13. アーキテクチャ上の意義

この構成により、

```
Application
        │
        ▼
Entry API
        │
        ▼
Chat Runtime
```

という依存関係が固定される。

Applicationはチャット実装の詳細を知らずに起動でき、Runtime側は内部構造を自由に変更できるため、**エントリポイントと実行系の疎結合**が実現される。

---

# 14. 不変条件（Invariants）

* `start-chat` はチャット実行処理を直接実装しない。
* `start-chat` は `chronos-r0.chat:start-chat` へ必ず委譲する。
* 引数は受け取らない。
* 戻り値は委譲先の戻り値をそのまま返す。
* 本モジュールは状態を保持しない。
* Runtime・Session・History・Prompt・Kernel状態を変更しない。
* 本モジュールは R0 Runtime の公開エントリ（Facade）としてのみ機能する。
