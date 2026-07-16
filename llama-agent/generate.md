# Chron-LLM Δ3 Immune Runtime Generation Loop 仕様書

**Document Version** : Δ3 Immune Runtime Prototype  
**Module** : `run-llm-generation-with-sensors`  
**Layer** : Runtime / Generation Engine / Immune Integration  
**Architecture** : Chron-LLM Δ3 Runtime

---

# 1. 概要

本モジュールは Chron-LLM Δ3 における **LLM推論ランタイム** の実装であり、通常の自己回帰生成へ **Immune System（免疫系）** を統合した生成ループである。

従来の

```
Prompt

↓

Generate

↓

Output
```

ではなく、

```
Prompt

↓

Generate

↓

Immune Monitor

↓

Fault Detection

↓

Rollback

↓

Safe Termination
```

という安全性を考慮した生成パイプラインを提供する。

---

# 2. 設計目的

本モジュールは以下を目的とする。

- LLM生成中の異常監視
- 構造破綻の早期検知
- WAL汚染防止
- KV Cache保護
- RuntimeとKernelの橋渡し

---

# 3. 責務

本モジュールは以下を担当する。

- モデルロード
- Prompt Prefill
- Token生成
- Immune Sensor呼び出し
- Decode
- EOS判定
- Rollback
- Resource管理

---

# 4. 非責務

本モジュールは以下を担当しない。

- WAL実装
- Graph構築
- History
- Branch生成
- Memory
- Prompt生成
- World管理
- Projection

---

# 5. アーキテクチャ

```
Prompt

↓

Tokenizer

↓

Prefill

↓

Sampler

↓

Token

↓

Immune Sensor

↓

Decode

↓

Repeat
```

異常検知時

```
Fault

↓

Rollback

↓

KV Reset

↓

Terminate
```

---

# 6. API

## run-llm-generation-with-sensors

### 引数

```
model-path

prompt

max-tokens

wal
```

---

### model-path

GGUFモデル

---

### prompt

入力文字列

---

### max-tokens

生成上限

---

### wal

Kernel WAL

Rollback対象。

---

# 7. Runtime State

内部状態

```
Model

Context

Sampler
```

---

## model

Native Model Handle

---

## ctx

Inference Context

---

## sampler

Sampling Engine

---

# 8. Resource Management

全リソースは

```
unwind-protect
```

で管理される。

これにより

```
正常終了

例外終了
```

双方で必ず解放される。

---

# 9. 初期化

## Step1

```
init-chron-llm()
```

実行。

---

生成

```
Model

Context
```

---

# 10. Prompt Prefill

Prompt

↓

Tokenize

↓

Prefill

---

処理

```
tokenize()

↓

prefill-prompt()
```

---

## n-past

```
0
```

へ初期化。

---

# 11. Sampler

初期値

```
Temperature

0.7
```

```
Top-P

0.9
```

---

Sampler生成

```
my-sampler-init()
```

---

# 12. Generation Loop

開始

```
Step=1
```

終了

```
Step=max-tokens
```

---

# 13. Sampling

毎Step

```
Sample

↓

TokenID
```

取得。

```
my-sampler-sample()
```

---

# 14. EOS判定

取得Token

↓

```
my-llama-is-eog()
```

---

真なら

```
Generation End
```

---

戻り値

```
:eos
```

---

# 15. Token表示

取得Token

↓

```
Token To Piece
```

↓

UTF-8

↓

Console

---

処理

```
my-llama-token-to-piece()
```

利用。

---

# 16. Immune Sensor

Token毎に

```
check-immune-status()
```

呼び出し。

---

戻り値

```
Status

Entropy
```

---

# 17. Immune Status

Status

```
:ok

:warning

:fault
```

---

Entropy

```
Float
```

---

# 18. Fault Detection

以下でFault判定。

```
Status

=

:fault
```

または

```
Entropy

>

20
```

---

# 19. Fault Recovery

Fault検知

↓

KV Reset

↓

Rollback

↓

Generate停止

---

処理

```
my-llama-reset-kv()

↓

rollback-stage()

↓

:return :fault
```

---

目的

Commit前生成を破棄し

WALを汚染しない。

---

# 20. Warning

条件

```
Status

=

:warning
```

かつ

```
Entropy

>

5
```

---

処理

```
Console Log
```

のみ。

生成継続。

---

# 21. Decode

正常Token

↓

```
my-llama-eval()
```

↓

KV更新

↓

n-past++

---

Autoregressive Decode。

---

# 22. KV更新

毎Token

```
Past

↓

Past+1
```

---

# 23. Generation Pipeline

```
Sample

↓

EOS?

↓

Output

↓

Immune

↓

Decode

↓

Repeat
```

---

# 24. Fault Pipeline

```
Sample

↓

Immune

↓

Fault

↓

Reset KV

↓

Rollback

↓

Terminate
```

---

# 25. Warning Pipeline

```
Sample

↓

Immune

↓

Warning

↓

Log

↓

Decode

↓

Continue
```

---

# 26. Resource Cleanup

終了時

```
Sampler

↓

Context

↓

Model
```

順に解放。

---

関数

```
my-sampler-free()

↓

my-llama-free()

↓

my-llama-model-free()
```

---

# 27. 戻り値

正常EOS

```
:eos
```

---

Fault

```
:fault
```

---

Token上限到達

```
NIL
```

（暗黙）

---

# 28. 状態遷移

```
Init

↓

Prefill

↓

Generate

↓

Immune

↓

Decode

↓

Generate

↓

・・・

↓

EOS

↓

Cleanup
```

または

```
Generate

↓

Immune

↓

Fault

↓

Rollback

↓

Cleanup
```

---

# 29. 不変条件

Fault検知後

```
Commit

禁止
```

---

Rollback後

```
Stage

空
```

---

KV

```
Reset済
```

---

# 30. 計算量

Generation

```
O(Token数)
```

---

Immune

```
O(Token数)
```

---

Memory

```
O(1)
```

追加。

---

# 31. Runtime特徴

通常LLM

```
Prompt

↓

Generate

↓

Finish
```

Chron-LLM

```
Prompt

↓

Generate

↓

Immune

↓

Fault Detection

↓

Rollback

↓

Finish
```

Runtime自身が

```
Fault Isolation
```

を実現する。

---

# 32. Kernelとの関係

Runtimeは

```
Rollback
```

のみ行う。

History修復

Branch

Projection

などはKernel責務。

---

# 33. Immune System

Immuneは

```
Token

↓

Health

↓

Entropy

↓

Decision
```

を返す。

Runtimeは

```
Policy Executor
```

として動作する。

---

# 34. WALとの関係

本Runtimeは

```
Commit

しない。
```

Fault時

```
Rollbackのみ
```

実施。

永続化判断はKernelが担当。

---

# 35. Chron-LLM全体での位置付け

```
Prompt Builder

↓

Runtime（本モジュール）

↓

Physical Layer

↓

llama.cpp
```

Kernelとは

```
WAL

Rollback

Health
```

のみ共有する。

---

# 36. コードレビュー・設計評価

## 36.1 優れている点

本モジュールは、一般的なLLM推論ループに**免疫システム（Immune System）**を組み込んだ点が最大の特徴である。

トークン生成ごとに健全性を評価し、異常が検出された場合には**Commit前に生成を破棄**することで、履歴やWALへの汚染を防ぐ設計となっている。

---

## 36.2 RuntimeとKernelの責務分離

責務分離も明確である。

Runtimeは

- 推論
- センサー呼び出し
- Rollback要求

のみを担当し、

Kernelは

- WAL
- Projection
- Branch
- History

を管理する。

この分離はChron-LLM全体のアーキテクチャ方針と一致している。

---

## 36.3 現状の課題

このコードには、今後改善できる点もある。

### ① トークンの永続化が未実装

現在はトークンを表示するだけで、

```
stage-event()
```

によるステージングが行われていない。

そのため、`rollback-stage()`を呼び出しても、実際にはRuntime側で破棄すべき生成イベントが存在しない。

将来的には

```
Sample
    ↓
stage-event(:assistant-token)
    ↓
Immune
    ↓
Commit または Rollback
```

という構成にすると、Rollbackの意味が明確になる。

### ② Entropy閾値の固定

現在は

- Warning：Entropy > 5
- Fault：Entropy > 20

という固定閾値で判定している。

モデルや温度設定によって適切な閾値は変化するため、将来的にはモデルごとのキャリブレーションや適応的閾値を導入するとより実用的になる。

### ③ 戻り値の情報量

現在の戻り値は

```
:eos
:fault
NIL
```

のみである。

実運用では

- 終了理由
- 生成トークン数
- 最終Entropy
- Runtime統計

などを含むDTOを返すと、Kernelや監視系との連携が容易になる。

---

# 37. 設計上の意義

この実装はChron-LLMにおいて、**「生成中に異常を検知し、安全に生成を中止できるRuntime」**を初めて具体化したプロトタイプである。

一般的なLLMランタイムが「生成結果」を中心に設計されるのに対し、本モジュールは**生成過程そのものを監視対象**とし、

- Token
- Health
- Entropy
- Rollback

を統合した、安全性を重視した推論パイプラインを実現している。