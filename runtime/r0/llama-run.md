# Chron-LLM R0 Runtime

## Llama Backend Interface Specification v1.0

**Status**

* Stable
* R0 Reference Runtime

**Layer**

* Backend Adapter
* Physical Runtime Interface

**Scope**

```
Prompt
    ↓
llama.cpp CLI
    ↓
Raw Text
```

---

# 1. 目的

本モジュールは、Chron-R0 RuntimeからLLMを利用するための最小バックエンドである。

R0では

```
History
    ↓
Prompt Projection
    ↓
Backend
    ↓
Generated Text
```

のみを担当し、

* Validation
* Candidate
* Kernel
* World

などは一切扱わない。

---

# 2. パッケージ

```
chronos-r0.llama
```

Export

```
llama-run
```

公開APIはこの1関数のみである。

---

# 3. アーキテクチャ

```
History

↓

Prompt

↓

llama-run()

↓

llama.cpp

↓

stdout

↓

String
```

CLIをBackendとして利用する非常に単純なAdapterとなる。

---

# 4. Public API

```
(llama-run prompt)
```

## 引数

```
prompt
```

型

```
string
```

Prompt Projection層が生成した完全なプロンプト。

---

## 戻り値

```
string
```

llama.cpp が標準出力へ生成した全文。

整形は行わない。

---

# 5. 実装方式

LLM実行には

```
uiop:run-program
```

を使用する。

```
(uiop:run-program ...)
```

同期実行であり、

呼び出し側は終了まで待機する。

---

# 6. llama.cpp 実行構成

実行ファイル

```
/home/junu/lisp-os/llama.cpp/build/bin/llama-completion
```

モデル

```
/home/junu/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf
```

実行オプション

```
--single-turn
```

単一ターン生成。

---

```
--n-predict 128
```

最大生成トークン数

```
128
```

---

```
--system-prompt
```

固定System Prompt

```
あなたは日本語で丁寧で簡潔に答えるアシスタントです。
```

---

```
-p prompt
```

Prompt Projection層が生成した全文を入力する。

---

# 7. 実行フロー

```
Prompt
      │
      ▼
llama-run
      │
      ▼
run-program
      │
      ▼
llama-completion
      │
      ▼
stdout
      │
      ▼
Common Lisp String
```

---

# 8. エラー処理

```
:error-output :string
```

stderrは取得される。

---

```
:ignore-error-status t
```

プロセス終了コードによる例外は送出しない。

つまり

```
Backend Failure
```

であっても

Lisp Runtimeは停止しない。

上位層が必要に応じて内容を解析する設計となっている。

---

# 9. 設計原則

## Backend Isolation

LLM固有仕様は本モジュールに閉じ込める。

R0 Runtimeは

```
String → String
```

という抽象インターフェースのみ利用する。

---

## Stateless

状態を保持しない。

保持するもの

なし

保持しないもの

* Session
* History
* Candidate
* Kernel State
* KV Cache

---

## Synchronous Execution

```
Prompt
```

↓

```
Blocking Execution
```

↓

```
Generated Text
```

逐次生成は扱わない。

---

# 10. R0での責務

担当

* Prompt送信
* CLI起動
* モデル指定
* System Prompt指定
* 生成結果取得
* stderr取得

担当外

* Prompt生成
* History管理
* Token Streaming
* Validation
* Retry
* Temperature制御
* Candidate生成
* Commit
* World管理
* Memory管理
* Graph管理

---

# 11. データフロー

```
History
      │
      ▼
Prompt Projection
      │
      ▼
Prompt String
      │
      ▼
llama-run
      │
      ▼
llama.cpp CLI
      │
      ▼
Raw Text
      │
      ▼
R0 Runtime
```

---

# 12. アーキテクチャ上の位置

```
┌────────────────────┐
│ History            │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Prompt Projection  │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ llama-run          │
│ Backend Adapter    │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ llama.cpp CLI      │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Generated Text     │
└────────────────────┘
```

---

# 13. 将来拡張

本APIはバックエンド非依存のインターフェースとして設計されており、`llama.cpp` 固有の実装を他の推論エンジンへ置き換えることが可能である。

置き換え候補例:

* llama.cpp Server
* llama.cpp C API
* Ollama
* vLLM
* OpenAI Compatible API
* LM Studio API

これらはすべて `llama-run(prompt) -> string` の契約を維持する限り、R0 Runtimeの他のモジュールを変更せずに差し替えられる。
