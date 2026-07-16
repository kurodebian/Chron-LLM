# Chron-LLM Δ3 Phase 1.1 Bootloader 詳細仕様書

---

# 1. 概要

## 目的

`llama-agent2.lisp` は Chron-LLM Δ3 の**統合ブートローダ**である。

責務は

* 実行環境初期化
* 全レイヤのロード順保証
* モック/実FFI切替
* 起動API提供

のみであり、

LLM推論、
因果処理、
Runtime、
Graph、
World、
Immune

などの実装は一切持たない。

---

# 2. システム内での位置

```
Bootloader
      │
      ▼
Physical Layer
      │
      ▼
LLM Interface
      │
      ▼
Core
      │
      ▼
Graph
      │
      ▼
World
      │
      ▼
Immune
      │
      ▼
Runtime
      │
      ▼
Generation
      │
      ▼
Test Wrapper
```

Bootloaderは唯一

**ロード順を保証するモジュール**

である。

---

# 3. 責務

Bootloaderが担当する処理

* Quicklisp初期化
* 必須ライブラリロード
* ファイル存在確認
* モジュールロード
* 起動ログ
* 起動API

---

担当しないもの

* 推論
* KV管理
* WAL
* Graph
* Runtime
* Prompt
* Event
* Memory
* Immune判定

---

# 4. 起動シーケンス

全体は10段階で構成される。

```
1 Environment
2 Physical Layer
3 LLM Interface
4 Core
5 Graph
6 World
7 Immune
8 Runtime
9 Generation
10 Test Wrapper
```

起動完了後

```
start-delta3
```

が利用可能になる。

---

# 5. Environment Initialization

## システムディレクトリ取得

```
*system-dir*
```

内容

```
(uiop:pathname-directory-pathname *load-pathname*)
```

意味

```
現在ロード中のファイルのディレクトリ
```

これを基準に全ファイルを検索する。

---

## Physical Layer切替

```
*use-mock-physical-p*
```

型

```
Boolean
```

意味

```
T
```

モック実装

```
NIL
```

実FFI

---

目的

物理層のみを差し替え可能にする。

上位レイヤは完全に同一コードで動作する。

---

# 6. Quicklisp Initialization

ロード順

```
Quicklisp
↓

CFFI

↓

Babel
```

実行

```
quicklisp/setup.lisp
```

存在しない場合

```
(error ...)
```

により即終了。

---

# 7. load-system-file

## 目的

安全なロード。

入力

```
filename
```

処理

```
merge-pathnames
↓

probe-file

↓

load
```

存在しない場合

```
error
```

を送出。

---

Phase1.1では

必須ファイル不足は全て停止。

---

# 8. Physical Layer

ロード対象

```
ffi-bindings.lisp
```

または

```
ffi-bindings-mock.lisp
```

切替条件

```
*use-mock-physical-p*
```

---

目的

以降の層は

```
my-llama-xxxx
```

ABIだけを見る。

実体は完全に隠蔽される。

---

# 9. LLM Interface

ロード

```
chron-llm.lisp
```

役割

* Event ABI
* Tokenizer
* Generate
* Prefill
* Init

---

Bootloaderは中身を知らない。

---

# 10. Core Layer

ロード

```
chron-llm-core.lisp
```

想定責務

* WAL
* Kernel
* Commit
* Projection

---

Bootloaderからは単なるロード対象。

---

# 11. Graph Layer

ロード

```
chron-llm-graph.lisp
```

責務

```
WAL
↓

Graph Projection
```

BootloaderはGraphを保持しない。

---

# 12. World Layer

ロード

```
chron-llm-world.lisp
```

責務

* Branch
* World
* Parent

Bootloaderは世界線を知らない。

---

# 13. Immune Layer

ロード

```
chron-llm-immune.lisp
```

責務

* Drift
* Fault
* Entropy

Bootloaderは免疫判定を行わない。

---

# 14. Runtime Layer

ロード

```
chron-llm-runtime.lisp
```

責務

```
Console

↓

Kernel

↓

LLM
```

BootloaderはRuntimeを生成しない。

---

# 15. Generation Layer

ロード

```
generate.lisp
```

責務

推論ループ。

BootloaderはGenerateを呼ばない。

---

# 16. Test Wrapper

ロード

```
run-test.lisp
```

目的

テスト用環境。

Phase1.1では起動時に自動ロードされる。

---

# 17. 起動ログ

開始

```
Chron-LLM Δ3 Phase 1.1 Bootloader Starting
```

終了

```
Chron-LLM Δ3 Phase 1.1 Boot Completed
```

ロード中

```
Loading Physical Layer
Loading Graph Layer
Loading Runtime
```

などが順に表示される。

---

# 18. Public API

## start-delta3

入力

```
model-path
```

既定値

```
/path/to/model.gguf
```

処理

```
Model Load

↓

Context Init

↓

agent-main-loop
```

戻り値

Runtime終了まで返らない。

---

## start-delta3-stub

目的

FFI不要でRuntimeのみ起動。

処理

```
agent-main-loop
```

引数

```
nil

nil
```

---

# 19. アーキテクチャ特性

## Layer Independence

各層は

```
load
```

のみで接続される。

依存方向

```
Boot

↓

Physical

↓

LLM

↓

Core

↓

Graph

↓

World

↓

Immune

↓

Runtime

↓

Generation
```

逆依存は禁止。

---

## Physical Swap

唯一差し替え可能なのは

```
Physical Layer
```

のみ。

```
Mock

↓

FFI
```

を変更しても

Core以上は変更不要。

---

## Strict Boot Ordering

ロード順は固定。

```
Physical

↓

LLM

↓

Core

↓

Graph

↓

World

↓

Immune

↓

Runtime

↓

Generation

↓

Test
```

変更すると依存解決に失敗する可能性がある。

---

# 20. エラー処理

Bootloaderは回復を試みない。

異常時

```
Required file not found
```

または

```
Quicklisp not found
```

で停止する。

フェイルファスト設計である。

---

# 21. Phase 1.1 制約

現在の実装では以下は対象外。

* ASDFによる依存解決
* モジュールの遅延ロード
* 動的プラグイン
* バージョン互換管理
* 設定ファイル読み込み
* ログレベル制御
* 並列ロード
* ホットリロード

---

# 22. 設計評価

このブートローダは、従来版 (`llama-agent.lisp`) と比較してモジュール構成が整理され、**Physical → LLM Interface → Core → Graph → World → Immune → Runtime → Generation** という Chron-LLM Δ3 のアーキテクチャ境界を明確に反映しています。一方で、現時点では `load` による逐次読み込みに依存しており、ASDF等による依存管理や設定の外部化は未実装です。

Phase 1.1 の範囲としては、**レイヤ分離とロード順保証を担う最小構成の統合ブートローダ**という位置付けになっています。
