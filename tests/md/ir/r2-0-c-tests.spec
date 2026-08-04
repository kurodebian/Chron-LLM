// ============================================================================
// CHRON-LLM R2.0-C OBSERVATION CONTRACT TEST SPECIFICATION
// Version: v1.0 (SSOT Harmonized)
// Target File: tests/md/ir/r2-0-c-tests.spec
// Single Source of Truth Alignment: chron-llm-r2-world-runtime-obs-v1.0
// ============================================================================

PKG chron-r2-0-c

TYPES:
  PayloadRef = { hash:SHA256, size:U64, storage:Enum{:memory, :disk, :remote} }
  MemStore = HashTable<Str, PayloadRef>
  Node = { id:ID, type:Kw, payload_ref:PayloadRef, causal_depth:U64, meta:Map }
  Edge = { from:ID, to:ID, type:Enum{:causal, :eval} }
  Graph = { nodes:Map<ID, Node>, edges:[Edge] }
  
  World = { id:ID, graph:Ref<Graph>, mem:Ref<MemStore>, root:ID, head:ID, policy:Map, meta:Map, lifecycle:Enum{:created, :active, :inactive, :archived} }
  Registry = { worlds:[World], ancestry:Map<ID, ID>, active:ID|NIL, graph:Ref<Graph>, mem:Ref<MemStore> }

  WorldObs = { ver:U16, world_id:ID, root_id:ID, head_id:ID, policy:Map, meta:Map, lifecycle:Enum{:created, :active, :inactive, :archived}, parent_id:ID|NIL }
  RegistryObs = { ver:U16, world_ids:[ID], active_id:ID|NIL, archived_ids:[ID] }
  AncestryObs = { world_id:ID, parent_id:ID|NIL, path:[ID] }
  DiffObs = { changed:Bool, fields:[Str] }

UTILS:
  %c-assert(cond:Bool, desc:Str) -> Bool | Error("R2.0-C invariant failed: ~A")
  %c-fixture() -> (g:Ref<Graph>, m:Ref<MemStore>, w:World, r:Registry, child:World)
    INIT g.nodes = {"root": {id:"root", type::root, payload_ref:{hash:"0", size:0, storage::memory}, causal_depth:0, meta:{}}};
         g.edges = [];
         m = make-memory-store();
         w = make-world("w-0", g, m, "root", "root", {}, {});
         r = register-world(new-registry(g, m), w);
         child = fork-world(w, "w-child");
         r' = register-world(r, child)

OPS:
  snapshot-world(w:World) -> WorldObs
  snapshot-registry(r:Registry) -> RegistryObs
  snapshot-ancestry(w:World) -> AncestryObs
  snapshot-diff(w1:World, w2:World) -> DiffObs

TESTS (Public Observation API Validation):
  c1-world-non-mutation() -> Bool
    POST: snapshot-world(w) => w' eq w AND obs.ver == 1 AND obs.world_id == w.id AND obs.root_id == w.root AND obs.head_id == w.head

  c2-registry-non-mutation() -> Bool
    POST: snapshot-registry(r) => r' eq r AND obs.ver == 1 AND obs.world_ids contains w.id AND obs.active_id == r.active

  c3-deterministic-observation() -> Bool
    POST: snapshot-world(w) == snapshot-world(w) AND snapshot-registry(r) == snapshot-registry(r)

  c4-accurate-ancestry() -> Bool
    POST: snapshot-ancestry(child).world_id == child.id AND snapshot-ancestry(child).parent_id == w.id AND snapshot-ancestry(child).path == [w.id, child.id]

  c5-deterministic-difference() -> Bool
    POST: snapshot-diff(w, w).changed == false AND snapshot-diff(w, w).fields == [] AND (snapshot-diff(w1, w2).changed == true IF w1.meta != w2.meta)

  c6-value-object-equality() -> Bool
    POST: equal(snapshot-world(w1), snapshot-world(w2)) == true IF (w1.id == w2.id AND w1.root == w2.root AND w1.head == w2.head AND w1.meta == w2.meta)

INVARIANTS (System Observation Contract Mapping):
  INV-5 (Obs-Primitive)       : All observation attributes MUST resolve strictly to primitive data types (null, bool, str, num, kw, list, map).
  INV-9 (Obs-Read-Only)       : Snapshot & Observation operations MUST NOT mutate World, Registry, or Graph state.
  INV_OBS_VER                 : Observation schema version MUST be fixed to version 1 (ver == 1).
  INV_OBS_DETERMINISM         : Equal state produces identical observation data (Pure Observation Function).