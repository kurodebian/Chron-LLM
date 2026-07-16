# IR FFI Bridge Specification v1.0

## 1. 概要

### 1.1 目的

`ir-ffi` パッケージは、Common Lisp 側の IR (Intermediate Representation) Callback 実装と、C/C++ 側ランタイム間の接続を提供する FFI (Foreign Function Interface) ブリッジ層である。

本モジュールの責務は以下に限定される。

* C側で保持される callback 登録APIへの接続
* Lisp callback function pointer の生成
* C側への callback 登録

本モジュール自身は以下を担当しない。

* IR生成
* IR解析
* 推論制御
* Proposal生成
* Commit
* History管理
* Runtime状態管理

---

# 2. Architecture Position

## 2.1 Layer Position

```
+-----------------------------+
|        LLM Backend          |
|      llama.cpp / C++        |
+-------------+---------------+
              |
              |
        register_ir_callback
              |
              ▼
+-----------------------------+
|          ir-ffi             |
|       FFI Bridge Layer      |
+-------------+---------------+
              |
              |
        Lisp Callback
              |
              ▼
+-----------------------------+
|        ir-callback          |
|     IR Event Receiver       |
+-------------+---------------+
              |
              ▼
+-----------------------------+
|            IR               |
|    Intermediate Event       |
+-----------------------------+
```

---

# 3. Package Specification

## 3.1 Package Definition

```lisp
(defpackage :ir-ffi
  (:use :cl
        :cffi
        :ir-callback)
  (:export
   :init-ir-bridge))
```

---

## 3.2 Package Name

```
ir-ffi
```

役割:

> IR Callback を外部ランタイムへ公開するためのFFI境界。

---

# 4. Dependency Specification

## 4.1 Used Packages

| Package       | Role                       |
| ------------- | -------------------------- |
| `CL`          | Common Lisp標準機能            |
| `CFFI`        | Foreign Function Interface |
| `IR-CALLBACK` | Lisp側callback定義            |

---

## 4.2 Dependency Graph

```
ir-ffi

 ├── cffi
 │
 └── ir-callback
```

---

# 5. Foreign Function Interface Definition

## 5.1 C Function Binding

```lisp
(cffi:defcfun
 ("register_ir_callback" register-ir-callback)
 :void
 (cb :pointer))
```

---

## 5.2 External Symbol

C側API:

```c
void register_ir_callback(void *cb);
```

想定ABI:

| 項目                 | 値                |
| ------------------ | ---------------- |
| Calling Convention | C ABI            |
| Return             | void             |
| Argument           | callback pointer |
| Ownership          | C側保持             |

---

# 6. register-ir-callback

## 6.1 Purpose

Cランタイムへ Lisp callback pointer を登録する。

---

## 6.2 Signature

Lisp:

```lisp
(register-ir-callback cb)
```

---

## 6.3 Arguments

### cb

型:

```
:pointer
```

意味:

```
Cから呼び出可能な関数ポインタ
```

---

## 6.4 Return

```
void
```

Lisp:

```
NIL
```

相当。

---

# 7. Callback Flow

## 7.1 Initialization Sequence

```
Application Start

      |
      v

init-ir-bridge

      |
      v

cffi:callback

      |
      v

Generate C Function Pointer

      |
      v

register_ir_callback

      |
      v

C Runtime Stores Pointer

      |
      v

IR Events Begin
```

---

# 8. init-ir-bridge Specification

## 8.1 Function

```lisp
(defun init-ir-bridge ()
  (register-ir-callback
    (cffi:callback ir-callback)))
```

---

## 8.2 Responsibility

`init-ir-bridge` はIR通信路の初期化エントリポイント。

処理:

1. Lisp callbackをC ABI形式へ変換
2. callback pointer生成
3. C runtimeへ登録

---

# 9. Detailed Execution

## Step 1

呼び出し:

```lisp
(cffi:callback ir-callback)
```

生成:

```
Lisp Function

↓

Foreign Callable Pointer
```

---

## Step 2

登録:

```lisp
(register-ir-callback pointer)
```

結果:

```
C Runtime

callback_address =
generated_pointer
```

---

# 10. Runtime Contract

## 10.1 Callback Lifetime

重要:

`cffi:callback` が生成したcallback pointerは、C側が保持する間、有効でなければならない。

必要条件:

```
callback object
       |
       |
       v
GC Root保持
```

---

## 10.2 GC Safety

現在コード:

```lisp
(cffi:callback ir-callback)
```

を直接渡している。

注意点:

C側が後からcallbackを呼ぶ場合、GCによる回収リスクがある。

推奨:

```lisp
(defvar *ir-callback-pointer*
  nil)

(defun init-ir-bridge ()
  (setf *ir-callback-pointer*
        (cffi:callback ir-callback))

  (register-ir-callback
    *ir-callback-pointer*))
```

---

# 11. ABI Contract

## 11.1 C Side Requirement

C側 callback signature は Lisp callback定義と一致する必要がある。

例:

C:

```c
typedef void (*ir_callback_t)(void*);
```

ならLisp:

```lisp
(cffi:defcallback ir-callback
    :void
    ((ptr :pointer)))
```

が必要。

---

# 12. Error Conditions

## 12.1 Missing C Symbol

状態:

```
register_ir_callback not found
```

原因:

* shared library未ロード
* symbol export不足
* ABI mismatch

---

## 12.2 Callback Signature Mismatch

状態:

```
C crash
```

原因:

```
C callback ABI
!=
Lisp callback ABI
```

---

## 12.3 Callback Lifetime Failure

状態:

```
random callback failure
segmentation fault
```

原因:

```
callback pointer GC invalidation
```

---

# 13. Current Responsibility Boundary

## Included

| 機能                    | 状態 |
| --------------------- | -- |
| C function binding    | ✓  |
| callback registration | ✓  |
| FFI initialization    | ✓  |

---

## Excluded

| 機能     | 担当          |
| ------ | ----------- |
| IR生成   | ir layer    |
| IR保存   | history/WAL |
| IR解析   | analysis    |
| Commit | kernel      |
| Policy | runtime     |

---

# 14. Chron-LLM Architecture Mapping

本モジュールは以下の位置に存在する。

```
             LLM
              |
              |
        Observation
              |
              v

        C Runtime
              |
              |
       IR Callback ABI
              |
              v

        ir-ffi
              |
              v

        ir-callback
              |
              v

        Kernel Proposal Pipeline
              |
              v

        Review / Commit / History
```

---

# 15. Design Classification

| 項目          | 分類          |
| ----------- | ----------- |
| Layer       | FFI Adapter |
| State       | 無し          |
| Determinism | 保持          |
| Persistence | 無し          |
| Authority   | 無し          |
| Mutation    | 無し          |

---

# 16. Formal Specification

```
IR-FFI MUST:

1. expose C callback registration
2. convert Lisp callback into C callable pointer
3. register callback exactly once during initialization
4. preserve callback lifetime while C runtime uses it


IR-FFI MUST NOT:

1. generate IR
2. modify History
3. perform Commit
4. contain Runtime policy
5. own inference state
```

---

# 17. Review Summary

## Current Implementation Status

評価:

**Minimal FFI Bridgeとして成立**

ただし本番Runtime投入前に以下の追加が必要。

Priority:

### P0

Callback lifetime管理

```
global callback pointer retention
```

---

### P1

ABI固定化

```
IR Callback ABI v1
```

定義:

* argument type
* ownership
* threading
* reentrancy

---

### P2

Error handling

追加:

```
register success flag
callback version
ABI compatibility check
```

---

## Final Assessment

このコードは Chron-LLM の設計上では、

> 「非決定的LLM出力をKernel観測可能なIRイベントへ変換する最初の境界層」

に相当する。

現段階では **IR Observation Channel の最小実装**であり、Commit権限や状態保持を持たないため、Chron-OSの決定論的Kernel境界設計と整合している。
