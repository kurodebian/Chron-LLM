# **Chron-LLM_R2.0-A_Graph_Runtime_Core_Constitution_Spec.md**

**Document ID:** CHRON-R2.0-A-GRAPH-CONSTITUTION  
**Constitution Revision:** 1.0  
**Status:** FROZEN CANDIDATE  
**Classification:** Constitution-Level Specification  
**Layer:** R2.0-A Graph Runtime Core  
**Target:** CodeX Implementation & Deterministic Verification Suite  

# **0. Purpose**

R2.0-A establishes the deterministic kernel foundation of Chron-LLM.

Its purpose is to define the immutable boundary between:

- Canonical History
- Memory Content
- Projection
- Prompt Construction
- Future Runtime Execution

All subsequent phases:

- R2.0-B World Runtime
- R2.0-C Observability Runtime
- R2.0-D Commit Kernel
- R2.1 Backend ABI
- R2.2 Evaluator

MUST operate within the deterministic boundaries defined here.

R2.0-A guarantees:

- deterministic causal structure
- immutable Memory content
- append-only Canonical Graph
- deterministic Projection
- pure Prompt generation
- reproducible Prefill State

# **0.1 Determinism Definition**

Chron-LLM determinism is defined as:

Given:

```
Canonical Graph Structure

*

Memory Store Content

*

Projection Policy

*

Prompt Builder Version
```

Then:

```
Prefill State MUST be identical
in both content and hash.
```

Identical logical inputs MUST always produce identical execution context.

This definition is the foundational invariant of the R2 series.

# **1. Core Philosophy**

Chron-LLM separates:

```
Fact
Knowledge
Usage
Execution
Authority
```

into independent layers.

```
Graph      = What happened (Causal Fact)

Memory     = What content exists

Projection = How information is selected

Prompt     = How context is formatted

Backend    = How generation is executed

Evaluator  = How proposals are produced

Kernel     = What becomes Canonical truth
```

Fundamental principles:

```
Causal is Fact.

Evaluation is Knowledge.

Prompt is Usage.

Commit is Authority.
```

The Graph stores historical facts only.

The Graph MUST NOT encode:

- success
- failure
- quality
- priority
- preference

Those belong to higher-level interpretation layers.

# **2. Authority Boundary**

Chron-LLM authority hierarchy:

```
Kernel
|
+-- Commit Kernel
| |
| +-- Canonical Event Creation
| +-- Canonical Graph Append
| +-- World Head Advancement
|
+-- Canonical Graph
|
+-- Memory Store
|
+-- Runtime Views
|
+-- World Runtime
|
+-- Observability Runtime
|
+-- Backend Runtime
|
+-- Evaluator Runtime
```

Authority Rules:

- Kernel owns Canonical transition authority.
- Commit Kernel is the only mechanism allowed to mutate Canonical state.
- Canonical Graph owns causal history structure.
- Memory Store owns immutable content.
- World Runtime owns execution views.
- Observability Runtime owns read-only inspection.
- Backend generates proposals.
- Evaluator generates proposals and evaluations.

No component may bypass Commit Kernel.

# **2.1 Canonical Mutation Rule**

Canonical state mutation is restricted.

Forbidden:

```
Backend
↓
Graph Mutation

Evaluator
↓
Graph Mutation

Projection
↓
Graph Mutation
```

Required:

```
Proposal

↓

Validation

↓

Commit Kernel

↓

Canonical Event

↓

Graph Append
```

Only Commit Kernel may create Canonical history.

# **3. Memory Store Specification**

## **3.1 Responsibility**

Memory Store owns content.

Graph stores references only.

```
Graph Node

↓

payload-ref

↓

Memory Store
```

Graph MUST NOT contain payload content.

## **3.2 Payload Reference**

```
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

## **3.3 Required API**

```
store-payload

load-payload

payload-exists-p
```

## **3.4 Memory Immutability**

Memory Store MUST be immutable.

Rules:

- Existing payload MUST NOT change.
- Update creates new payload.
- Hash MUST derive from content.

Example:

```
store(A)

store(A)

↓

same hash
```

# **4. Canonical Graph Specification**

## **4.1 Canonical Node**

```
(defstruct canonical-node
id
type
payload-ref
metadata)
```

Node Types:

```
:system

:prompt

:assistant

:eval

:feedback
```

Node Type Semantics:

```
:system
System initialization event.

:prompt
Prompt construction event.

:assistant
Generated response event.

:eval
Evaluation recording event.

:feedback
Feedback recording event.
```

## **Canonical History Recording Rule**

All accepted nodes are stored in Canonical Graph.

Canonical Graph represents:

```
Canonical History
=
All accepted historical events
```

However:

```
Canonical History
≠
Causal Execution History
```

A Canonical Node records a historical fact.

It does not automatically define execution causality.

Therefore:

```
Recorded Fact
≠
Causal Fact
```

## **Node Type Authority Rule**

Only nodes connected through:

:causal

edges participate in execution causal lineage.

`:eval` and `:feedback` nodes represent observational history.

They MAY:

- exist inside Canonical Graph
- reference Canonical Nodes
- be used by Projection Layers
- participate in analysis views

They MUST NOT:

- define execution causality
- become causal ancestors of execution events
- modify existing causal lineage
- directly affect Backend execution
- directly mutate Canonical state

## **Edge Separation Rule**

Canonical relationships are separated by edge type.

Execution causality:

```
:causal
```

Evaluation relationship:

```
:eval
```

Feedback relationship:

```
:feedback
```

Therefore:

```
:eval Node
+
:feedback Node
```
DO NOT

create execution causality

## **Projection Rule**

Evaluation and feedback information MUST be accessed through explicit projection layers.

Evaluation Projection

Feedback Projection

Projection MAY expose:

- evaluation knowledge
- feedback knowledge

Projection MUST NOT:

- mutate Canonical Graph
- mutate Memory Store
- modify causal lineage

## **Causal Isolation Guarantee**

The existence of:

:eval nodes

or

:feedback nodes

MUST NOT change:

Causal Graph Structure

Causal Projection Result

Causal Prefill State

unless explicitly included by:

Projection Policy

Final semantic distinction:

:causal

Execution history lineage

:eval

Evaluation observation history

:feedback

Feedback observation history

No non-causal node type may become a hidden source of execution causality.

## **4.2 Node Contract**

Nodes MUST:

- be immutable
- reference immutable payload
- represent accepted Canonical history only

Nodes MUST NOT:

- contain mutable state
- contain execution state
- contain future predictions
- contain hidden runtime state

Metadata:

- MAY contain immutable descriptive information.
- MUST NOT contain mutable execution state.
- MUST NOT become an alternative source of truth.

## **4.3 Graph Edge**

```
(defstruct graph-edge
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

Meaning:

```
:causal
Execution lineage relationship.

:eval
Evaluation observation relationship.

:feedback
Feedback observation relationship.
```

Only:

```
:causal
```

edges define execution causality.

## **4.4 Graph**

```
(defstruct canonical-graph
node-store
edge-store
root-id)
```

Graph Rules:

- append-only
- node mutation prohibited
- edge mutation prohibited

All changes MUST be represented by new nodes or edges.

## Root Node Contract

root-id MUST reference the immutable first Canonical Node.

root-id MUST NOT change after Graph creation.

All causal projection MUST originate from root-id.

## Root Reachability Contract

Every :causal node MUST be reachable from root-id.

Nodes not reachable through :causal edges
MUST NOT participate in causal execution history.

A Canonical Graph containing unreachable causal nodes
is invalid.

# **5. Causal Projection**

Causal Projection extracts historical causality.

Projection is a deterministic view operation.

The Projection Layer:

- MUST NOT mutate Graph.
- MUST NOT create Canonical state.
- MUST NOT change Memory.

Rule:

`causal-subgraph`

MUST traverse only:

:causal

edges.

Evaluation information MUST:

- NOT mutate causal history.
- NOT appear in causal projection.
- NOT define causal ordering.

API:

```
causal-subgraph(graph target-id)
```

Output:

```
ordered causal node sequence
```

# **6. Evaluation Projection**

Evaluation exists as an independent knowledge layer.

API:

```
associated-evaluations(graph node-id)
```

Evaluation:

- MAY reference causal nodes
- MUST NOT modify causal structure
- MUST NOT change historical fact

# **7. Context Projection**

Context Projection combines independent views.

```
Causal View

*

Evaluation View

↓

Context View
```

Context Node:

```
(defstruct context-node
id
type
content
feedbacks)
```

Context Projection MUST be deterministic.

# **8. Prompt Builder Contract**

Prompt Builder MUST be a pure function.

Input:

```
context-node list
```

Output:

```
prompt representation
```

MUST:

- deterministic
- side-effect free
- reproducible

MUST NOT:

```
Graph Access

Memory Access

Random

Timestamp

External IO

Global Mutation
```

# **9. Canonical Prompt Format**

```
(prompt
(:node <id>
:type <keyword>
:content <string>
:feedback (<string> ...)))
```

# **10. Prefill State Contract**

```
(defstruct prefill-state
context
target-id
hash)
```

Guarantee:

Given identical:

```
Canonical Graph

Memory Store

Projection Policy

Prompt Builder Version
```

Then:

```
Prefill State MUST be identical.

Prefill Hash MUST be identical.
```

World-specific differences MUST originate only from explicit Projection Policy differences.

# **11. Verification Specification**

R2.0-A MUST satisfy:

| Test ID | Name | Objective |
|---|---|---|
| T1 | Memory Determinism      | Same content produces same hash              |
| T2 | Graph Replay            | Same Canonical Graph and Memory reproduce identical causal sequence |
| T3 | View Separation         | Evaluation nodes MUST NOT appear in causal projection |
| T4 | Context Projection      | Causal View and Evaluation View merge without mutation |
| T5 | Prefill Hash Stability  | Same Graph, Memory, Projection Policy, and Prompt Builder produce same hash |
| T6 | Evaluation Independence | Existence of evaluation nodes MUST NOT alter causal-only Prefill State     |


# **11.1 T6 Formal Definition**

Given identical:

```
Canonical Graph

Memory Content

Causal Projection Policy
```

Then:

```
Causal Prefill State MUST remain identical
```

regardless of the existence of additional:

```
:eval
:feedback
```

nodes.

Evaluation information MAY affect Prefill State only through an explicit:

```
Evaluation Projection Policy
```

Evaluation Projection MUST NOT mutate:

```
Canonical Graph

Memory Store

Causal History
```

# **12. Completion Criteria**

R2.0-A is complete when:

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

# **13. Out of Scope**

R2.0-A excludes:

```
Backend ABI

llama.cpp integration

KV Cache

World Fork

Scheduler

Evaluator Generation

Tool Execution

Persistence
```

# **14. Next Phase: R2.0-B World Runtime**

R2.0-B introduces:

```
World Identity

Forked Execution Views

Copy-on-Write Metadata

World Projection Policy
```

Worlds MUST preserve:

```
Single Canonical Graph

Single Memory Store

Shared History
```

# **15. Implementation Rules**

Implementation MUST:

- preserve immutability
- preserve deterministic behavior
- use Commit Kernel for mutation
- reject hidden global state
- provide verification tests

Any violation requires Constitution Revision.

# **Final Statement**

This Constitution defines:

- Canonical history boundary
- Immutable content ownership
- Causal data model
- Projection semantics
- Deterministic context generation

R2.0-A establishes the immutable historical substrate.

All future Runtime layers MUST conform.

Only Commit Kernel may create Canonical history.
 