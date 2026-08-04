# Chron-LLM Δ3 Physical Layer（FFI Bindings）仕様書

**Document Version** : Δ3 Physical Layer v3  
**Module** : `ffi-bindings.lisp`  
**Layer** : Physical Layer / Native FFI Binding Layer  
**Architecture Level** : Hardware Abstraction Layer (HAL)

---

# 1. 概要

本モジュールは Chron-LLM Δ3 の最下層に位置する **Physical Layer** であり、Common Lisp と `llama.cpp`（C Wrapper）との橋渡しを行う FFI（Foreign Function Interface）層である。

Chron-LLM の上位レイヤは、本モジュールを介してのみ推論エンジンへアクセスする。

---

# 2. 設計目的

本モジュールの目的は、

- Lisp と C の境界を完全に抽象化する
- llama.cpp 依存を Physical Layer のみに閉じ込める
- Runtime・Kernel・Graph を C 実装から独立させる
- ABI を安定化し、将来のバックエンド差し替えを容易にする

ことである。

---

# 3. アーキテクチャ

```
Application

↓

Runtime

↓

Kernel

↓

Prompt Builder

↓

Physical Layer（本モジュール）

↓

C Wrapper

↓

llama.cpp

↓

GGUF Model
```

本モジュールより上位は CFFI を直接利用しない。

---

# 4. 責務

本モジュールは以下のみを担当する。

- CFFI型定義
- 外部関数定義
- ABI公開
- ライフサイクル管理
- 推論API公開

---

# 5. 非責務

以下は担当しない。

- Prompt生成
- Token管理
- KV管理ロジック
- WAL
- Graph
- Memory
- Runtime制御
- Scheduler
- History
- Branch

---

# 6. パッケージ定義

```
(defpackage :chron-llm ...)
```

Physical Layer がシステムの起点（創世主）となり、

- パッケージ生成
- 公開シンボル定義

を担当する。

---

# 7. Export API

公開される主なAPIは以下の通り。

## Runtime API

```
init-chron-llm

tokenize

prefill-prompt

generate
```

---

## Runtime State

```
*n-past*
```

---

## 起動API

```
start-delta3

start-delta3-stub
```

---

## ライフサイクル管理

```
my-llama-free

my-llama-model-free

my-llama-reset-kv
```

---

## Kernel ABI

```
event

make-event

ev-index

ev-clock

ev-causal-id

ev-kind

ev-payload
```

これにより、Kernel と Physical Layer が同一パッケージを共有できる。

---

# 8. CFFI型定義

## llama-token

```
:int32
```

Chron-LLM 内部では

```
llama-token

↓

int32
```

として扱われる。

---

# 9. モデルロードAPI

## my-llama-model-load

### C Prototype

```c
void* my_llama_model_load(char* path);
```

---

### Lisp

```lisp
(path :string)
```

---

### 戻り値

```
:pointer
```

モデルポインタ。

---

### 役割

```
GGUF

↓

Model Handle
```

生成。

---

# 10. Context生成API

## my-llama-init

### C Prototype

```c
void* my_llama_init(model, n_ctx);
```

---

### 引数

```
Model Pointer

Context Size
```

---

### 戻り値

```
Context Pointer
```

---

### 役割

推論コンテキスト生成。

---

# 11. Vocabulary取得

## my-llama-model-get-vocab

### 入力

```
Model
```

---

### 出力

```
Vocabulary Pointer
```

Tokenizerが利用する。

---

# 12. 推論評価API

## my-llama-eval

### C Prototype

```c
int my_llama_eval(...)
```

---

### 入力

```
Context

Token Buffer

Token Count

n-past
```

---

### 戻り値

```
int32
```

---

### 成功

```
0
```

---

### 用途

```
Prefill

Decode
```

双方で利用される。

---

# 13. Token文字列変換

## my-llama-token-to-piece

### 入力

```
Model

Token ID

Buffer

Length
```

---

### 出力

```
文字列長
```

BufferへUTF-8を書き込む。

---

# 14. Tokenizer

## my-llama-tokenize

### 入力

```
Vocabulary

Text

Length

Output Buffer

Max Tokens

Add Special

Parse Special
```

---

### 戻り値

```
Token Count
```

---

### 特徴

2パス方式を想定。

```
Pass1

必要サイズ取得

↓

Pass2

実Token生成
```

---

# 15. EOG判定

## my-llama-is-eog

### 入力

```
Context

Token
```

---

### 出力

```
bool
```

---

### 用途

生成終了判定。

---

# 16. Sampler生成

## my-sampler-init

### 入力

```
Temperature

Top-P
```

---

### 出力

```
Sampler Pointer
```

---

# 17. Sampling

## my-sampler-sample

### 入力

```
Sampler

Context
```

---

### 出力

```
Token ID
```

---

### 用途

次トークン生成。

---

# 18. Sampler解放

## my-sampler-free

### 入力

```
Sampler
```

---

### 戻り値

```
void
```

---

# 19. Context解放

## my-llama-free

### 入力

```
Context
```

---

### 戻り値

```
void
```

---

### 用途

KV・Context破棄。

---

# 20. Model解放

## my-llama-model-free

### 入力

```
Model
```

---

### 戻り値

```
void
```

---

### 用途

GGUFアンロード。

---

# 21. KV Reset

## my-llama-reset-kv

### 入力

```
Context
```

---

### 戻り値

```
void
```

---

### 用途

```
KV Cache

↓

Reset
```

---

# 22. Physical Layer API一覧

```
my-llama-model-load

my-llama-init

my-llama-model-get-vocab

my-llama-eval

my-llama-tokenize

my-llama-token-to-piece

my-llama-is-eog

my-sampler-init

my-sampler-sample

my-sampler-free

my-llama-free

my-llama-model-free

my-llama-reset-kv
```

---

# 23. データフロー

```
Prompt

↓

Tokenizer

↓

Token Buffer

↓

Eval

↓

Sampler

↓

Token

↓

Eval

↓

・・・
```

---

# 24. ライフサイクル

```
Load Model

↓

Create Context

↓

Tokenize

↓

Prefill

↓

Generate

↓

Reset（任意）

↓

Destroy Context

↓

Unload Model
```

---

# 25. ABI設計原則

すべての関数は

```
Lisp

↓

C Wrapper

↓

llama.cpp
```

の一対一対応を維持する。

Lisp側で推論ロジックを持たない。

---

# 26. エラー処理

本モジュール自身はエラー処理を行わない。

戻り値はそのまま上位レイヤへ返される。

判定責務は

```
Runtime

または

Kernel
```

が担当する。

---

# 27. 不変条件

Physical Layer は

```
State-less
```

であることを原則とする。

保持するのは

```
Native Pointer
```

のみ。

---

# 28. 計算量

各APIは Native Call のラッパであり、

```
O(1)
```

として扱われる。

実際の計算量は llama.cpp 側に依存する。

---

# 29. 実装上の特徴

このモジュールは **純粋なABI定義** に徹しており、

- ロジック
- 状態管理
- メモリ管理方針

を一切持たない。

そのため、Chron-LLM全体の中で最も安定したレイヤとなることを目的としている。

---

# 30. モック版との対応

本モジュールには `ffi-bindings-mock.lisp` に対応するモック実装が存在する。

| Real FFI | Mock FFI |
|----------|----------|
| CFFI経由でC Wrapper呼び出し | Lisp構造体のみ |
| 実際のGGUFモデル | ダミーモデル |
| 実際のKV Cache | 擬似KV状態 |
| 実トークナイズ | 固定値 |
| 実サンプリング | 固定トークン |

両者は**同一ABI**を持つため、RuntimeやKernelは実装を意識せず切り替え可能である。

---

# 31. Chron-LLM全体での位置付け

本モジュールはChron-LLMの**唯一のネイティブ依存層**である。

```
Kernel
    ↓
Runtime
    ↓
Physical Layer（本モジュール）
    ↓
C Wrapper
    ↓
llama.cpp
```

この構造により、将来的に `llama.cpp` 以外の推論エンジン（ONNX Runtime、vLLM、MLXなど）へ移行する場合でも、Physical Layerのみを差し替えることで上位アーキテクチャを維持できる。

---

# 32. コードレビュー・設計評価

## 32.1 優れている点

- **責務が明確**で、FFIバインディング以外のロジックを持たない。
- **ABIをパッケージレベルで公開**しており、Chron-LLM全体のインターフェースが一元化されている。
- **モック実装と実実装のシグネチャが一致**しているため、テスト環境と本番環境の切り替えが容易。

## 32.2 改善が望まれる点

現在のコードでは、エクスポートしている

```
init-chron-llm
tokenize
prefill-prompt
generate
start-delta3
start-delta3-stub
```

などは本ファイル内では定義されておらず、別モジュールに実装されることを前提としている。

そのため、**Physical Layer専用モジュール**として整理するなら、

- FFI定義
- 型定義
- ライフサイクルAPI

のみをエクスポートし、Runtime APIは別パッケージへ分離すると、依存関係がさらに明確になる。