# Chron-R2.0 World Graph Runtime Specification
## World / Causal Graph / Memory Store / Observation Boundary v1.0

**Status:** Stable  
**Layer:** R2.0 Runtime Layer  
**Scope:**

- Causal Graph Runtime
- Content Addressed Memory Store
- Context Projection
- Canonical Prefill State
- World Branch Runtime
- World Registry
- Observation Snapshot Boundary

**Package:**

- `chron-r2-0-a`
    - Core Runtime
- `chron-r2-0-c`
    - Observation Layer


---

# 1. Design Principle

Chron-R2.0 World Runtime は、


Memory
↓
Causal Graph
↓
World State
↓
Projection
↓
Prefill
↓
LLM Runtime


という因果世界再構成パイプラインを提供する。


基本原則:

## 1.1 Graph is Truth Structure

Causal Graph は世界の因果構造を保持する。

Graph は以下を管理する。

- Node
- Edge
- Causal ancestry
- Evaluation relation


ただし payload 本体は保持しない。


---

## 1.2 Memory is Content Addressed

Memory Store は payload を hash により管理する。

特徴:

- 内容アドレス方式
- 重複保存防止
- 再現可能
- 外部状態依存なし



content

|
v

SHA256

|
v

payload-ref



---

## 1.3 World is a Projection Context

World は Graph + Memory 上の視点である。

World は正史そのものではなく、


World
|
+-- root-node
|
+-- head-node
|
+-- projection-policy
|
+-- metadata
|
+-- lifecycle


を持つ実行コンテキストである。


---

# 2. Memory Store Specification


## 2.1 Payload Reference

```lisp
(defstruct payload-ref
 hash
 type
 size
 storage)

Payload は直接保持せず参照のみ保持する。

Fields
Field	Type	Meaning
hash	string	SHA256 identifier
type	keyword	payload type
size	integer	UTF8 byte size
storage	keyword	storage backend

Example:

(make-payload-ref
 "sha256:xxxx"
 :text
 128
 :memory)
2.2 Memory Store

生成:

(make-memory-store)

内部:

HashTable

hash
 |
 +-- payload

特徴:

global cache 不使用
process state 非依存
deterministic
2.3 Store Operation
store-payload
(store-payload store content)

処理:

content
 ↓
canonical string
 ↓
UTF8 bytes
 ↓
SHA256
 ↓
payload-ref

戻り値:

payload-ref
load-payload
(load-payload store reference)

Payload を復元する。

入力:

payload-ref
hash string

出力:

content string
3. Causal Graph Specification
3.1 Causal Node
(defstruct causal-node
 id
 type
 payload-ref
 metadata)

意味:

Field	Meaning
id	node identifier
type	semantic type
payload-ref	external content reference
metadata	auxiliary data

Node は immutable。

3.2 Causal Edge
(defstruct causal-edge
 from
 to
 type)

Edge type:

:causal
:eval

など。

3.3 Causal Graph
(defstruct causal-graph
 nodes
 edges)

保持:

Graph

Nodes:
 A
 B
 C


Edges:

A --causal--> B

B --eval--> E
4. Graph Mutation API
add-node!
(add-node! graph node)

保証:

node type validation
duplicate id rejection

Failure:

Duplicate node id
add-edge!
(add-edge! graph edge)

保証:

edge validation
endpoint existence

Failure:

Missing endpoint
5. Causal Projection
causal-subgraph
(causal-subgraph graph target-id)

目的:

Target node の因果祖先を取得する。

対象:

only :CAUSAL edges

Algorithm:

target

 ↓

parent search

 ↓

recursive ancestry

 ↓

root first ordering

Example:

A → B → C


target C


Result:

(A B C)

保証:

cycle safe
deterministic ordering
non destructive
6. Context Projection
Context Node
(defstruct context-node
 id
 type
 content
 feedbacks)

これは LLM prompt 用の projection object。

project-context
(project-context graph store target-id)

処理:

Causal Graph

     |
     v

causal-subgraph

     |
     v

load payload

     |
     v

Context Node

結果:

(
 context-node
 context-node
 ...
)
6.1 Evaluation Projection

Default:

include-evaluations=nil

の場合:

causal fact only

trueの場合:

Node

 |
 +-- :eval

      |
      v

 Evaluation payload

を feedback として追加する。

7. Prefill Runtime
Prefill State
(defstruct prefill-state
 context
 target-id
 hash)

意味:

LLM generation 前の canonical context。

canonical-prompt
(canonical-prompt context)

生成形式:

(prompt
 (:node ID
  :type TYPE
  :content CONTENT
  :feedback FEEDBACK))

特徴:

deterministic
hashable
replay可能
build-prefill-state
(build-prefill-state
 graph
 store
 target-id)

Pipeline:

Graph

 ↓

project-context

 ↓

canonical-prompt

 ↓

SHA256

 ↓

prefill-state
8. World Runtime
World Model

World represents:

One possible causal viewpoint

Structure:

World

world-id

root-node

head-node

projection-policy

metadata

lifecycle
8.1 World Lifecycle

States:

:active

:inactive

:archived

Rules:

Active

Only one world may be active.

Archived

Cannot become active.

9. World Registry
Registry
(defstruct world-registry
 worlds
 ancestry
 active-id
 graph
 memory)

Purpose:

World identity management.

Registry Rules
Shared Truth Constraint

Registered worlds must share:

same causal graph
same memory store

Validation:

eq graph
eq memory

Meaning:

Worlds are views, not independent copies.

10. World Registration
register-world
(register-world registry world)

Guarantees:

unique world-id
ancestry validation
graph consistency

Does NOT:

modify graph
modify memory
11. Active World Switching
set-active-world
(set-active-world registry id)

Behavior:

Before:

W1 active

After:

W1 inactive

W2 active
12. World Archiving
archive-world
(archive-world registry id)

Effect:

lifecycle = :archived

If active:

active-world=nil
13. Observation Boundary

Package:

chron-r2-0-c

Purpose:

Expose World state without exposing mutable runtime objects.

Principle:

Observation is data-only snapshot.

13.1 Observation Schema

Version:

+observation-schema-version+
=
1
World Observation
world-observation

Fields:

Field
world-id
root-node-id
head-node-id
projection-policy
metadata
lifecycle
parent-world-id
Registry Observation

Contains:

world ids

active world

archived worlds
Ancestry Observation

Represents:

child
 |
 parent
 |
 ancestry path
Diff Observation

Represents:

changed-p

changed-fields

Example:

(:head-node-id
 :metadata)
14. Observation Safety Rules

Observation layer rejects:

objects
structures
runtime references

Allowed:

primitive tree only

Primitive:

string
number
keyword
character
list
15. Runtime Architecture Summary
             LLM Runtime
                  |
                  |
             Prefill State
                  |
                  |
          Context Projection
                  |
                  |
          Causal Graph Runtime
                  |
          +-------+-------+
          |               |
      Memory Store    World Registry
          |
      Payload Hash
16. Frozen Contracts
Immutable
payload-ref structure
causal-node structure
causal-edge structure
causal ancestry semantics
projection semantics
prefill hashing
observation schema
Extensible
payload storage backend
projection policy
evaluation types
world metadata
observation fields
Final Statement

Chron-R2.0 World Graph Runtime は、

「因果グラフを真実構造として保持し、Memory を内容アドレス化し、World を視点として管理し、LLM に再現可能な Prefill Context を提供する Runtime Layer」

である。

本仕様により、

因果再構成
世界線分岐
deterministic replay
LLM context reconstruction
外部観測可能な snapshot

を統一的に扱うことが可能になる。