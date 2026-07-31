TYPE World = { id:Str, graph-ref:Ref<Graph>, mem-ref:Ref<Mem>, root-node:NodeID, head-cell:[NodeID], policy:Policy, meta:[Meta], lifecycle:[State] }
TYPE Policy = { include-evals:Bool | ... }
TYPE ReplayRes = { world-id:Str, head-node:NodeID, policy:Policy, meta:Meta, prefill-hash:Hash }

INV-1: World.id != ""
INV-2: World.graph-ref == Shared(Graph) // Never copied
INV-3: World.mem-ref == Shared(Mem) // Never copied
INV-4: Access(World.policy/meta) -> Copy() // Immutable view
INV-5: Update(Head) ONLY via kernel-commit-world!
INV-6: NodeID unique in Graph (Immutable once committed)
INV-7: Replay deterministic

OP make-world(id, graph, mem, root, head, policy, meta?) -> World
  PRE: id != "" AND exists(root) AND exists(head)
  POST: w.graph-ref=graph; w.mem-ref=mem; w.policy=copy(policy); w.meta=[copy(meta)]; w.head-cell=[head]; w.lifecycle=[Created]

OP fork-world(parent) -> World
  POST: child.id!=parent.id; child.graph-ref=parent.graph-ref; child.mem-ref=parent.mem-ref; child.root-node=parent.root-node; child.head-cell=[car parent.head-cell]; child.policy=copy(parent.policy); child.meta=copy(parent.meta)

OP replace-world-metadata!(w, new-meta) -> Void
  POST: w.meta = [copy(new-meta)] // CoW

OP kernel-commit-world!(w, node) -> World
  PRE: causal-node-p(node) AND !exists(get-node(w.graph-ref, node.id))
  SEQ: add-node!(w.graph-ref, node); w.head-cell[0] = node.id
  POST: return w

OP replay-world(w) -> ReplayRes
  PURE
  STATE = build-prefill-state(w.graph-ref, w.mem-ref, car w.head-cell, w.policy)
  RETURN { world-id:w.id, head-node:car w.head-cell, policy:w.policy, meta:car w.meta, prefill-hash:hash(STATE) }