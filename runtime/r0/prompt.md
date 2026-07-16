# Chron-LLM R0 Specification

## Prompt Projection Layer

Version
: R0

Status
: Stable

Layer
: Runtime Prompt Projection

Package

```
chronos-r0.prompt
```

---

# 1. 目的

このモジュールは

```
History
    ↓
Prompt
```

への唯一の変換器である。

Chron-R0では

```
History = Canonical Session
```

とみなし、

LLMへ入力するPromptを完全決定論で生成する。

---

# 2. 責務

このモジュールが行うこと

* Historyの読み出し
* Prompt構築
* ChatML形式への射影
* Roleの変換
* Assistant開始位置の生成

---

行わないこと

* LLM実行
* 履歴更新
* Validation
* Candidate生成
* Commit
* Policy
* Retry
* Worldline管理

---

# 3. 入力

```
History
```

構造

```
history
 ├ events[]
      history-event
          role
          content
```

Role例

```
:user
:assistant
:system
```

---

# 4. 出力

```
String
```

LLMへ渡す完成Prompt。

---

# 5. エントリポイント

```
project-to-prompt(history)
```

戻り値

```
String
```

純粋関数である。

Historyを書き換えない。

---

# 6. Prompt生成アルゴリズム

## Step1

History取得

```
events
←
history-events(history)
```

---

## Step2

文字列生成開始

```
with-output-to-string
```

使用。

副作用無し。

---

## Step3

BOS追加

```
<|begin_of_text|>
```

---

## Step4

System Header追加

```
<|start_header_id|>system<|end_header_id|>
```

---

## Step5

固定System Prompt

```
あなたは日本語で丁寧に答えるアシスタントです。
```

R0では固定値。

---

## Step6

履歴列挙

```
loop
for e across events
```

各イベントについて

```
Role

↓

Header

↓

Content
```

を追加する。

---

生成形式

```
<|start_header_id|>
ROLE
<|end_header_id|>

CONTENT
```

例

```
<|start_header_id|>user<|end_header_id|>
こんにちは

<|start_header_id|>assistant<|end_header_id|>
こんにちは。
```

Role名は

```
~(~A~)
```

により小文字化される。

---

## Step7

最後にAssistant Header

```
<|start_header_id|>assistant<|end_header_id|>
```

のみ追加。

ここから先をLLMが生成する。

---

# 7. Promptフォーマット

最終形

```
<|begin_of_text|>

<|start_header_id|>system<|end_header_id|>

System Prompt

<|start_header_id|>user<|end_header_id|>

・・・

<|start_header_id|>assistant<|end_header_id|>

・・・

<|start_header_id|>assistant<|end_header_id|>
```

---

# 8. ChatML互換性

利用している特殊トークン

```
<|begin_of_text|>

<|start_header_id|>

<|end_header_id|>
```

Llama3系Chat Template準拠。

---

# 9. データフロー

```
History

↓

history-events

↓

Loop

↓

Role Header

↓

Content

↓

Prompt String
```

---

# 10. 決定性

同一Historyなら

```
Prompt
```

は必ず一致する。

つまり

```
Prompt(H)

=

Prompt(H)
```

乱数

無し。

時刻

無し。

環境依存

無し。

---

# 11. 不変条件

Historyは変更しない。

```
Input Immutable
```

Promptのみ生成。

```
Output Only
```

---

# 12. 時間計算量

イベント数

```
N
```

文字列長

```
L
```

計算量

```
O(N+L)
```

---

# 13. メモリ使用量

生成文字列のみ。

追加メモリ

```
O(L)
```

---

# 14. エラー処理

このモジュール自身では

```
error
```

を発生させない。

History構造が正しい前提。

---

# 15. モジュール依存

依存

```
chronos-r0.history
```

利用API

```
history-events

history-event-role

history-event-content
```

LLM依存

無し。

---

# 16. レイヤ境界

入力

```
History
```

↓

このモジュール

↓

```
Prompt
```

↓

```
chronos-r0.llama
```

---

# 17. 設計原則

## Projection Only

意味解析しない。

---

Validationしない。

---

Historyを書き換えない。

---

Promptのみ生成する。

---

# 18. R0における位置付け

```
History

↓

Prompt Projection
      ← 本モジュール

↓

LLM Runtime

↓

Raw Text
```

---

# 19. 将来拡張点

R1以降では固定System Promptを設定から取得する構成へ変更可能。

想定される拡張例:

* `config` によるシステムプロンプト切り替え
* 要約 (`summary`) の挿入
* 長期メモリ (`memory`) セクションの追加
* コンテキスト長に応じた履歴トリミング
* モデルごとのテンプレート切り替え（Llama 3系、Qwen系、Gemma系など）

これらは **Projection Policy** の拡張であり、本モジュールの「History→Promptを決定論的に射影する」という責務自体は維持される。
