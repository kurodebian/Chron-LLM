MOD: CycleDetection
T: State=ID | Path=[State] | Cycle=[State] | Graph={nodes:[State], edges:[(State,State)]}
F: find-cycle(Path)->Cycle | find-recurrent-cycle(Graph,State,Int)->Cycle

ALG(find-cycle):
  rev=reverse(path)
  t=rev[0]
  i=index(t, rev[1:])
  IF i>=0: RETURN reverse(rev[0..i+1])
  ELSE: RETURN [t]

ALG(find-recurrent-cycle):
  p=rollout*(graph, start, steps)
  c=find-cycle(p)
  RETURN reverse(c)

INV:
  INV-1: ret ∈ [State]
  INV-2: pure_analysis
  INV-3: deterministic
  INV-4: no_graph_mutation

CONST:
  anchor=last_node
  multi_cycle=False
  min_len=1