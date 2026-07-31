# Chron-LLM R1 Specification

# IR Divergence Analysis Layer

**Version**
: R1 Phase-1

**Status**
: Stable Baseline

**Layer**
: Observation Analysis Layer

**Package**

```lisp
ir-divergence
```

# 1. 概要

`ir-divergence` は Chron-LLM の **Observation Analysis Layer** に属する解析モジュールであり、複数回のLLMデコード実行から得られた IR（Intermediate Representation）を比較し、推論過程の**分岐性（Divergence）**を定量的に評価する。

本モジュールは観測専用であり、LLM の推論結果や Runtime の状態には一切影響を与えない。

# 2. 設計目的

LLM は同一プロンプトであっても、

* Sampling
* Temperature
* Top-p

などの影響により異なる生成系列を生成する。

本モジュールは、

```
Prompt
   │
   ├── Run1
   ├── Run2
   ├── Run3
   │
   ▼
IR Streams
   │
   ▼
Agreement Analysis
```

を行い、

**どの位置から推論が分岐し始めるか**

を測定することを目的とする。

# 3. アーキテクチャ上の位置

```
LLM Backend

      │

      ▼

IR Callback

      │

      ▼

IR Stream

      │

      ▼

IR Divergence Analysis
（本モジュール）

      │

      ▼

Statistics

      │

      ▼

Visualization / Research
```

Kernel には接続されない。

# 4. 責務

本モジュールが担当するもの

* IR抽出
* Phase-1 Action抽出
* 複数回推論実行
* Token一致率測定
* Divergence統計生成

担当しないもの

* Candidate生成
* Validation
* Commit
* Policy
* Prompt生成
* Worldline管理
* Runtime制御

# 5. 公開API

```lisp
extract-actions
run-ir-trial
divergence-profile
```

# 6. extract-actions

## 目的

IR Streamから

```
Phase = 1
```

のみ抽出する。

## シグネチャ

```lisp
(extract-actions ir-stream)
```

入力

```
Vector<IR>
```

出力

```
List<IR>
```

## アルゴリズム

### Step1

IR位置順にソート

```lisp
(sort
 (copy-seq ir-stream)
 #'<
 :key #'ir-pos)
```

元データは変更されない。

### Step2

Phase抽出

```
phase == 1
```

のみ採用。

```
IR

↓

Action IR
```

となる。

## 時間計算量

```
Sort

O(N log N)
```

抽出

```
O(N)
```

合計

```
O(N log N)
```

# 7. run-ir-trial

## 目的

1回の推論を実行し、

Phase-1 IR列を取得する。

## シグネチャ

```lisp
(run-ir-trial prompt)
```

入力

```
Prompt
```

出力

```
Vector<IR>
```

## 処理手順

### Step1

IR Stream初期化

```lisp
(clear-ir-stream)
```

### Step2

LLM実行

```lisp
(llama-run
 *model*
 *ctx*
 prompt)
```

IR CallbackによりIR Streamが蓄積される。

### Step3

Action抽出

```
extract-actions
```

### Step4

Vector化

```lisp
(coerce
 ...
 'vector)
```

返却。

## データフロー

```
Prompt

↓

LLM

↓

IR Callback

↓

IR Stream

↓

extract-actions

↓

Vector<IR>
```

# 8. divergence-profile

## 目的

同一Promptを複数回実行し、

各Token位置ごとの一致率を測定する。

## シグネチャ

```lisp
(divergence-profile prompt n-runs)
```

入力

| 項目     | 型       |
| ------ | ------- |
| prompt | String  |
| n-runs | Integer |

出力

```
List<Profile>
```

# 9. アルゴリズム

## Step1

複数回推論

```lisp
(loop repeat n-runs
 collect
 (run-ir-trial prompt))
```

結果

```
Run1

Run2

Run3

...
```

## Step2

共通長決定

```lisp
(apply #'min
       (mapcar #'length runs))
```

最短系列を採用する。

理由

途中終了した系列を安全に比較するため。

## Step3

各Step解析

```
Step0

Step1

Step2

...
```

について

各Runから

```
Token
```

を取得。

### Token取得

```lisp
(ir-token
 (aref seq step))
```

### 全一致判定

```lisp
(apply #'=
 tokens)
```

結果

```
T

または

NIL
```

### 一致率

```lisp
(count first-token tokens)

/

(length tokens)
```

で算出。

例

```
5 Runs

A
A
A
B
A

↓

4 / 5

↓

0.8
```

# 10. 出力形式

各Stepについて

```lisp
(:step
 step

 :all-same
 boolean

 :p-same
 probability)
```

例

```lisp
(:step 12
 :all-same NIL
 :p-same 0.6)
```

# 11. Divergence指標

現在計測される指標

| 項目       | 意味         |
| -------- | ---------- |
| step     | Token位置    |
| all-same | 全系列一致      |
| p-same   | 最多Token一致率 |

# 12. 決定性

同一Run集合なら

```
Profile
```

は必ず一致する。

解析中に乱数は使用しない。

# 13. 不変条件

解析は

```
IR

↓

Statistics
```

のみ生成する。

変更しないもの

* Runtime
* Kernel
* Candidate
* Canonical
* Prompt

# 14. 時間計算量

Run数

```
R
```

平均系列長

```
L
```

とすると

Run生成

```
O(R × Decode)
```

解析

```
O(R × L)
```

メモリ

```
O(R × L)
```

# 15. エラー処理

本モジュールでは明示的な例外処理は行わない。

前提条件

* `llama-run` が正常終了する
* `IR Callback` がIRを生成する
* `*model*` および `*ctx*` が有効

これらが満たされない場合の動作は下位モジュールに委譲される。

# 16. 設計原則

## Observation Only

解析のみを行い、Runtimeへ影響を与えない。

## Deterministic Analysis

同一IR集合からは必ず同一統計が得られる。

## Lossless Observation

IRを加工せず、そのまま解析対象とする。

## Runtime Isolation

解析結果はKernel・Canonical・推論制御へフィードバックされない。

# 17. 将来拡張

本実装は最小限の一致率解析を提供するが、Phase G 以降では以下の統計量へ拡張可能である。

* Shannon Entropy による分岐度評価
* Token Frequency Distribution
* Divergence Point Detection（初回分岐位置）
* Jensen–Shannon Divergence
* KL Divergence
* Levenshtein Distance
* Prefix Agreement Ratio
* Worldline Branch Probability
* Phase別（Prefill / Decode / Tool）解析
* 可視化（ヒートマップ・系列グラフ）

# 18. R1アーキテクチャにおける位置付け

```
                LLM Backend
                     │
                     ▼
              Physical Events
                     │
                     ▼
               IR Callback
                     │
                     ▼
                IR Stream
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
   Phase E Translation     IR Divergence
      (IR → DSL)             Analysis
         │                       │
         ▼                       ▼
     Candidate             Statistics
         │
         ▼
   Validation / Kernel
```

`ir-divergence` は **観測データの解析専用モジュール**として位置付けられ、Chron-LLM の決定論的 Runtime とは独立した研究・評価・デバッグ基盤を提供する。
