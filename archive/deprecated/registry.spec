// ============================================================================
// [DEPRECATED / SUPERSEDED]
// This file is no longer active. Logic has been migrated to:
//   docs/spec/ir/R2.0-B_C_World_Runtime_Observation_Contract_v1.0.spec
// ============================================================================

TYPES: ID=Int|Str; State={inactive,active,archived}; World={id:ID,state:State}; Registry={worlds:[(ID,World)],ancestry:[(ID,ID)],active-id:ID|NIL,graph:Graph,memory:Memory}
OPS: find-world(r:Registry,i:ID)->w:World|NIL : assoc r.worlds i; list-worlds(r:Registry)->[World] : map cdr r.worlds; active-world(r:Registry)->w:World|NIL : find-world r r.active-id
INTERNALS: %shared-p(w:World,r:Registry)->Bool : eq(w.graph,r.graph)&&eq(w.memory,r.memory)
REGISTER-WORLD(r:Registry,w:World,p?:ID|NIL)->w':World PRE: world-p(w),!assoc(r.worlds,w.id),%shared-p(w,r),(p?!=NIL->assoc(r.worlds,p?)) POST: r'.worlds=append(r.worlds,[(w.id,w)]);if p?!=NIL then r'.ancestry=append(r.ancestry,[(w.id,p?)]);if r.graph==NIL then r'.graph=w.graph;r'.memory=w.memory
SET-ACTIVE-WORLD(r:Registry,w:World)->w':World PRE: assoc(r.worlds,w.id),w.state!=archived POST: let old=r.active-id;if old!=NIL&&old!=w.id then set-state(find-world(r,old),inactive);set-state(w,active);r'.active-id=w.id
ARCHIVE-WORLD(r:Registry,w:World)->w':World PRE: assoc(r.worlds,w.id) POST: set-state(w,archived);if r.active-id==w.id then r'.active-id=NIL
INVARIANTS: I1:unique(map car r.worlds);I2:order_preserved(r.worlds);I3:!w in r.worlds:eq(w.graph,r.graph)&&eq(w.memory,r.memory);I4:!(c,p) in r.ancestry:assoc(r.worlds,p);I5:count(filter(r.worlds,state=active))<=1;I6:!w in r.worlds:w.state==archived->w.id!=r.active-id
LIFECYCLE: register->inactive;set-active(inactive|active)->active;archive(active|inactive)->archived;forbidden:archived->active