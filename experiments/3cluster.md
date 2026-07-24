# Experiment Graph Model Specification v1.0

## 3-Cluster Graph Construction and Topology Model

# 1. Overview

## 1.1 Purpose

`experiment` パッケージに定義される Graph Model は、Chron-LLM / Chron-OS の状態遷移・収束解析実験用に使用する **人工的な有向グラフ構造**を提供する。

本モジュールの役割:

* Node 定義
* Edge 定義
* Graph 定義
* 3 Cluster Test Graph の生成
* SCC (Strongly Connected Component) 解析対象データ提供
* Attractor / Basin Analysis の入力生成

# 2. Architectural Position

```
                Experiment Graph

                      |
                      v

              Graph Runtime Analysis

                      |
          +-----------+-----------+
          |                       |
          v                       v

     SCC Analysis          Attractor Analysis

          |                       |
          v                       v

    Cycle Detection        Basin Structure

          |
          v

     Phase-E Trace Analysis
```

# 3. Package Specification

## 3.1 Package Definition

```lisp
(defpackage :experiment
  (:use :cl)
  (:export
   #:make-3cluster-graph
   #:node-id
   #:node-role
   #:edge-from
   #:edge-to
   #:edge-relation
   #:edge-strength
   #:graph-nodes
   #:graph-edges
   #:compute-sccs
   #:find-recurrent-cycle
   #:find-cycle
   #:build-basin-structure
   #:basin
   #:rollout*
   #:next-event
   #:find-attractor
   #:build-basin-map))
```

# 4. Responsibility Boundary

## 4.1 Provides

| Component      | Responsibility           |
| -------------- | ------------------------ |
| Node           | State representation     |
| Edge           | Transition relation      |
| Graph          | State-space container    |
| 3Cluster Graph | Test topology generation |

## 4.2 Does Not Provide

| Function           | Layer        |
| ------------------ | ------------ |
| State mutation     | Kernel       |
| Event commit       | Commit layer |
| Persistence        | WAL          |
| LLM inference      | Backend      |
| Semantic reasoning | LLM          |

# 5. Graph Data Model

# 5.1 Node Structure

```lisp
(defstruct node
  id
  role)
```

## Node Logical Model

```
Node =
{
 id   : unique identifier
 role : semantic category
}
```

## Fields

## node-id

Accessor:

```lisp
(node-id node)
```

Purpose:

Node identity.

Examples:

```
:a1
:b2
:c1
```

## node-role

Accessor:

```lisp
(node-role node)
```

Purpose:

Node classification.

Defined roles:

| Role      | Meaning                     |
| --------- | --------------------------- |
| :reply    | Reply transition cluster    |
| :temporal | Temporal transition cluster |
| :bridge   | Bridge node                 |

# 5.2 Edge Structure

```lisp
(defstruct edge
  from
  to
  relation
  strength)
```

## Edge Logical Model

```
Edge =
{
 from
 to
 relation
 strength
}
```

## Fields

## edge-from

Source node.

Example:

```
:a1
```

## edge-to

Destination node.

Example:

```
:a2
```

## edge-relation

Transition category.

Examples:

```
:reply

:temporal
```

## edge-strength

Transition weight.

Range:

```
0.0 - 1.0
```

Example:

```
0.9
```

# 5.3 Graph Structure

```lisp
(defstruct graph
  nodes
  edges)
```

## Graph Model

```
Graph =
{
 nodes : Node List
 edges : Edge List
}
```

# 6. 3 Cluster Graph Generator

## Function

```lisp
(make-3cluster-graph)
```

## Purpose

Creates a deterministic test graph containing:

1. Reply Cluster
2. Temporal Cluster
3. Bridge Cluster

# 7. Generated Node Topology

## 7.1 Nodes

Generated nodes:

```
A Cluster

a1
a2
a3


B Cluster

b1
b2
b3


C Bridge

c1
c2
```

## Node Classification

| Node | Role     |
| ---- | -------- |
| a1   | reply    |
| a2   | reply    |
| a3   | reply    |
| b1   | temporal |
| b2   | temporal |
| b3   | temporal |
| c1   | bridge   |
| c2   | bridge   |

# 8. Edge Topology

# 8.1 A Cluster

## Purpose

Strong reply cycle.

Edges:

```
a1 → a2
a2 → a3
a3 → a1
```

Relation:

```
:reply
```

Strength:

```
0.9
```

Graph:

```
       +----+
       |    |
       v    |
a1 → a2 → a3
^         |
|---------|
```

# 8.2 B Cluster

## Purpose

Temporal recurrence cycle.

Edges:

```
b1 → b2
b2 → b3
b3 → b1
```

Relation:

```
:temporal
```

Strength:

```
0.3
```

Graph:

```
       +----+
       |    |
       v    |
b1 → b2 → b3
^         |
|---------|
```

# 8.3 C Bridge Cluster

## Purpose

Connect independent attractor candidates.

Edges:

## c1

```
c1 → a1
```

Relation:

```
:reply
```

Strength:

```
0.6
```

```
c1 → b1
```

Relation:

```
:temporal
```

Strength:

```
0.4
```

## c2

```
c2 → a2
```

Relation:

```
:reply
```

Strength:

```
0.4
```

```
c2 → b2
```

Relation:

```
:temporal
```

Strength:

```
0.6
```

# 9. Complete Graph Structure

```
                 +---------+
                 |         |
                 v         |
              a1 → a2 → a3 |
              ^            |
              |------------|


              b1 → b2 → b3
              ^            |
              |------------|


          c1 --------> a1
          |
          |
          +--------> b1


          c2 --------> a2
          |
          |
          +--------> b2
```

# 10. Graph Properties

## 10.1 Node Count

```
N = 8
```

## 10.2 Edge Count

```
E = 10
```

# 11. Expected SCC Structure

Given the topology:

## SCC-1

```
{a1,a2,a3}
```

Reason:

All nodes mutually reachable.

## SCC-2

```
{b1,b2,b3}
```

Reason:

Temporal cycle.

## Bridge Nodes

```
{c1,c2}
```

Not strongly connected because:

```
c → cluster

but

cluster → c
```

does not exist.

# 12. Attractor Analysis Compatibility

This graph is designed for:

```
Graph

↓

rollout

↓

find-attractor

↓

build-basin-map

↓

build-basin-structure
```

Expected attractor candidates:

```
A cycle

(a1,a2,a3)


B cycle

(b1,b2,b3)
```

# 13. Basin Analysis Example

Potential result:

```
Basin A

attractor:
(a1,a2,a3)

nodes:
[c1,c2,a1,a2,a3]


Basin B

attractor:
(b1,b2,b3)

nodes:
[b1,b2,b3]
```

※ 実際の分類は `next-event` / `rollout*` / `find-attractor` の遷移規則に依存する。

# 14. Chron-OS Mapping

このGraph Modelは Chron-OS の以下の抽象に対応する。

```
State Space

     |
     v

Graph Nodes

     |
     v

Event Transition

     |
     v

Trajectory

     |
     v

Attractor

     |
     v

Basin
```

# 15. Determinism Contract

## Input

固定:

```
nodes

edges

transition rules
```

## Output

必ず同一:

```
SCC

cycle

attractor

basin structure
```

# 16. Design Assessment

## Strengths

### 1. Minimal Topology

8 nodes / 10 edges で以下を検証可能:

* SCC
* cycle
* attractor
* basin
* bridge influence

### 2. Separation of Concepts

```
Node
 ↓
Edge
 ↓
Graph
 ↓
Trajectory
 ↓
Attractor
 ↓
Basin
```

という解析階層が明確。

### 3. Chron-OS Compatibility

このGraphは:

* Runtime state graph
* Event transition graph
* Worldline graph

の検証用モデルとして利用可能。

# 17. Formal Specification Summary

```
3ClusterGraph provides a deterministic directed graph.

Components:

Nodes:
    8 states

Edges:
    10 transitions


Clusters:

A:
    reply recurrent cycle

B:
    temporal recurrent cycle

C:
    bridge nodes


Purpose:

Evaluate:

    SCC detection
    cycle discovery
    attractor detection
    basin construction
    state-space topology
```

このコードは、前段の `build-basin-map` / `build-basin-structure` と組み合わせることで、Chron-OS Phase-E の **「状態空間トポロジー解析用リファレンスグラフ」** として機能する設計になっています。
