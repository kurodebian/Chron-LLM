# Chron-LLM Δ3 Unified Bootloader 仕様書

**Document Version** : Δ3  
**Module** : `llama-agent.lisp`  
**Layer** : Bootloader / System Initialization  
**Architecture** : Chron-LLM Δ3

---

# 1. 概要

本モジュールは Chron-LLM Δ3 全体の**統合ブートローダ（Unified Bootloader）**である。

Chron-LLM を構成する各レイヤを正しい依存順序でロードし、実行可能なシステムへ初期化する責務を持つ。

本モジュールは **依存関係管理・起動シーケンス管理・実行エントリポイント** を提供する。

---

# 2. 設計目的

本モジュールの目的は以下である。

- システム初期化
- レイヤ依存性管理
- Physical Layer切替
- Runtime起動
- 開発環境と本番環境の共通化

---

# 3. 責務

Bootloaderは以下を担当する。

- Quicklisp初期化
- 必要ライブラリロード
- モック／実機切替
- システムファイルロード
- Runtime起動
- エントリポイント提供

---

# 4. 非責務

Bootloaderは以下を担当しない。

- 推論
- Token生成
- WAL
- Graph
- Immune判定
- Prompt生成
- History管理
- World管理

---

# 5. Boot Sequence

```
Start

↓

Environment

↓

Physical Layer

↓

Logical Layer

↓

Kernel

↓

Immune

↓

Runtime

↓

Generation

↓

Main Loop
```

---

# 6. 起動メッセージ

起動時に以下を表示する。

```
=========================================
🚀 Chron-LLM Δ3 — Unified Bootloader Starting...
=========================================
```

目的は起動状態の可視化である。

---

# 7. システムディレクトリ

```
*system-dir*
```

現在ロード中の

```
*load-pathname*
```

から取得する。

```
uiop:pathname-directory-pathname
```

を利用する。

---

# 8. Physical Layer切替

```
*use-mock-physical-p*
```

により物理層を切り替える。

初期値

```
T
```

---

意味

```
T

↓

Mock Runtime
```

```
NIL

↓

Real llama.cpp
```

---

# 9. 設計意図

モック環境と実環境を

**同一ABI**

で切り替える。

上位レイヤは物理層の違いを意識しない。

---

# 10. Quicklisp初期化

ホームディレクトリの

```
quicklisp/setup.lisp
```

をロードする。

存在しない場合

```
error
```

を送出する。

---

# 11. 共通ライブラリ

ロード対象

```
CFFI

Babel
```

---

目的

```
FFI

UTF-8
```

---

# 12. Package

Quicklispロード後

```
CL-USER
```

へ戻る。

---

# 13. load-system-file

## API

```
load-system-file(filename)
```

---

### 処理

```
filename

↓

Absolute Path

↓

probe-file

↓

load
```

---

存在しない場合

```
warn
```

のみ。

停止しない。

---

# 14. Layer 1

## Physical Layer

ロード対象

```
ffi-bindings.lisp
```

または

```
ffi-bindings-mock.lisp
```

---

切替条件

```
*use-mock-physical-p*
```

---

# 15. Physical Layer責務

提供するもの

```
FFI

Mock ABI

Context

Model

Sampler
```

---

# 16. Layer 2

## Logical Layer

ロード対象

```
chron-llm.lisp
```

---

内容

- ABI
- Tokenize
- Generate
- Prefill

---

# 17. Layer 3

## Causal Kernel

ロード対象

```
chron-llm-causal.lisp
```

---

内容

```
WAL

Graph

History

Projection
```

---

# 18. Layer 4

## Immune System

ロード対象

```
immune-system.lisp
```

---

内容

```
Entropy

Health

Fault
```

---

# 19. Layer 5

## Runtime Kernel

ロード対象

```
chron-llm-runtime.lisp
```

---

内容

```
Kernel API

DTO

Context

World
```

---

# 20. Layer 6

## Generation Logic

ロード対象

```
generate.lisp
```

---

内容

```
Generation Loop

Sampling

Decode
```

---

# 21. Layer 7

## Runtime Loop

ロード対象

```
run-test.lisp
```

---

内容

```
Console

User Input

Main Loop
```

---

# 22. 完了メッセージ

全ロード完了後

```
Chron-LLM Δ3 Unified System Booted Successfully
```

を表示する。

---

# 23. エントリポイント

提供API

```
start-delta3

start-delta3-stub
```

---

# 24. start-delta3

## API

```
start-delta3(model-path)
```

---

デフォルト

```
/path/to/model.gguf
```

---

# 25. 起動フロー

```
Model Load

↓

Context Init

↓

Main Loop
```

---

# 26. Model生成

```
my-llama-model-load()
```

呼び出し。

Mock

Real

双方同一API。

---

# 27. Context生成

```
my-llama-init()
```

呼び出し。

Context Size

```
4096
```

固定。

---

# 28. Runtime起動

最後に

```
agent-main-loop(ctx,model)
```

を呼び出す。

以後Runtime制御へ移行する。

---

# 29. start-delta3-stub

## API

```
start-delta3-stub()
```

---

Mock専用。

```
agent-main-loop(nil,nil)
```

を実行する。

---

# 30. 依存関係

ロード順序

```
Physical

↓

Logical

↓

Kernel

↓

Immune

↓

Runtime

↓

Generate

↓

Run
```

この順序は厳密に維持される。

---

# 31. アーキテクチャ

```
Bootloader

├── Environment
├── Physical Layer
├── Logical Layer
├── Kernel
├── Immune
├── Runtime
├── Generation
└── Main Loop
```

---

# 32. Layer Dependency

```
Runtime
    ↓

Kernel
    ↓

Logical
    ↓

Physical
```

逆方向依存は禁止される。

---

# 33. Runtime状態

Bootloader終了後

```
Model

Context

Kernel

Immune

Runtime
```

すべて利用可能となる。

---

# 34. エラー処理

Quicklispが存在しない場合

```
error
```

発生。

---

各システムファイルが存在しない場合

```
warn
```

のみ。

起動継続。

---

# 35. 開発モード

```
Mock

↓

Runtime

↓

Kernel

↓

Immune
```

実機なしで全レイヤを検証できる。

---

# 36. 本番モード

```
Real FFI

↓

llama.cpp

↓

Runtime
```

Mockとの差異はPhysical Layerのみ。

---

# 37. 不変条件

Bootloaderは

- ABIを変更しない
- Runtime状態を保持しない
- Kernel状態を保持しない

純粋に初期化のみを担当する。

---

# 38. Chron-LLM全体での位置付け

```
Bootloader

↓

Physical Layer

↓

Logical Layer

↓

Kernel

↓

Immune

↓

Runtime

↓

Generation

↓

Agent
```

Bootloaderは全システムの唯一の起動入口である。

---

# 39. コードレビュー・設計評価

## 39.1 優れている点

### レイヤ分離

本モジュール最大の長所は、

```
Physical

↓

Logical

↓

Kernel

↓

Immune

↓

Runtime
```

というChron-LLMの設計思想がそのままロード順序に反映されていることである。

依存関係が非常に明確であり、循環依存が発生しにくい。

---

### Mock切替

```
*use-mock-physical-p*
```

だけで

```
Mock

Real
```

を切り替えられるため、

開発

CI

ユニットテスト

実機

を同じコードで運用できる。

Chron-LLMの開発速度を大きく向上させる構成である。

---

### 共通ABI

MockとFFIが

```
my-llama-*
```

ABIを共有しているため、

Runtime以降は物理層を一切意識しない。

これは非常に優れた抽象化である。

---

## 39.2 現状の課題

### ① ASDF未対応

現在は

```
(load ...)
```

を用いて手動ロードしている。

将来的には

```
ASDF System
```

で依存管理を行う方がCommon Lispらしく保守性も高い。

---

### ② 固定ロード順

ロード対象がコード中に固定されている。

今後Kernel PluginやMemory Pluginを追加する場合、

```
Plugin Registry
```

を導入すると拡張性が向上する。

---

### ③ エラー回復

現状では

```
warn
```

のみでロードを継続する。

重要モジュール（Kernel・Immune等）が欠落した状態でも起動できてしまうため、

- 必須モジュール
- 任意モジュール

を区別する仕組みがあると望ましい。

---

### ④ 起動設定

現在

```
*use-mock-physical-p*
```

はグローバル変数で切り替えている。

将来的には

```
Configuration Object
```

または

```
Boot Options
```

としてまとめると、複数設定（Context Size・Model Path・Plugin構成など）を一元管理できる。

---

# 40. 設計上の意義

このモジュールはChron-LLMにおける**システム統合点（Composition Root）**であり、各レイヤを疎結合のまま組み立てる役割を担う。

特に、**Physical LayerをMockと実機で透過的に切り替えられる設計**は、Chron-LLMの段階的開発・検証・将来のバックエンド差し替え（llama.cpp以外への対応）を容易にする重要な基盤となっている。