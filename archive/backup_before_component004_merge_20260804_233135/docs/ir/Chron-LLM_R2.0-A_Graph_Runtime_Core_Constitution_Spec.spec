Hash = sha256
ID = unique-identifier
PayloadType = text | json | blob | meta
StorageType = memory | disk | remote
NodeType = system | prompt | assistant | eval | feedback
EdgeType = causal | eval | feedback

PayloadRef = {hash: Hash, type: PayloadType, size: Int, storage: StorageType}
CanonicalNode = {id: ID, type: NodeType, payload-ref: PayloadRef, metadata: Map}
GraphEdge = {from: ID, to: ID, type: EdgeType}
CanonicalGraph = {nodes: Map[ID, CanonicalNode], edges: GraphEdge[], root-id: ID}
ContextNode = {id: ID, type: NodeType, content: String, feedbacks: String[]}
PrefillState = {context: ContextNode[], target-id: ID, hash: Hash}

MemoryStore: Map[Hash, Payload]
GraphStore: CanonicalGraph

store-payload(content) -> Hash
PRE: content != null
POST: MemoryStore[hash(content)] == content

load-payload(hash) -> Payload
PRE: payload-exists-p(hash)

payload-exists-p(hash) -> Bool

causal-subgraph(graph: CanonicalGraph, target-id: ID) -> CanonicalNode[]
PRE: target-id in graph.nodes
POST: result contains only nodes reachable via EdgeType=causal

associated-evaluations(graph: CanonicalGraph, node-id: ID) -> CanonicalNode[]
PRE: node-id in graph.nodes
POST: result contains nodes linked via EdgeType=eval or EdgeType=feedback

build-prompt(context-nodes: ContextNode[]) -> Prompt
PRE: context-nodes != null
POST: result is deterministic; no side-effects

commit-proposal(proposal) -> CanonicalEvent
PRE: proposal validated
POST: GraphStore appended with CanonicalEvent

INV-MEM-IMMUTABLE: MemoryStore[h] == constant after write
INV-MEM-HASH: hash(content) == h
INV-GRAPH-APPEND: GraphStore.size >= previous_size; no node/edge mutation
INV-GRAPH-ROOT: GraphStore.root-id == constant
INV-GRAPH-REACH: forall n in GraphStore.nodes where n.type in {system, prompt, assistant}: reachable(GraphStore.edges, root-id, n.id)
INV-CAUSAL-SEPARATION: causal-subgraph traverses only EdgeType=causal; excludes NodeType={eval, feedback}
INV-PROMPT-PURE: build-prompt is deterministic; no side-effects; no external IO/random/timestamps
INV-PREFILL-DET: PrefillState(Graph, Memory, Policy, Builder) -> unique hash
INV-AUTHORITY: GraphStore mutation allowed ONLY via CommitKernel
INV-EVAL-INDEP: Existence of NodeType={eval, feedback} does not alter causal-subgraph or causal PrefillState

Proposal -> Validation -> CommitKernel -> CanonicalEvent -> GraphAppend

T1: Memory Determinism (content -> hash)
T2: Graph Replay (Graph+Memory -> identical causal sequence)
T3: View Separation (eval nodes excluded from causal projection)
T4: Context Projection (Causal+Eval merge without mutation)
T5: Prefill Hash Stability (Inputs -> identical hash)
T6: Evaluation Independence (eval nodes -> no causal PrefillState change)