# Chron-LLM Δ3 論理層・共通ABI・LLM Runtime 仕様書

**Document Version** : Δ3 Phase1  
**Module** : Logical Layer / Common ABI / LLM Runtime  
**Layer** : Foundation Layer

---

# 1. 概要

本モジュールはChron-LLM全体の最下位論理層であり、

- 共通ABI
- Event定義
- Runtime Node定義
- Tokenization
- Prompt Prefill
- LLM Generation
- Model初期化

を提供する。

Chron-LLMの全レイヤはここで定義されるABIを共有する。

---

# 2. アーキテクチャ

```
                 Runtime
                     │
                     ▼
                Chron Kernel
                     │
                     ▼
             Graph Projection
                     │
                     ▼
               Write Ahead Log
                     │
                     ▼
            Logical Layer (ABI)
                     │
                     ▼
               llama.cpp Wrapper
                     │
                     ▼
                 llama.cpp
```

Logical LayerはKernelより下位に位置する。

---

# 3. 責務

本モジュールが担当するもの

- Event ABI
- Runtime Node
- Tokenize
- Prompt Prefill
- Streaming Decode
- Model Initialization
- Common Utility

---

# 4. 非責務

本モジュールは以下を担当しない。

- History
- Graph
- Kernel
- World
- Memory
- Prompt Builder
- Immune
- Replay
- Validation

---

# 5. 共通ABI

## 目的

Chron-LLM全レイヤが共有するデータ構造を定義する。

```
Runtime

Kernel

History

Graph

WAL
```

すべて同じEvent ABIを利用する。

---

# 6. Event構造

## event

永続イベント

```
Header

+

Payload
```

から構成される。

---

## Header

### index

```
WAL位置
```

永続順序

---

### clock

```
論理時計
```

Commit順序

---

### node-id

```
永続Node ID
```

一意

---

### causal-id

```
世界線ID
```

Branch単位

---

### kind

イベント種別

例

```
:user-message

:assistant-reply

:branch
```

---

## Payload

利用者データ

型

```
Property List
```

例

```
:text

:parent-world
```

---

# 7. Event設計原則

```
Header

↓

Kernel管理

Payload

↓

利用者データ
```

HeaderはKernelのみ更新可能。

Payloadはイベント内容を保持する。

---

# 8. Runtime Node

## node

Runtime互換構造

現在

```
将来互換
```

用に保持される。

---

### ID

Node識別子

---

### Kind

Node種別

---

### Content

内容

---

### Parent

親Node

---

### Worldline

世界線

初期

```
:wl-0
```

---

### Status

```
:active

:fault
```

---

# 9. Nodeの位置付け

Nodeは

```
Runtime Object
```

である。

永続化対象ではない。

将来的には

```
Graph Node
```

へ統合予定。

---

# 10. Runtime State

## *n-past*

現在KV Cache長

```
Past Tokens
```

を管理する。

Prefill

↓

Decode

で更新される。

---

# 11. Token Streaming

## print-token-stream()

### 目的

Token

↓

Byte列

↓

UTF-8

↓

Console

変換

---

### 入力

```
Model

Token ID
```

---

### 出力

```
Byte Vector
```

---

### 処理

```
Token

↓

Piece

↓

Bytes

↓

Console

↓

Return Bytes
```

---

# 12. Tokenize

## tokenize()

### 目的

文字列

↓

Token列

変換

---

### 入力

```
Model

Text
```

---

### 出力

```
List<Token>
```

---

### アルゴリズム

UTF8変換

↓

Pass1

必要サイズ取得

↓

Pass2

Token生成

---

### エラー

```
0 Tokens

↓

Error
```

```
Negative

↓

Error
```

---

# 13. Prompt Prefill

## prefill-prompt()

### 目的

PromptをKV Cacheへ投入する。

---

### 入力

```
Context

Token List
```

---

### 処理

```
Token Array

↓

llama_eval()

↓

KV Cache

↓

n_past更新
```

---

### 更新

```
*n-past*

+=

Prompt Length
```

---

# 14. Generation

## generate()

### 目的

Streaming Generation

---

### 入力

```
Context

Model

Temperature

TopP

MaxTokens
```

---

### 出力

```
Generated String
```

---

# 15. Generation Pipeline

```
Sampler生成

↓

Sample

↓

EOG?

↓

Print Token

↓

Decode

↓

KV更新

↓

Loop
```

---

# 16. Sampling

Sampler生成

```
Temperature

TopP
```

設定

---

Sampling

```
Sampler

↓

Token ID
```

---

# 17. End判定

```
my-llama-is-eog()
```

で終了判定。

終了時

```
Generation終了
```

---

# 18. Decode

取得Token

↓

Console表示

↓

Eval

↓

KV更新

---

### 更新

```
*n-past*

++

```

---

# 19. Generation結果

Streaming中

```
Bytes保存
```

終了後

```
Bytes結合

↓

UTF8変換

↓

String返却
```

---

# 20. Sampler管理

Sampler生成

↓

Generation

↓

Free

必ず

```
unwind-protect
```

で解放。

---

# 21. 初期化

## init-chron-llm()

### 入力

```
Model Path

Context Size
```

---

### 出力

```
Model

Context
```

---

### 初期化

```
Model Load

↓

Context生成

↓

n_past=0
```

---

# 22. Runtime Flow

```
Model

↓

Tokenize

↓

Prefill

↓

Generate
```

---

# 23. データフロー

```
Prompt

↓

UTF8

↓

Tokens

↓

KV

↓

Sample

↓

Token

↓

Bytes

↓

UTF8

↓

Reply
```

---

# 24. エラー処理

Tokenize失敗

↓

例外

---

Prefill失敗

↓

例外

---

Decode失敗

↓

例外

---

Model Load失敗

↓

例外

---

# 25. 不変条件

Generation開始時

```
n_past

=

Prompt Length
```

Generation終了後

```
n_past

=

Prompt

+

Generated
```

Samplerは必ず解放される。

---

# 26. 計算量

Tokenize

```
O(n)
```

---

Prefill

```
O(n)
```

---

Generation

```
O(tokens)
```

---

Token Print

```
O(piece)
```

---

# 27. Phase1制約

実装済

- Event ABI
- Runtime Node
- Tokenize
- Prefill
- Generate
- Streaming
- Model初期化

未実装

- Chat Template
- Prompt Builder
- Memory Search
- Tool Calling
- Grammar
- Structured Output
- KV Reset API
- Multi Session
- Batch Decode

---

# 28. ABI設計原則

EventはChron-LLM全体で唯一の共通ABIである。

```
Runtime

↓

Kernel

↓

WAL

↓

Graph

↓

History
```

すべて同じEventを共有する。

HeaderはKernel管理、

Payloadは利用者データである。

---

# 29. LLM Runtime設計原則

LLM Runtimeは

```
Prompt

↓

Token

↓

Generation
```

のみ担当する。

LLMは

- History
- World
- Graph
- Memory
- Kernel

を一切知らない。

完全に

```
Prompt In

↓

Text Out
```

の純粋推論器として設計される。

---

# 30. 将来拡張

Phase2

- KV Reset
- Batch Decode
- Streaming Callback
- Metrics

Phase3

- Speculative Decode
- Prefix Cache
- Continuous Batching

Phase4

- Prompt Builder統合
- Tool Calling
- Memory Retrieval
- Structured Generation

---

# 31. コードレビュー・設計評価

## 31.1 モジュール責務の混在

現在の `chron-llm.lisp` は以下の異なる責務を1ファイルに含んでいます。

- 共通ABI（`event`, `node`）
- LLMラッパー（tokenize, prefill, generate）
- モデル初期化
- ユーティリティ

設計上は以下のように分割すると責務が明確になります。

```
chron-abi.lisp
    Event
    Node

chron-tokenizer.lisp
    tokenize
    print-token-stream

chron-generation.lisp
    prefill
    generate

chron-model.lisp
    init-chron-llm
```

---

## 31.2 `*n-past*` のグローバル状態

`*n-past*` はグローバル変数であり、

- マルチセッション
- マルチモデル
- 並列生成

には対応できません。

将来的には

```
LLM Context
    ├── ctx
    ├── sampler
    └── n-past
```

のようにコンテキストへ保持する方が拡張性があります。

---

## 31.3 Event ABI

`event` 構造体はChron-LLM全体の基盤となる設計であり、

HeaderとPayloadの分離も適切です。

特に、

- `index`
- `clock`
- `node-id`
- `causal-id`

をHeaderへ固定している点は、WAL・Graph・History・Replayが共通の意味論を持てるため、アーキテクチャ上非常に重要です。

---

## 31.4 `node` 構造体

現状ではほぼ利用されておらず、「旧互換・将来拡張用」とコメントされています。

今後 `causal-node` が正式なGraphノードとなるのであれば、この構造体との役割分担または統合方針を仕様で明確に定義しておくことが望まれます。

---

# 32. 総合評価

このモジュールは **Chron-LLMの共通ABIとLLM実行基盤を提供する土台**です。

設計思想としては、

- Eventを唯一の共通ABIとする
- LLMを「Prompt → Text」の純粋推論器に限定する
- KernelやHistoryの概念を一切持ち込まない

という責務分離が徹底されており、Chron-LLM全体のレイヤ構造を支える基盤モジュールとなっています。

一方で、実装面では責務が1ファイルに集約されているため、将来的にはABI・Tokenizer・Generation・Model初期化を分離することで保守性と拡張性がさらに向上します。