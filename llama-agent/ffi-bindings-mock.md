# Chron-LLM Δ3 Mock Physical Layer（FFI Bindings Mock）仕様書

**Document Version** : Δ3 Mock Physical Layer  
**Module** : `ffi-bindings-mock.lisp`  
**Layer** : Physical Layer (Mock) / FFI ABI Compatibility Layer

---

# 1. 概要

本モジュールは Chron-LLM Δ3 における **物理層（Physical Layer）** のモック実装である。

目的は、実際の `llama.cpp` や CFFI を使用せずに、

- Runtime
- Kernel
- Prompt
- Reset
- Token Pipeline

など上位レイヤを単体で開発・検証できるようにすることである。

---

# 2. 設計目的

Chron-LLMは以下のような層構造を採用する。

```
Application

↓

Runtime

↓

Kernel

↓

Prompt

↓

Physical Layer

↓

llama.cpp
```

本モジュールは

```
Physical Layer
```

のみをモック化する。

---

# 3. 責務

本モジュールは以下のみ担当する。

- FFI ABI互換
- Model生成
- Context生成
- KV Cache管理
- Eval実行
- Sampler
- Tokenizer
- Resource解放

---

# 4. 非責務

以下は担当しない。

- Prompt構築
- History
- Graph
- WAL
- Kernel
- Memory
- Branch
- Runtime制御

---

# 5. パッケージ初期化

```
(unless (find-package :chron-llm)
    ...
)
```

目的

```
Package存在確認

↓

未定義なら生成
```

これにより単独ロードが可能となる。

---

# 6. アーキテクチャ

```
Runtime

↓

Mock ABI

↓

Mock Context

↓

Mock Model
```

すべて Lisp オブジェクトのみで構成される。

---

# 7. Mock Model

## mock-model

保持情報

```
Model Path
```

---

### path

ロード対象モデル名

例

```
phi4.gguf
```

---

# 8. Mock Context

## mock-ctx

保持情報

```
Model

Context Size

KV Position
```

---

### model

対応モデル

---

### context-size

KV最大長

初期値

```
4096
```

---

### kv-past-tokens

現在のKV位置

---

# 9. Model Load

## my-llama-model-load()

目的

```
Model

↓

Mock Model
```

生成

---

入力

```
Model Path
```

---

出力

```
mock-model
```

---

副作用

```
Console表示
```

---

# 10. Context Init

## my-llama-init()

目的

```
Model

↓

Mock Context
```

生成

---

入力

```
Model

Context Size
```

---

出力

```
mock-ctx
```

---

# 11. KV Trim

## my-llama-kv-cache-seq-rm()

目的

KVキャッシュの巻き戻し。

---

入力

```
Sequence

Start

End
```

---

実装

```
kv-past

=

Start
```

---

戻り値

```
0
```

成功コード。

---

# 12. Eval

## my-llama-eval()

目的

```
Prefill

Generate
```

共通評価API。

---

入力

```
Context

Tokens

Token Count

n-past
```

---

処理

```
KV

=

n-past

+

Token Count
```

---

戻り値

```
0
```

成功。

---

# 13. Vocabulary

## my-llama-model-get-vocab()

戻り値

```
:mock-vocab
```

固定。

---

# 14. Tokenize

## my-llama-tokenize()

目的

Tokenizer ABI互換。

---

現在

```
1 Token
```

固定。

---

戻り値

```
1
```

---

実際には

```
tokens
```

配列は変更しない。

---

# 15. Token To Piece

## my-llama-token-to-piece()

目的

Token

↓

文字列

変換。

---

現在

```
0 byte
```

返却。

---

実際の文字列生成は行わない。

---

# 16. EOG判定

## my-llama-is-eog()

目的

```
End Of Generation
```

判定。

---

現在

```
常に NIL
```

---

そのため

```
Generate Loop
```

は終了しない。

---

# 17. Sampler

## my-sampler-init()

入力

```
Temperature

Top-P
```

---

戻り値

```
:mock-sampler
```

---

# 18. Sampling

## my-sampler-sample()

現在

```
42
```

固定返却。

---

実際の確率計算は存在しない。

---

# 19. Sampler Free

## my-sampler-free()

目的

Sampler解放。

---

現在

```
t
```

返却。

---

# 20. Context Free

## my-llama-free()

目的

Context破棄。

---

副作用

```
Console表示
```

---

戻り値

```
t
```

---

# 21. Model Free

## my-llama-model-free()

目的

Model破棄。

---

戻り値

```
t
```

---

# 22. KV Reset

## my-llama-reset-kv()

目的

```
KV Cache

↓

Reset
```

---

現在

Console表示のみ。

---

戻り値

```
t
```

---

# 23. Physical Layer API

提供されるABI一覧

```
my-llama-model-load

my-llama-init

my-llama-eval

my-llama-reset-kv

my-llama-kv-cache-seq-rm

my-llama-tokenize

my-llama-token-to-piece

my-llama-model-get-vocab

my-llama-is-eog

my-sampler-init

my-sampler-sample

my-sampler-free

my-llama-free

my-llama-model-free
```

---

# 24. Runtimeから見たデータフロー

```
Prompt

↓

Tokenize

↓

Eval

↓

Sample

↓

Eval

↓

Sample

↓

・・・
```

---

# 25. KV更新

Eval時

```
KV

=

Past

+

Token Count
```

となる。

---

# 26. Reset

```
Reset

↓

KV Clear

↓

Past = 0
```

概念のみ提供。

---

# 27. ABI互換性

本モジュールは

```
llama.cpp

↓

C Wrapper

↓

CFFI
```

の代替として設計されている。

Runtimeから見ると

```
Real

Mock
```

の差異を意識しない。

---

# 28. モックの特徴

すべて

```
成功
```

する。

例外

```
なし
```

---

Sampler

```
固定
```

---

Tokenizer

```
固定
```

---

Model

```
固定
```

---

# 29. 制限事項

現実のLLM動作とは異なる。

以下は未実装。

- 実トークナイズ
- 実サンプリング
- KV管理
- EOG判定
- Decode
- Context Overflow
- GPU
- Memory Allocation

---

# 30. 不変条件

すべてのABIは

```
llama.cpp ABI
```

と同一シグネチャを維持することを目的とする。

戻り値

```
0

=

Success
```

を維持する。

---

# 31. 計算量

Model Load

```
O(1)
```

---

Init

```
O(1)
```

---

Eval

```
O(1)
```

---

Sampler

```
O(1)
```

---

Reset

```
O(1)
```

---

# 32. 実装上の意義

本モジュールはChron-LLMの**ハードウェア抽象化層（Hardware Abstraction Layer, HAL）**に相当する。

上位レイヤは、実機の `llama.cpp` を使用しているか、本モックを使用しているかを意識せずに開発できる。これにより、

- Kernel
- Runtime
- Prompt Builder
- Memory
- World Service

などを物理層から独立して実装・テストできる。

---

# 33. コードレビュー・設計評価

## 33.1 優れている点

この実装は**ABI互換性**を最優先として設計されている。

関数名・引数・戻り値を実際の `llama.cpp` ラッパーに合わせているため、実装差し替え時に上位コードを変更する必要がほとんどない。

---

## 33.2 抽象化レベル

本モジュールは

```
Runtime
    ↓
Physical ABI
```

という明確な境界を提供している。

この設計により、実機版・モック版・将来的な別バックエンド（ONNX RuntimeやvLLMなど）も同一ABIで接続できる。

---

## 33.3 現在の制約

PoCとしては十分だが、現在は以下が簡略化されている。

- `my-llama-tokenize()` は常に1トークン
- `my-sampler-sample()` は常に42
- `my-llama-is-eog()` は常にNIL
- `my-llama-token-to-piece()` は空文字

そのため、実際の生成品質やコンテキスト挙動の検証には使用できず、**制御フロー検証専用**のモックとなっている。

---

# 34. Chron-LLM全体での位置付け

Chron-LLM全体では、本モジュールは**Physical Layer Adapter**として位置付けられる。

```
Kernel
    ↓
Runtime
    ↓
Physical Layer ABI
    ↓
Mock Physical Layer（本実装）
         または
llama.cpp FFI
```

この分離により、Chron-LLMは推論エンジンに依存しない設計となっており、物理バックエンドを交換してもKernel・WAL・Graph・World Serviceには影響を与えない。