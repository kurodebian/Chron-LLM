TYPES
  Bool = t | nil
  Str, Int, Map<K,V>, List[T]
  Node { id: Str }
  Edge { src: Node, dst: Node }
  Graph { nodes: [Node], edges: [Edge] }
  Store {}
  Registry { worlds: [World], active_id: Str, ancestry: Map<Str, Str> }
  World { id: Str, root_node: Node, head_node: Node, policy: Policy, meta: Meta, lifecycle: Lifecycle }

  WOBS { schema_version: Int, world_id: Str, ... }
  ROBS { world_ids: [Str], active_id: Str, ... }
  AOBS { child_id: Str, parent_id: Str, path: [(Str . Str)] }
  DOBS { changed_p: Bool, changed_fields: [Str] }

UTILS
  %c-assert(cond: Bool, desc: Str) -> t | Error
    Pre: true
    Post: !cond -> Error(desc); cond -> t

  %c-fixture() -> (Graph, Store, Registry)
    State: G.nodes=["root","head"]; G.edges=[(root->head)]
    Returns: (G, S, R) bound(G,S)

TESTS
  d1-world-non-mutation() -> t | Error
    Setup: W = World(policy={include-evals:nil}, meta={label:"stable"})
    Op: Obs = describe-world(W)
    Assert: world-observation-p(Obs)
    Assert: W.id==W'.id & W.nodes==W'.nodes & W.policy==W'.policy & W.meta==W'.meta & W.lifecycle==W'.lifecycle
    Assert: Obs.schema_version == +observation-schema-version+

  d2-registry-non-mutation() -> t | Error
    Setup: R.worlds=["first","second"]; R.active_id="second"; R.archived=["first"]
    Op: Obs = describe-registry(R)
    Assert: registry-observation-p(Obs)
    Assert: R.worlds==R'.worlds & R.active_id==R'.active_id & R.ancestry==R'.ancestry

  d3-deterministic-observation() -> t | Error
    Setup: W, R
    Op1: O1=describe-world(W); O2=describe-world(W)
    Assert: O1.world_id == O2.world_id
    Op2: R1=describe-registry(R); R2=describe-registry(R)
    Assert: R1.world_ids == R2.world_ids

  d4-accurate-ancestry() -> t | Error
    Setup: P=World("parent"); C=World("child"); Link(P->C)
    Op: Anc = describe-ancestry(C)
    Assert: ancestry-observation-p(Anc)
    Assert: Anc.child_id=="child" & Anc.parent_id=="parent"
    Assert: Anc.path == [("child" . "parent")]

  d5-deterministic-difference() -> t | Error
    Setup: A, B (Obs)
    Op1: D=describe-diff(A,A)
    Assert: diff-observation-p(D) & D.changed_p==nil & D.changed_fields==[]
    Op2: D2=describe-diff(A,A)
    Assert: D == D2
    Op3: D3=describe-diff(WObs, RObs)
    Assert: D3.changed_p == t

  d6-representation-independence() -> t | Error
    Setup: W1(params="same"), W2(params="same") distinct instances
    Op: O1=describe-world(W1); O2=describe-world(W2)
    Assert: O1.world_id==O2.world_id & O1.root_node_id==O2.root_node_id

  d7-value-object-equality() -> t | Error
    Setup: Same as d6 (W1, W2 equivalent params)
    Op: O1=describe-world(W1); O2=describe-world(W2)
    Assert: equal(O1,O2)==t & world-observation-equal(O1,O2)==t

RUNNER
  run-r2-0-c-tests() -> t | Error
    Ops: For test in [d1..d7]: res=funcall(test); %c-assert(res!=nil)
    Returns: t

INVARIANTS (INV)
  Immutability: describe(X) -> X' s.t. X == X'
  Determinism: f(x)=y => f(x)=y
  SchemaCompliance: WOBS.schema_version == +observation-schema-version+
  AncestryAccuracy: AOBS.path reflects explicit edges
  DiffSemantics: diff(a,a).changed_p==nil; diff(TypeA,TypeB).changed_p==t
  ValueSemantics: equal(Obs1,Obs2) iff content(Obs1)==content(Obs2)