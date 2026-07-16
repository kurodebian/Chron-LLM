# Chron-LLM R1 Specification

# IR Callback Layer (Physical → IR Bridge)

**Version**
: R1

**Status**
: Stable Baseline

**Layer**
: Physical Observation Bridge

**Package**

```lisp
ir-callback
```

---

# 1. 概要

本モジュールは、LLMバックエンド（C/C++）から発生する**物理イベント（Physical Event）**を、Chron-LLM の内部観測形式である **IR (Intermediate Representation)** に変換し、IR Streamへ格納するためのブリッジ層である。

アーキテクチャ上では **Physical Layer と Observation Layer の境界**を構成する。

```
llama.cpp

    │
    ▼

C Callback

    │
    ▼

IR Callback
    │
    ▼

IR Object
    │
    ▼

IR Stream
```

---

# 2. 設計目的

Chron-LLMでは、LLM内部状態を直接操作しない。

代わりに、

```
Physical Event

↓

IR

↓

Kernel
```

という観測中心アーキテクチャを採用する。

本モジュールはその最初の入口となる。

---

# 3. 責務

本モジュールが担当するもの

* C Callback受信
* Physical Event取得
* IR生成
* IR Streamへの追加

---

担当しないもの

* Validation
* Candidate生成
* Commit
* Policy
* Kernel評価
* 世界線操作
* Prompt生成
* 推論制御

---

# 4. 依存モジュール

```
ir
```

利用

* `make-ir`

---

```
ir-stream
```

利用

* `push-ir`

---

```
cffi
```

利用

* `defcallback`

---

# 5. 公開API

```lisp
ir-callback
```

エクスポートされる唯一のシンボルである。

---

# 6. Callback仕様

```lisp
(cffi:defcallback ir-callback ...)
```

C側から呼び出される。

---

## シグネチャ

```text
void callback(
    void* ctx_id,
    int pos,
    int token,
    float score,
    int phase
)
```

---

### 引数

| 引数     | 型       | 意味           |
| ------ | ------- | ------------ |
| ctx-id | Pointer | LLMコンテキスト識別子 |
| pos    | Integer | トークン位置       |
| token  | Integer | 生成トークンID     |
| score  | Float   | 生成スコア        |
| phase  | Integer | 生成フェーズ       |

---

### 戻り値

```
void
```

戻り値は存在しない。

---

# 7. IR生成

Callback受信後、

```
make-ir
```

を呼び出す。

生成されるIR

```lisp
(make-ir
 :ctx-id ctx-id
 :pos pos
 :phase phase
 :token token
 :score score)
```

---

## フィールド対応

| Physical Event | IR     |
| -------------- | ------ |
| ctx-id         | ctx-id |
| pos            | pos    |
| phase          | phase  |
| token          | token  |
| score          | score  |

情報はそのまま保持される。

---

# 8. IR Stream登録

生成後、

```
(push-ir ir)
```

を実行する。

結果

```
IR

↓

IR Stream
```

追加される。

---

# 9. データフロー

```
C Runtime

↓

Callback

↓

make-ir

↓

push-ir

↓

IR Stream
```

---

# 10. データ変換

本モジュールは

```
Physical Event

↓

IR
```

への

**1対1変換**

のみを行う。

変換規則

```
ctx-id
↓

ctx-id

pos

↓

pos

token

↓

token

score

↓

score

phase

↓

phase
```

加工は一切行わない。

---

# 11. 決定性

同一入力なら

```
IR
```

は必ず一致する。

```
Callback(A)

↓

IR(A)
```

乱数

なし。

時刻

なし。

状態依存

なし。

---

# 12. 不変条件

Callbackは

* Runtime状態を変更しない
* Kernelを変更しない
* Canonicalを変更しない

変更されるのは

```
IR Stream
```

のみである。

---

# 13. エラー処理

本コードでは

例外処理は存在しない。

前提条件

* `make-ir` が成功する
* `push-ir` が成功する

失敗時の挙動は依存モジュールへ委譲される。

---

# 14. 性能

処理内容

```
IR生成

+

Vector追加
```

時間計算量

```
O(1)
```

メモリ

```
O(1)
```

（IR Streamの増加を除く）

---

# 15. スレッド安全性

本実装では同期処理は行われていない。

そのため、

```
push-ir
```

がスレッドセーフであることを前提としている。

複数スレッドから同時にコールバックされる環境では、IR Stream 側で排他制御またはロックフリー構造を提供する必要がある。

---

# 16. アーキテクチャ上の位置

```
LLM Backend

        │

        ▼

Physical Event

        │

        ▼

IR Callback
（本モジュール）

        │

        ▼

IR Stream

        │

        ▼

Phase E

        │

        ▼

Candidate

        │

        ▼

Validation

        │

        ▼

Kernel
```

---

# 17. 設計原則

## Physical Boundary

物理層から論理層への唯一の入口となる。

---

## Observation Only

観測のみを行う。

意思決定は一切行わない。

---

## Lossless Translation

受信した全フィールドを保持し、情報を欠落・加工しない。

---

## Deterministic

同一入力は必ず同一IRへ変換される。

---

## Side-effect Isolation

副作用は **IR Streamへの追加のみ** とし、Kernel・Canonical・Runtime状態には影響を与えない。

---

# 18. Phase Eとの関係

本モジュールは **R1 Observation Layer** の終端であり、Phase E Translation Layer の入力を生成する。

```
Physical Event
        │
        ▼
IR Callback
        │
        ▼
IR Stream
        │
        ▼
Phase E
(IR → Causal DSL)
```

この設計により、**物理イベントとKernel評価を完全に分離**し、Chron-LLM の「観測 → 正規化 → 因果評価 → 権威状態更新」という決定論的ランタイムアーキテクチャを支える基盤となる。
