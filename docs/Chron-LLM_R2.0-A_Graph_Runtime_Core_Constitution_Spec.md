# **Chron-LLM_R2.0-A_Graph_Runtime_Core_Constitution_Spec.md**

**Document ID:** CHRON-R2.0-A-GRAPH-CONSTITUTION  
**Status:** Normative / Constitution-Level  
**Target:** CodeX Implementation & Verification Suite  
**Phase:** R2.0-A  
**Purpose:** Deterministic Graph Runtime Core Foundation  

---

# **0. Purpose**

R2.0-A の目的は、Chron-LLM の決定論的カーネル基盤を確立し、後続フェーズ：

- R2.0-B Worldline Runtime  
- R2.1 Backend ABI  
- R2.2 Evaluator  

がこの基盤の境界条件を侵食しないように固定することである。

R2.0-A は以下を保証する：

- 因果構造の決定論性  
- Memory 内容の不変性  
- Projection の再現性  
- Prompt 生成の純粋性  
- Prefill State の完全再現性  

---

# **0.1 Determinism Definition (R2.0-A)**

Chron-LLM における決定論とは以下を意味する。

```
Given:

  Graph (Structure)
  Memory (Content)
  Projection Policy (View)
  Prompt Builder (Pure Function)

Then:

  Prefill State MUST be identical
  in both content and hash.
```

同一入力状態から生成される実行状態は、常に同一でなければならない。  
この定義は R2 系全体の基準となる。

---

# **1. Core Philosophy**

Chron-LLM の責務分離：

```
Graph      = What happened (Structure)
Memory     = What content exists (Content)
Projection = How information is viewed (View)
Prompt     = How context is formatted (Usage)
Backend    = How generation occurs (Execution)
Evaluator  = How results are judged (Proposal)
Kernel     = What becomes truth (Authority)
```

基本原則：

```
Causal is Fact.
Evaluation is Knowledge.
Prompt is Usage.
```

Graph は価値判断を保持しない。  
成功・失敗・高評価・低評価を区別せず、発生した事象を事実として保存する。  
評価・優先度・探索戦略は上位レイヤーの責務である。

---

# **2. Module Structure**

```
chron-os/

+-- memory/
|    +-- store.lisp
|
+-- graph-runtime/
|    +-- graph.lisp
|    +-- causal.lisp
|    +-- projection.lisp
|    +-- prefill.lisp
|
+-- tests/
     +-- r2-0-a-tests.lisp
```

---

# **2.1 Authority Boundary**

The authority hierarchy of Chron-LLM is:

```
Kernel
|
+-- Canonical Graph
|
+-- Memory Store
|
+-- Projection Policy
|
+-- Backend
|
+-- Evaluator
```

## **Authority Rules**

- Kernel owns truth.  
- Graph owns history structure.  
- Memory owns immutable content.  
- Projection owns context selection.  
- Backend owns generation only.  
- Evaluator produces proposals only.  

**No upper layer may directly mutate lower authority layers.**

## **Evaluator Commit Flow**

禁止：

```
Evaluator
  ↓
Direct Graph Mutation
```

正しい流れ：

```
Evaluator
  ↓
Evaluation Proposal
  ↓
Kernel Validation
  ↓
Commit Event
  ↓
Canonical Graph
```

---

# **3. Memory Store Specification**

## **3.1 Responsibility**

Memory Store は内容データを管理する。  
Graph は内容を保持しない。  
Graph Node は Memory Reference のみ保持する。

---

## **3.2 Payload Reference**

```lisp
(defstruct payload-ref
  hash
  type
  size
  storage)
```

Fields:

```
hash      Content Address
type      :text | :json | :blob | :meta
size      Byte Size
storage   :memory | :disk | :remote
```

---

## **3.3 Required API**

```
store-payload
load-payload
payload-exists-p
```

---

## **3.4 Immutability Contract**

Memory Store MUST be immutable.

Rules:

- 保存後の payload 変更は禁止。  
- 更新は新しい payload として扱う。  
- hash は内容から決定される。

Example:

```
store(A)
store(A)
→ same hash
```

---

# **4. Graph Runtime Specification**

## **4.1 Node**

```lisp
(defstruct causal-node
  id
  type
  payload-ref
  metadata)
```

Node Type examples:

```
:system
:prompt
:assistant
:eval
:feedback
```

---

## **4.2 Edge**

```lisp
(defstruct causal-edge
  from
  to
  type)
```

Edge Types:

```
:causal
:eval
:feedback
```

---

## **4.3 Graph**

```lisp
(defstruct causal-graph
  nodes
  edges)
```

Graph Rules:

- Append only  
- Node mutation 禁止  
- Edge mutation 禁止  

変更は新しい Node / Edge として表現する。

---

# **5. Causal Projection**

## **5.1 Rule**

`causal-subgraph` は `:causal` edge のみを辿る。

評価情報は混入してはならない。

---

## **5.2 API**

```
causal-subgraph(graph target-id)
```

Output:

```
ordered causal node sequence
```

---

# **6. Evaluation Projection**

Evaluation は独立した View として取得する。

API:

```
associated-evaluations(graph node-id)
```

Evaluation は因果履歴を書き換えない。

---

# **7. Context Projection**

Context Projection は複数 View を非破壊的に統合する。

```
Causal View
+
Evaluation View
↓
Context View
```

Context Node:

```lisp
(defstruct context-node
 id
 type
 content
 feedbacks)
```

---

# **8. Prompt Builder Contract**

Prompt Builder は Pure Function とする。

## **MUST**

- Pure Function  
- Deterministic Output  
- Input = context-node list  

## **MUST NOT**

```
Graph Access
Memory Access
Random
Timestamp
External IO
Global State Mutation
```

---

# **9. Canonical Prompt Format**

```lisp
(prompt
 (:node <id>
  :type <keyword>
  :content <string>
  :feedback (<string> ...)))
```

---

# **10. Prefill State**

```lisp
(defstruct prefill-state
 context
 target-id
 hash)
```

Guarantee:

同一：

```
Graph
Memory
Projection Policy
Prompt Builder
```

から生成される Prefill State は同一 hash を持つ。

---

# **11. Verification Specification**

Chron-LLM R2.0-A は以下の Kernel Invariants を満たさなければならない。

| Test ID | Name                    | Objective |
| ------- | ----------------------- | ---------- |
| **T1**  | Memory Determinism      | 同一内容 → 同一 hash |
| **T2**  | Graph Replay            | 因果列順序の再現 |
| **T3**  | View Separation         | causal に eval が混入しない |
| **T4**  | Context Projection      | 因果＋評価の非破壊統合 |
| **T5**  | Prefill Hash Stability  | 同一入力 → 同一 hash |
| **T6**  | Evaluation Independence | eval の存在で causal-only 結果が変化しない |

---

## **11.1 T6 Evaluation Independence — Formal Definition**

Purpose:
Verify that causal history remains independent from evaluation knowledge.

Rule:

Given identical:
- Graph causal structure
- Memory content
- Projection Policy excluding evaluation view

Then:

Prefill State MUST remain identical
regardless of existence of :eval nodes.

Evaluation nodes may affect Prefill State
ONLY through an explicit Evaluation Projection Policy.

---

# **12. Completion Criteria**

R2.0-A Completion:

```
[PASS]

Memory Determinism
Graph Determinism
Causal/Evaluation Separation
Projection Determinism
Prompt Determinism
Prefill Hash Stability
Evaluation Independence
```

Canonical result:

```
Canonical Prefill Hash = sha256:<value>
```

Implementation completion後に記録する。

---

# **13. Out of Scope**

R2.0-A では以下を扱わない。

```
Backend ABI
llama.cpp integration
KV Cache
Worldline Fork
Scheduler
Evaluator Generation
Tool Execution
```

---

# **14. Next Phase: R2.0-B Worldline Runtime**

R2.0-B の目的：

```
make-world
fork-world
world-root
copy-on-write metadata
branch projection
worldline selection policies
```

R2.0-A の決定論的基盤上に、世界線を OS の一級オブジェクトとして導入する。

---

# **15. Implementation Rules**

Implementation MUST:

- Follow API signatures defined in this document.
- Preserve immutability guarantees.
- Reject hidden global state.
- Provide deterministic tests before adding new phases.
- Do not implement out-of-scope components.

Any deviation requires a specification revision.

---

# **Final Statement**

本仕様書は Chron-LLM R2 系における：

- Kernel Boundary  
- Data Ownership  
- Causal Model  
- Projection Model  
- Deterministic Verification  

を定義する Constitution Specification である。

CodeX implementation MUST treat this document as a **binding contract**。  
違反する実装は仕様外とする。

---
