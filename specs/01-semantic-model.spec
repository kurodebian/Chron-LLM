MODULE SemanticModel
DEFINES SpecOS::SemanticUniverse

-- ================================================================
-- 0. SCOPE OF SEMANTIC MODEL
-- ================================================================

SemanticModel defines the fundamental ontology of SpecOS.

It SHALL define:

- Event
- State
- Worldline
- Replay
- Projection

SemanticModel SHALL NOT:

- define authority
- define commit semantics
- define runtime execution
- define kernel execution
- define agent reasoning


-- ================================================================
-- 1. IDENTIFIERS
-- ================================================================

TYPE EventID =
  IDType(NamespacedID("event"))

TYPE StateID =
  IDType(NamespacedID("state"))

TYPE WorldlineID =
  IDType(NamespacedID("worldline"))


-- ================================================================
-- 2. EVENT MODEL
-- ================================================================

ENTITY Event {

  event_id :
    EventID

  payload :
    Expression

  timestamp :
    LogicalClock

  origin :
    Expression
}

INVARIANT EVENT_01:
Event MUST be immutable.

INVARIANT EVENT_02:
Event MUST NOT define authority.


-- ================================================================
-- 3. STATE MODEL
-- ================================================================

ENTITY State {

  state_id :
    StateID

  content :
    Expression
}

INVARIANT STATE_01:
State is a projection of applied Events.

INVARIANT STATE_02:
State MUST NOT define authority.


-- ================================================================
-- 4. WORLDLINE MODEL
-- ================================================================

ENTITY Worldline {

  worldline_id :
    WorldlineID

  events :
    List<Reference<Event>>
}

INVARIANT WORLDLINE_01:
Worldline MUST preserve event ordering.

INVARIANT WORLDLINE_02:
Worldline MUST NOT mutate Events.

INVARIANT WORLDLINE_03:
Worldline MUST NOT define authority.


-- ================================================================
-- 5. REPLAY MODEL
-- ================================================================

OPERATION Replay {

  input :
    Worldline

  output :
    State
}

INVARIANT REPLAY_01:
Replay MUST be deterministic.

INVARIANT REPLAY_02:
Replay MUST equal Fold(ApplyEvent, Worldline.events).

INVARIANT REPLAY_03:
Replay MUST NOT define authority.


-- ================================================================
-- 6. PROJECTION MODEL
-- ================================================================

OPERATION Projection {

  input :
    State

  view :
    Expression

  output :
    Expression
}

INVARIANT PROJECTION_01:
Projection MUST NOT mutate State.

INVARIANT PROJECTION_02:
Projection MUST NOT define authority.


-- ================================================================
-- 7. SEMANTIC MODEL INVARIANTS
-- ================================================================

INVARIANT SEM_01:
SemanticModel MUST NOT define Commit.

INVARIANT SEM_02:
SemanticModel MUST NOT define CanonicalState.

INVARIANT SEM_03:
SemanticModel MUST NOT define Branch or Merge.

INVARIANT SEM_04:
SemanticModel MUST NOT define Runtime or Kernel behavior.

INVARIANT SEM_05:
SemanticModel defines ontology only.
