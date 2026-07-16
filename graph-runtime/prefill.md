# Prefill State Construction Specification v1.0

## Chron-R2.0-A Prompt Projection / LLM Prefill Boundary

---

# 1. Overview

## 1.1 Purpose

`prefill-state`, `canonical-prompt`, `build-prefill-state` は Chron-R2.0-A における **LLM Prefill 用状態生成層**を定義する。

責務:

* Graph/History から LLM 入力 Context を射影
* Deterministic Prompt を生成
* Prompt Hash を取得
* Prefill State として固定化

する。

---

# 2. Architectural Position

```text
                 WAL / History

                       |
                       v

              Causal Graph

                       |
                       v

             project-context

                       |
                       v

              Context Nodes

                       |
                       v

           canonical-prompt

                       |
                       v

              Prompt String

                       |
                       v

              SHA256 Hash

                       |
                       v

            prefill-state

                       |
                       v

              LLM Prefill
```

---

# 3. Responsibility Boundary

## 3.1 Responsible

| Component           | Responsibility              |
| ------------------- | --------------------------- |
| prefill-state       | Prefill input identity      |
| canonical-prompt    | Deterministic serialization |
| build-prefill-state | Context → Prompt → Hash     |

---

## 3.2 Non-Responsible

| Function         | Owner             |
| ---------------- | ----------------- |
| Tokenization     | LLM Backend       |
| KV Cache         | llama.cpp/runtime |
| Generation       | LLM               |
| Commit           | Kernel            |
| History mutation | WAL               |

---

# 4. Design Principle

Chron-OS / Chron-LLM architecture:

```text
LLM = Non Deterministic

Kernel = Deterministic
```

の境界として、

Prefill State は:

```text
Context Projection
        |
        v
Canonical Prompt
        |
        v
Stable Identity
```

を提供する。

---

# 5. prefill-state Specification

## 5.1 Definition

```lisp
(defstruct
    (prefill-state
      (:constructor make-prefill-state
          (context target-id hash)))

  context
  target-id
  hash)
```

---

# 6. Logical Model

```text
PrefillState =
{
    context,
    target-id,
    prompt-hash
}
```

---

# 7. Field Specification

---

## 7.1 context

Definition:

```lisp
(context nil
 :type list
 :read-only t)
```

---

Purpose:

LLM に提示する context projection。

内容:

```text
Context Nodes
```

---

例:

```text
[
 Node-A
 Node-B
 Node-C
]
```

---

重要:

これは:

```text
Knowledge
```

ではない。

あくまで:

```text
Prompt Projection
```

である。

---

## 7.2 target-id

Definition:

```lisp
(target-id nil
 :read-only t)
```

---

Purpose:

この Prefill State が生成された対象 node。

例:

```text
target = current task node
```

---

用途:

* replay
* trace
* debugging
* prompt identity

---

## 7.3 hash

Definition:

```lisp
(hash ""
 :type string
 :read-only t)
```

---

Purpose:

Canonical Prompt の content hash。

生成:

```text
prompt

↓

SHA256

↓

hash
```

---

意味:

Prompt identity。

---

# 8. canonical-prompt Specification

## 8.1 Definition

```lisp
(defun canonical-prompt (context)
```

---

# 9. Purpose

Context Node 列を deterministic string に変換する。

---

# 10. Serialization Format

生成形式:

```lisp
(prompt
 (:node NODE-ID
  :type NODE-TYPE
  :content CONTENT
  :feedback FEEDBACK))
```

---

Example:

Context:

```text
Node:
 id = :n1
 type = :question
 content = "hello"
 feedback = nil
```

---

Output:

```lisp
(prompt
 (:node :n1
  :type :question
  :content "hello"
  :feedback nil))
```

---

# 11. Serialization Rules

## Rule 1

Node order is preserved.

Input:

```text
[A B C]
```

Output:

```text
A

B

C
```

---

## Rule 2

No semantic transformation.

保持:

```text
content
feedback
type
id
```

---

## Rule 3

Same context produces same prompt.

---

# 12. canonical-prompt Algorithm

```lisp
(with-output-to-string (stream)

  for each node:

      emit fixed format

)
```

---

Pseudo:

```text
Context

 ↓

Node iteration

 ↓

Format serialization

 ↓

String
```

---

# 13. build-prefill-state Specification

## 13.1 Definition

```lisp
(defun build-prefill-state
    (graph
     store
     target-id
     &key
       (include-evaluations nil)
       (prompt-builder #'canonical-prompt))
```

---

# 14. Purpose

Graph Context から LLM Prefill 用 immutable state を生成する。

---

# 15. Input

---

## graph

Causal/Runtime Graph。

---

## store

Context source。

想定:

```text
History Store
```

---

## target-id

対象 node。

---

## include-evaluations

Optional:

```lisp
nil
```

default。

---

意味:

Evaluation metadata を context に含めるか。

---

## prompt-builder

Default:

```lisp
canonical-prompt
```

---

拡張可能:

```lisp
custom prompt projection
```

---

# 16. Execution Flow

```text
graph
 |
 v

project-context

 |
 v

context

 |
 v

prompt-builder

 |
 v

prompt

 |
 v

sha256-string

 |
 v

prefill-state
```

---

# 17. Step Details

## Step 1

Context Projection:

```lisp
(project-context
 graph
 store
 target-id)
```

---

Output:

```text
Context List
```

---

# Step 2

Prompt Generation:

```lisp
(funcall prompt-builder context)
```

---

Expected:

```text
string
```

---

# Step 3

Validation:

```lisp
(unless (stringp prompt)
  error)
```

---

Contract:

Prompt Builder MUST return string.

---

# Step 4

Hash Generation:

```lisp
(sha256-string prompt)
```

---

Output:

```text
stable hash
```

---

# Step 5

State Creation:

```lisp
(make-prefill-state
 context
 target-id
 hash)
```

---

# 18. Example

Input:

```text
Target:

node-5


Context:

node-1
node-2
node-3
```

---

Prompt:

```lisp
(prompt
 (:node :node-1 ...)
 (:node :node-2 ...)
 (:node :node-3 ...))
```

---

Hash:

```text
a8f92....
```

---

Output:

```text
PrefillState

{
 context:
   [node-1 node-2 node-3]

 target:
   node-5

 hash:
   a8f92...
}
```

---

# 19. Determinism Contract

Given:

same:

```text
Graph

Store

Target

Prompt Builder
```

then:

must produce:

```text
same Context

same Prompt

same Hash
```

---

# 20. Immutability Contract

All fields:

```lisp
:read-only t
```

---

意味:

Prefill State は:

```text
snapshot
```

であり:

```text
mutable working state
```

ではない。

---

# 21. Relationship With KV Cache

重要:

```text
Prefill State
```

と:

```text
KV Cache
```

は別物。

---

Correct model:

```text
History

 |
 v

Prefill State

 |
 v

LLM Prefill

 |
 v

KV Cache
```

---

KV:

```text
short-term computation state
```

Prefill:

```text
deterministic input identity
```

---

# 22. Relationship With Replay

Replay:

```text
History

 ↓

project-context

 ↓

canonical-prompt

 ↓

hash verify

 ↓

LLM invocation
```

が可能。

---

# 23. Prompt Hash Usage

用途:

## 23.1 Cache Validation

```text
hash A

vs

hash B
```

---

## 23.2 Debug Trace

Trace:

```text
target-id

prompt hash

response
```

---

## 23.3 Deterministic Audit

同一 Context から:

同一 Prompt が生成されたことを検証。

---

# 24. Complexity

## canonical-prompt

Context size:

[
N
]

の場合:

[
O(N)
]

---

## build-prefill-state

Dominant:

```text
project-context
```

依存。

---

# 25. Extension Points

## 25.1 Alternative Prompt Builder

可能:

```lisp
(build-prefill-state
 ...
 :prompt-builder #'my-builder)
```

---

用途:

* Code prompt
* Chat prompt
* Analysis prompt
* Tool prompt

---

## 25.2 Context Filtering

将来:

```text
important nodes only
```

---

## 25.3 Prompt Versioning

追加候補:

```lisp
prompt-schema-version
```

---

# 26. Chron-OS Mapping

| Component          | Role                |
| ------------------ | ------------------- |
| History/WAL        | Truth               |
| Graph              | Structure           |
| Context Projection | View                |
| Prefill State      | LLM boundary object |
| Prompt Hash        | Identity proof      |
| KV                 | Temporary compute   |

---

# 27. Design Assessment

## Strengths

### 1. LLM State Separation

正しく:

```text
Knowledge ≠ KV
```

を実装している。

---

### 2. Deterministic Boundary

LLM の非決定性前に:

```text
Prompt Hash
```

という検証点を置いている。

---

### 3. Replay Compatibility

Prefill State により:

```text
same history

↓

same prompt identity
```

が可能。

---

# 28. Current Limitations

## 28.1 Hash Only

現在:

```text
hash(prompt)
```

のみ。

将来:

```text
hash(
 context
 +
 builder-version
 +
 schema-version
)
```

が望ましい。

---

## 28.2 Context Order Dependency

現在:

```text
[A B C]
```

と:

```text
[B A C]
```

は別 hash。

これは設計上正しいが、順序規約は必要。

---

# Final Specification Summary

```text
build-prefill-state creates an immutable deterministic
LLM input snapshot.

Pipeline:

Graph/History
      |
      v
Context Projection
      |
      v
Canonical Prompt
      |
      v
SHA256 Identity
      |
      v
Prefill State
      |
      v
LLM Prefill


Properties:

- deterministic
- immutable
- replay-compatible
- KV independent
- prompt identity verifiable


Role in Chron-R2.0-A:

Deterministic Kernel
        |
        v
 Prefill Boundary
        |
        v
Non-deterministic LLM
```

この設計は、Chron-LLM の基本原則である

```
LLM = 推論器
Kernel = 状態管理者
History = Truth
KV = 一時作業領域
```

を Prefill 境界で明確に分離する実装になっています。
