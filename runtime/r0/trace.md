# Chron-LLM R0 Specification

# Trace Layer (Execution Observation)

**Version**
: R0

**Status**
: Stable

**Layer**
: Runtime Trace / Observation Layer

**Package**

```lisp
chronos-r0.trace
```

---

# 1. 概要

Trace Layer は Chron-R0 の**実行観測層 (Observation Layer)** であり、チャット実行中に発生した各推論ステップを**完全なスナップショットとして記録**するためのモジュールである。

この層は Runtime の挙動を記録することのみを目的とし、Runtime の状態や履歴を変更しない。

---

# 2. 設計目的

R0では

```
User
 ↓
History
 ↓
Prompt
 ↓
LLM
 ↓
Response
```

という一連の実行を、

**完全に観測可能**

にすることが目的である。

Trace は

* デバッグ
* 再現実験
* Runtime解析
* Prompt解析

のためだけに存在する。

---

# 3. 責務

本モジュールが担当するもの

* Runtime実行記録
* Prompt保存
* Raw出力保存
* Parsed出力保存
* History前後状態保存
* Prompt長保存
* Response長保存
* Trace一覧保持
* Trace永続化

---

担当しないもの

* LLM実行
* Prompt生成
* History更新
* Validation
* Policy
* Commit
* Candidate生成
* Runtime制御

---

# 4. データモデル

## R0 Trace

```lisp
(defstruct r0-trace
  user-text
  prompt
  raw
  parsed
  history-before
  history-after
  prompt-length
  response-length
  history-size-before
  history-size-after)
```

---

## フィールド仕様

| フィールド               | 型       | 説明             |
| ------------------- | ------- | -------------- |
| user-text           | String  | ユーザー入力         |
| prompt              | String  | LLMへ送信したPrompt |
| raw                 | String  | LLMの生出力        |
| parsed              | String  | 抽出後の応答         |
| history-before      | History | 実行前履歴          |
| history-after       | History | 実行後履歴          |
| prompt-length       | Integer | Prompt文字数      |
| response-length     | Integer | 応答文字数          |
| history-size-before | Integer | 履歴件数（前）        |
| history-size-after  | Integer | 履歴件数（後）        |

---

# 5. Trace Storage

グローバルログ

```lisp
(defvar *trace-log*)
```

実体

```
Adjustable Vector
```

初期値

```
[]
```

---

## 性質

可変長

```
vector-push-extend
```

で追加される。

---

# 6. エントリポイント

## log-trace

```
(log-trace trace)
```

役割

Traceをログへ追加。

実装

```
Trace
    ↓
vector-push-extend
    ↓
*trace-log*
```

戻り値

```
trace
```

---

## save-trace-to-file

```
(save-trace-to-file path)
```

役割

現在保持しているTraceを

```
ファイル
```

へ保存する。

---

### 動作

まず

```
*trace-log*
```

を

```
List
```

へコピーする。

```
snapshot
```

を利用する理由は、

保存中にTraceが追加されても

出力対象が変化しないようにするためである。

---

### 出力形式

各Traceを

```
~S
```

で保存。

つまり

```
READ可能
```

なS式となる。

例

```lisp
#S(R0-TRACE
   ...)
```

---

### ファイルモード

```
append
```

既存内容は保持される。

---

# 7. dump-trace

```
(dump-trace)
```

役割

Traceを標準出力へ表示する。

表示形式

```
=== TRACE ===

#S(...)
```

---

# 8. スナップショット方式

保存時は

```
snapshot
```

を生成する。

```
*trace-log*
    ↓
coerce
    ↓
List
```

このため、

保存途中で

```
vector-push-extend
```

されても、

保存対象は変化しない。

---

# 9. データフロー

```
Runtime

↓

make-r0-trace

↓

log-trace

↓

*trace-log*

↓

save-trace-to-file
```

または

```
dump-trace
```

---

# 10. Runtimeとの関係

Traceは

```
Observer
```

である。

Runtime状態には影響しない。

```
Runtime

↓

Trace

↓

Nothing Returns
```

---

# 11. 不変条件

Trace追加によって

* History
* Session
* Prompt

は変更されない。

---

# 12. 計算量

## log-trace

```
O(1)
```

平均。

---

## save-trace-to-file

```
O(N)
```

N

Trace数。

---

## dump-trace

```
O(N)
```

---

# 13. メモリ使用量

Traceは

```
永続保持
```

される。

よって

```
O(N)
```

増加する。

---

# 14. 永続化仕様

保存形式

```
S-expression
```

読み戻し可能。

Common Lisp標準Readerで再構築できる。

---

# 15. エラー処理

ファイル保存時は

```
with-open-file
```

へ委譲。

ファイルシステムエラーは

Lisp標準例外となる。

---

# 16. モジュール依存

依存

```
chronos-r0.history
```

ただし直接Historyを書き換えない。

保存のみ。

---

# 17. レイヤ位置

```
History

↓

Prompt

↓

LLM

↓

Response

↓

Trace
```

TraceはRuntimeを横断する

**観測レイヤ**

として存在する。

---

# 18. 設計原則

## Observation Only

Runtimeへ影響を与えない。

---

## Immutable Snapshot

History前後を保存する。

実行後に変更されても、

Traceは当時の状態を保持する。

---

## Readable Serialization

保存形式は

```
~S
```

を使用し、

Lisp Readerで再構築可能。

---

## Side-effect Isolation

Trace保存は

```
Snapshot
```

を利用し、

書き込み中のRuntime変更の影響を受けない。

---

# 19. R0アーキテクチャにおける位置付け

```
          User
            │
            ▼
        History Layer
            │
            ▼
      Prompt Projection
            │
            ▼
        LLM Runtime
            │
            ▼
      Response Parsing
            │
            ▼
     Runtime Trace Layer
            │
            ▼
     Trace Log / File Export
```

Trace Layer は **R0 Runtime の観測・解析基盤**であり、すべての実行ステップを再現可能な形で記録する。これは将来の **R1 Observation Layer（IR生成）** や **Phase E Translation Layer** に接続される際の基礎となる実装である。
