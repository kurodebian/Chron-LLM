# Chron-LLM Δ3 Immune System（Entropy Sensor）仕様書

**Document Version** : Δ3  
**Module** : `immune.lisp`  
**Layer** : Kernel / Immune Service  
**Architecture** : Chron-LLM Δ3

---

# 1. 概要

本モジュールは Chron-LLM Δ3 における **Immune System（免疫系）** を実装する。

LLM が生成するトークン列の **確率分布（Logits）** を監視し、その情報量（Shannon Entropy）から生成状態の健全性を判定する。

このモジュールは **生成品質そのものではなく、生成状態の構造的健全性** を監視するためのセンサー層である。

---

# 2. 目的

Immune System の目的は以下である。

- LLM生成状態の監視
- ドリフト検知
- 構造破綻検知
- Runtimeへの警告通知
- Rollback判断材料の提供

---

# 3. 責務

本モジュールは以下を担当する。

- Logits取得
- Shannon Entropy計算
- 健全性判定
- Warning判定
- Fault判定

---

# 4. 非責務

本モジュールは以下を担当しない。

- Token生成
- Sampler
- Decode
- KV管理
- WAL
- Rollback
- Graph
- History
- World管理
- Prompt生成

---

# 5. アーキテクチャ

```
LLM Context

↓

Logits

↓

Entropy

↓

Immune Decision

↓

Runtime
```

---

# 6. モジュール構成

```
Immune Parameters

↓

FFI

↓

Entropy Calculation

↓

Health Decision
```

---

# 7. 初期化

ロード時

```
Quicklisp

↓

CFFI
```

をロードする。

```
(eval-when
 ...
 (ql:quickload :cffi))
```

---

# 8. 設定パラメータ

## Fault Threshold

```
*entropy-fault-threshold*
```

初期値

```
3.5
```

---

### 意味

Entropy がこの値を超えると

```
:fault
```

と判定する。

---

## Warning Threshold

```
*entropy-warning-threshold*
```

初期値

```
2.5
```

---

### 意味

Entropy がこの値を超えると

```
:warning
```

と判定する。

---

# 9. FFI

本モジュールは

```
ffi-bindings.lisp
```

を利用する。

---

使用FFI

```
my_llama_get_logits
```

```
my_llama_n_vocab
```

---

# 10. Logits取得

```
%llama-get-logits(ctx)
```

↓

```
float*
```

---

返却値

```
Vocabulary全体のLogits
```

---

# 11. Vocabulary取得

```
%llama-n-vocab(ctx)
```

↓

```
int
```

---

意味

```
語彙数
```

---

# 12. calculate-entropy

## API

```
calculate-entropy(ctx)
```

---

戻り値

```
Single Float
```

Entropy値。

---

# 13. Null Context

ctxが

```
NIL
```

の場合

```
1.0

～

1.8
```

程度のランダム値を返す。

```
1.0 + random(0.8)
```

---

用途

Mock

Test

Simulation

---

# 14. 数値安定化

Softmax計算では

```
最大Logit
```

を減算する。

```
exp(x-max)
```

形式。

---

目的

Overflow防止。

---

# 15. 最大Logit探索

最初のループ

```
O(V)
```

で

```
max-logit
```

取得。

---

# 16. Softmax分母

第二ループ

```
Σexp
```

を計算。

```
sum-exp
```

---

# 17. Shannon Entropy

第三ループ

```
P(i)

=

Softmax
```

計算。

---

Entropy

```
H

=

-ΣP logP
```

---

実装

```
(decf entropy

(* p (log p)))
```

---

# 18. 微小確率除外

```
P

<

1e-6
```

は無視する。

---

目的

数値誤差低減。

---

# 19. 戻り値

Entropy

↓

```
Single Float
```

へ変換。

---

# 20. check-immune-status

## API

```
check-immune-status(ctx,next-id)
```

---

next-id

現状では未使用。

将来

```
Token依存判定
```

用。

---

# 21. 判定フロー

```
Entropy

↓

Fault?

↓

Warning?

↓

Healthy
```

---

# 22. Fault判定

条件

```
Entropy

>

3.5
```

---

戻り値

```
:fault

Entropy
```

---

# 23. Warning判定

条件

```
Entropy

>

2.5
```

---

戻り値

```
:warning

Entropy
```

---

# 24. Healthy判定

条件

```
Entropy

<=

2.5
```

---

戻り値

```
:healthy

Entropy
```

---

# 25. Runtime連携

Runtimeは

```
check-immune-status()
```

を

```
毎Token
```

呼び出す。

---

返却値

```
Status

Entropy
```

に応じ

```
Continue

Warning

Rollback
```

を決定する。

---

# 26. Fault Pipeline

```
Token

↓

Entropy

↓

Fault

↓

Runtime

↓

KV Reset

↓

Rollback

↓

Stop
```

---

# 27. Warning Pipeline

```
Token

↓

Entropy

↓

Warning

↓

Log

↓

Continue
```

---

# 28. Healthy Pipeline

```
Token

↓

Entropy

↓

Healthy

↓

Decode
```

---

# 29. 計算量

最大Logit探索

```
O(V)
```

---

Softmax

```
O(V)
```

---

Entropy

```
O(V)
```

---

総計

```
O(3V)

≈

O(V)
```

---

# 30. メモリ使用量

追加メモリ

```
O(1)
```

---

保持変数

```
max-logit

sum-exp

entropy
```

のみ。

---

# 31. 数値特性

本実装は

```
Log-Sum-Exp
```

安定化法を利用する。

---

特徴

Overflow耐性

高い。

---

# 32. エラー処理

ctxが無い場合

```
Simulation Mode
```

へ移行。

例外を発生させない。

---

# 33. Kernelとの関係

Kernelは

```
Health State
```

を管理する。

Immuneは

```
Health Sensor
```

として機能する。

---

# 34. Runtimeとの関係

Runtimeは

```
Decision Executor
```

Immuneは

```
Decision Sensor
```

である。

---

# 35. Chron-LLM全体での位置付け

```
Physical Layer

↓

Logits

↓

Immune（本モジュール）

↓

Runtime

↓

Kernel

↓

WAL
```

---

# 36. 不変条件

Entropy計算は

```
Logits
```

のみから導出される。

外部状態に依存しない。

---

判定は

```
Healthy

↓

Warning

↓

Fault
```

の単調閾値構造を持つ。

---

# 37. コードレビュー・設計評価

## 37.1 優れている点

本モジュールは **モデル内部の確率分布（Logits）** を直接利用して生成状態を評価するため、生成された文字列ではなく**生成過程**を監視できる。

また、Log-Sum-Expによる数値安定化を採用しており、大規模語彙に対しても比較的安定したエントロピー計算が可能である。

Runtime・Kernel・Immuneの責務分離も明確であり、Immuneは純粋な「センサー」として機能する設計になっている。

---

## 37.2 現状の課題

### ① 計算コスト

毎トークンごとに全語彙 (`n_vocab`) を3回走査するため、

```
O(3V)
```

の計算量となる。

Phi-4 Miniのように語彙数が20万近いモデルでは、この処理を毎トークン実行するとオーバーヘッドが大きい。

実運用では、

- Top-K近似
- Top-P近似
- C側でEntropyを計算するFFI

などの高速化が望ましい。

### ② 固定閾値

現在の

- Warning = 2.5
- Fault = 3.5

という閾値は固定値である。

モデルサイズやTemperature、Sampling方式によって適切な範囲は変わるため、モデルごとの自動キャリブレーションや動的閾値設定が今後の課題となる。

### ③ next-id未使用

`check-immune-status(ctx, next-id)` の `next-id` は現状では無視されている。

将来的には、

- 特殊トークン監視
- 禁止トークン検出
- EOS近傍の異常判定

などに利用できる拡張ポイントとなる。

### ④ センサー情報の不足

現在の戻り値は

```
(Status, Entropy)
```

のみである。

将来的には、

- Top-1確率
- Top-K分布
- Perplexity
- Margin（Top1−Top2）
- Temperature補正値

なども返却すると、より高度な免疫判定が可能になる。

---

# 38. 設計上の意義

本モジュールはChron-LLMにおいて、**「LLMをブラックボックスではなく観測可能なシステムとして扱う」**という設計思想を具体化した中核コンポーネントである。

生成された文章ではなく、**生成直前の確率分布**を解析することで、構造的なドリフトや破綻を早期に検知できる点が特徴であり、Chron-LLM全体の安全性・自己監視能力を支える基盤となる。