# Chron-LLM R0 Runtime

# Chat Runtime Specification v1.0

**Status:** Frozen Reference Specification

**Layer:** R0 Chat Runtime

**Package:** `chronos-r0.chat`

---

# 1. 概要

本モジュールは **Chron-LLM R0** のチャット実行ランタイムを実装する。

責務は以下に限定される。

* Session管理
* History更新
* Prompt生成
* LLM呼び出し
* Assistant応答登録
* Trace記録
* CLIチャットループ

R0は最も単純な逐次チャットランタイムであり、World・Kernel・Validation等は存在しない。

---

# 2. アーキテクチャ上の位置

```
User Input
     │
     ▼
start-chat
     │
     ▼
chat()
     │
     ├── History
     ├── Prompt Projection
     ├── llama-run
     ├── History Update
     └── Trace Logging
     │
     ▼
Console Output
```

---

# 3. 依存モジュール

本モジュールは以下のサブシステムを統合する。

| モジュール                | 役割        |
| -------------------- | --------- |
| `chronos-r0.history` | 会話履歴管理    |
| `chronos-r0.prompt`  | Prompt生成  |
| `chronos-r0.llama`   | LLMバックエンド |
| `chronos-r0.trace`   | 実行トレース    |

本モジュール自身は Prompt や History の内部実装を持たない。

---

# 4. Export API

公開API

```
session
session-model
session-history

make-new-session

chat

start-chat
```

---

# 5. Session

## 概要

Runtime全体の状態を保持する最小構造体。

```
Session
 ├── Model
 └── History
```

---

## 構造

| フィールド   | 内容       |
| ------- | -------- |
| model   | LLMモデル参照 |
| history | 会話履歴     |

---

## 特徴

Session自身は

* Prompt
* Trace
* Runtime状態

を保持しない。

---

# 6. make-new-session

## 目的

新規チャットセッション生成。

---

## 入力

```
:model
```

任意。

---

## 処理

```
Session
    model

History
    make-history()
```

を生成する。

---

## 出力

```
session
```

---

# 7. extract-generation

## 役割

LLM出力の抽出関数。

現状実装

```
identity
```

である。

```
raw

↓

raw
```

を返す。

---

## 将来の拡張点

将来的には

* ChatML除去
* EOS除去
* Tool Call抽出
* JSON抽出

などをここへ実装できる。

---

# 8. make-assistant-event

## 目的

LLM生成結果をHistory Eventへ変換する。

入力

```
text
```

↓

生成

```
History Event
    role = assistant
    content = text
```

---

# 9. chat()

## 概要

R0の中心処理。

1回の対話を処理する。

---

## 入力

```
Session

User Text
```

---

## 処理フロー

### Step1

History取得

```
history
```

---

### Step2

History Snapshot取得

```
history-before
```

Trace用。

---

### Step3

User Event追加

```
History

↓

append(user)
```

---

### Step4

Prompt生成

```
Prompt Projection
```

実行

```
project-to-prompt(history)
```

---

### Step5

統計取得

取得される値

```
Prompt Length

History Size
```

---

### Step6

LLM呼び出し

```
raw

=

llama-run(prompt)
```

---

### Step7

生成結果抽出

```
parsed

=

extract-generation(raw)
```

---

### Step8

Assistant Event生成

```
assistant

↓

History Append
```

---

### Step9

Trace生成

Traceには以下が記録される。

| 項目                  | 内容         |
| ------------------- | ---------- |
| user-text           | 入力         |
| prompt              | Prompt全文   |
| raw                 | LLM生出力     |
| parsed              | パース後       |
| history-before      | 更新前History |
| history-after       | 更新後History |
| prompt-length       | Prompt長    |
| response-length     | 応答長        |
| history-size-before | 更新前履歴数     |
| history-size-after  | 更新後履歴数     |

---

### Step10

Session返却

```
session
```

を返す。

---

# 10. データフロー

```
User Text

      │

      ▼

History Append

      │

      ▼

Prompt Projection

      │

      ▼

LLM

      │

      ▼

Assistant Text

      │

      ▼

History Append

      │

      ▼

Trace
```

---

# 11. start-chat()

## 概要

CLIチャットループ。

---

## 初期化

```
make-new-session()
```

を呼ぶ。

---

## メインループ

繰り返し

```
You>
```

を表示。

---

### 入力取得

```
read-line
```

---

### 終了条件

```
EOF

または

:exit
```

---

### チャット実行

```
chat(session,input)
```

---

### Assistant検索

Historyから

```
role == assistant
```

である最後のイベントを検索する。

探索方向

```
末尾

↓

先頭
```

---

### 出力

```
AI>

assistant-content
```

を表示する。

---

# 12. Runtime状態遷移

```
Session

 │

 ▼

Append User

 │

 ▼

Prompt

 │

 ▼

LLM

 │

 ▼

Assistant

 │

 ▼

Append History

 │

 ▼

Trace

 │

 ▼

Return Session
```

---

# 13. Trace Contract

Traceは必ず

```
History Before

History After
```

を保持する。

これにより

* Prompt生成
* 履歴変化
* 応答内容

を完全に再現できる。

---

# 14. 不変条件（Invariants）

* `Session` は `model` と `history` のみを保持する。
* `chat()` は必ず User Event を履歴へ追加してから Prompt を生成する。
* Prompt は常に最新の History を入力として生成される。
* LLM 呼び出しは `chronos-r0.llama:llama-run` に委譲される。
* Assistant 応答は必ず History に追加される。
* Trace は更新前後の History をスナップショットとして保持する。
* `chat()` は Session を破棄せず、更新後の Session を返す。
* `start-chat()` は単一 Session を維持したまま対話を継続する。
* 終了条件は EOF (`nil`) または `:exit` のみである。
* CLI 表示は History 内の最後の `:assistant` イベントのみを出力する。

---

# 15. 設計上の特徴

## 逐次実行モデル

R0 は単純な **User → LLM → Assistant** の逐次対話モデルを採用し、非同期処理や並列生成は扱わない。

## 明確な責務分離

* **History**：会話履歴の管理
* **Prompt**：履歴からのプロンプト投影
* **LLM**：推論実行
* **Trace**：実行記録
* **Chat Runtime**：各コンポーネントのオーケストレーション

## 将来拡張性

`extract-generation` が独立しているため、将来的に ChatML の除去、JSON/Tool Call の抽出、特殊トークン処理などを追加しても、`chat()` の制御フローを変更せずに拡張できる。これは R0 をシンプルなリファレンス実装として保ちながら、R1 以降の高度なランタイムへの移行を容易にする設計となっている。
