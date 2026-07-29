TYPE Node = {id:Object, type:Keyword, payload-ref:Ref, metadata:Any} : immutable
TYPE Edge = {from:Object, to:Object, type::causal|:eval}
TYPE Graph = {nodes:[Node], edges:[Edge]}
TYPE ContextNode = {id:Object, type:Keyword, content:Payload, feedbacks:[Eval]}
TYPE PrefillState = {context:[ContextNode], target-id:Object, hash:String}

OP get-node(g:Graph, id:Object) -> Node|nil
OP add-node!(g:Graph, n:Node) : PRE(!exists(n' in g.nodes | n'.id==n.id))
OP add-edge!(g:Graph, e:Edge) : PRE(get-node(g,e.from)!=nil && get-node(g,e.to)!=nil)
OP causal-subgraph(g:Graph, target:Object) -> [Node] : traverse_incoming(:causal, target); INV(deterministic_order, cycle_safe)
OP associated-evals(g:Graph, id:Object) -> [Eval] : traverse_outgoing(:eval, id)
OP project-context(g:Graph, store:Store, target:Object, inc-evals:Boolean) -> [ContextNode] : nodes=causal-subgraph(g,target); map(n->{id:n.id, type:n.type, content:store.load(n.payload-ref), feedbacks:(inc-evals?associated-evals(g,n.id):[])}); INV(read_only_g)
OP canonical-prompt(ctx:[ContextNode]) -> String : serialize(ctx); INV(deterministic_serialization)
OP build-prefill-state(g:Graph, store:Store, target:Object, opts:{inc-evals:Boolean, builder:(ctx)->String}) -> PrefillState : ctx=project-context(g,store,target,opts.inc-evals); prompt=(opts.builder||canonical-prompt)(ctx); hash=SHA256(prompt); return{context:ctx, target-id:target, hash}; PRE(builder returns String)

INV Determinism: inputs(g,store,builder,target)==inputs' -> output.hash==output'.hash
INV CausalIntegrity: PrefillState.context derived exclusively from :causal edges
INV EvalIsolation: Evaluation data is optional metadata; disjoint from causal ancestry logic