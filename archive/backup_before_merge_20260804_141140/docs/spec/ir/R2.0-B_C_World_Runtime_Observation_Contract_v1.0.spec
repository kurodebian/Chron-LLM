TYPES:
PayloadRef = {hash:SHA256, type:Str, size:U64, storage:Ref}
MemStore = HashTable<Str, Payload>
CausalNode = {id:ID, type:Type, payload:PayloadRef, meta:Map}
CausalEdge = {from:ID, to:ID, type:{:causal|:eval}}
CausalGraph = {nodes:[CausalNode], edges:[CausalEdge]}
ContextNode = {id:ID, type:Type, content:Str, feedbacks:[Str]}
PrefillState = {context:[ContextNode], target:ID, hash:SHA256}
World = {id:ID, graph:Ref, mem:Ref, root:ID, head:ID, policy:Map, meta:Map, lifecycle:{:created|:active|:inactive|:archived}}
Registry = {worlds:[World], ancestry:Map<ID,ID>, active:ID, graph:Ref, mem:Ref}
WorldObs = {ver:1, world-id:ID, root-id:ID, head-id:ID, policy:Map, meta:Map, lifecycle:Enum, parent-id:ID}
RegistryObs = {ver:1, world-ids:[ID], active-id:ID, archived-ids:[ID]}
AncestryObs = {world-id:ID, parent-id:ID, path:[ID]}
DiffObs = {changed:Bool, fields:[Str]}

INVARIANTS:
INV(Graph): Unique(node.id)
INV(Mem): ContentAddr(hash=SHA256(content))
INV(World): head in graph.nodes
INV(Commit): Atomic(GraphAppend, HeadAdvance)
INV(Obs): Type(x) in {null, bool, str, num, char, kw, list}
INV(Truth): kernel-commit-world! == ONLY(head_advance)
INV(Replay): Hash(Graph+Mem+Policy) == PrefillHash

OPERATIONS:
make-memory-store() -> MemStore
add-node!(g, n) -> g' | Pre: !exists(g.nodes, n.id)
add-edge!(g, e) -> g' | Pre: exists(g.nodes, e.from) & exists(g.nodes, e.to)
causal-subgraph(g, target) -> [Node] | Filter: edge.type==:causal; Order: Root->Target
project-context(g, m, target, include_eval) -> [ContextNode] | Logic: ancestry->load->ctx; If include_eval: add :EVAL feedbacks
canonical-prompt(ctx) -> PrefillState | Rule: Deterministic
make-world(id, g, m, root, head, policy, meta) -> World | Pre: exists(g.nodes, root), exists(g.nodes, head)
fork-world(parent, child_id) -> World | Post: child.graph==parent.graph, child.mem==parent.mem
replace-world-metadata!(w, meta) -> w' | Post: w'.meta==meta, w'.graph==w.graph (CoW)
kernel-commit-world!(w, node) -> w' | Pre: valid(node); Post: w'.head==node.id, w'.graph.nodes+=[node]
replay-world(w) -> {id, head, policy, meta, hash}
register-world(r, w) -> r' | Pre: unique(w.id), exists(r.worlds, w.parent)
set-active-world(r, id) -> r' | Pre: w.lifecycle!=:archived
archive-world(r, id) -> r' | Post: w.lifecycle=:archived, r.active!=id
snapshot-world(w) -> WorldObs | Rule: Data-only, No mutation
snapshot-registry(r) -> RegistryObs | Rule: Data-only, No mutation
snapshot-ancestry(w) -> AncestryObs | Rule: Data-only, No mutation
snapshot-diff(w1, w2) -> DiffObs | Rule: Data-only, No mutation