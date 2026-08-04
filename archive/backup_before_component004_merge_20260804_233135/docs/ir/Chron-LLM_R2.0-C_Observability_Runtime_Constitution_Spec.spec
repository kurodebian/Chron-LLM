SPEC_ID=CHRON-R2.0-C-OBSERVABILITY-CONSTITUTION
REV=1.0
STATUS=DRAFT
LAYER=R2.0-C
DEPS=[R2.0-A, R2.0-B]

TYPES:
State={Kernel, Graph, Memory, World, Registry}
Observation={id:UUID, logical_time:T, snapshot:StateSnapshot}
StateSnapshot={world:WorldObs, registry:RegistryObs, kernel:KernelObs}
WorldObs={id:ID, head:NodeID, root:NodeID, policy:Policy, meta:Map, lifecycle:State, parent:ID?}
RegistryObs={worlds:[ID], active:ID, ancestry:Graph, archived:[ID]}
DiffResult={added:Set, removed:Set, modified:Set}

OPS:
observe(s:State)->o:Observation | PRE:true, POST:s==s'
diff(o1:Observation, o2:Observation)->d:DiffResult | PRE:true, POST:o1==o1', o2==o2'
get_world_obs(id:ID)->WorldObs
get_registry_obs()->RegistryObs

INVARIANTS:
INV_READ_ONLY: observe(s)->o | s==s'
INV_DETERMINISTIC: observe(s)==observe(s)
INV_ACCURATE: o.snapshot==snapshot(s)
INV_NO_SIDE_EFFECTS: observe(s)->o | !mutate(s)
INV_IMMUTABLE_OBS: created(o)->!mutate(o)
INV_NON_AUTH: truth==Kernel
INV_LAYER: Kernel->World->Obs->Presentation
INV_VALUE_OBJ: o1==o2 | o1.snapshot==o2.snapshot
INV_COMPLETE: o.snapshot contains all observable(s)
INV_NO_INFER: o.snapshot==actual(s) & !infer(o) & !synthesize(o) & !approx(o) & !fabricate(o) & !hide(o)
INV_PRESENTATION_INDEPENDENT: semantics(obs) independent of presentation_layer

CONSTRAINTS:
NO_DEPS=[WallClock, PID, ThreadID, MemAddr, RNG, OSTiming]
NO_MUTATION=[Graph, Memory, World, Registry, Kernel]
NO_EXEC: Observation contains no executable behavior
NO_MUTABLE_REFS: Observation contains no mutable references
NO_LAZY_MUT: Observation contains no lazy mutations
NO_HIDDEN_STATE: Observation contains no hidden state

LIFECYCLE:
Observation: Created->Consumed->Discarded

TESTS:
D1: observe(w)->o | w==w'
D2: observe(r)->o | r==r'
D3: observe(s)==observe(s)
D4: o.ancestry==runtime.ancestry
D5: diff(o1, o2)==diff(o1, o2)
D6: semantics(obs)==semantics(obs) | presentation
D7: created(o)->!mutate(o)

CONFORMANCE:
PASS=[INVARIANTS, TESTS]