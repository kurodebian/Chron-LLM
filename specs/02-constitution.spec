MODULE Constitution
EXTENDS SemanticModel
DEFINES SpecOS::ConstitutionUniverse

-- ================================================================
-- 0. SCOPE OF CONSTITUTION
-- ================================================================

Constitution defines the fundamental laws that govern:

- Authority
- Mutation
- Causality
- Replay behavior

Constitution SHALL:

- define CanonicalState as authoritative state
- define Authority rels
- constrain how Events may mutate CanonicalState
- constrain Replay and Worldline behavior

Constitution SHALL NOT:

- define Commit semantics
- define Runtime behavior
- define Kernel execution
- define Agent reasoning


-- ================================================================
-- 1. IDENTIFIERS
-- ================================================================

TYPE CanonicalStateID =
  IDType(NamespacedID("canonical-state"))

TYPE AuthorityID =
  IDType(NamespacedID("authority"))


-- ================================================================
-- 2. CANONICAL STATE MODEL
-- ================================================================

ENTITY CanonicalState {

  canonical_id :
    CanonicalStateID

  content :
    Expression
}

INVARIANT CANON_01:
CanonicalState is the unique authoritative state
for a given world at a given logical time.

INVARIANT CANON_02:
CanonicalState MUST NOT be mutated directly.

INVARIANT CANON_03:
CanonicalState MAY change only through Event application.


-- ================================================================
-- 3. AUTHORITY MODEL
-- ================================================================

ENTITY Authority {

  authority_id :
    AuthorityID

  subject :
    Expression

  scope :
    Expression

  constraints :
    Expression
}

INVARIANT AUTH_01:
Authority MUST be derived from Constitution,
NOT from Runtime or Kernel.

INVARIANT AUTH_02:
Authority MUST NOT be redefined by SemanticModel.

INVARIANT AUTH_03:
Authority MUST NOT be redefined by Runtime or Kernel.


-- ================================================================
-- 4. MUTATION LAWS
-- ================================================================

LAW MutationRequiresEvent {

  FORALL s IN CanonicalState,
         s' IN CanonicalState =>

    (s != s') IMPLIES
      EXISTS e IN Event =>
        MutatedBy(s, s', e)
}

LAW MutationIsEventBound {

  FORALL s IN CanonicalState,
         s' IN CanonicalState,
         e IN Event =>

    MutatedBy(s, s', e) IMPLIES
      Applied(e, s, s')
}

INVARIANT MUT_01:
No CanonicalState change MAY occur
without an associated Event.

INVARIANT MUT_02:
Event MUST be the sole carrier of mutation.


-- ================================================================
-- 5. CAUSALITY LAWS
-- ================================================================

LAW EventCausalityOrder {

  FORALL wl IN Worldline,
         e1, e2 IN wl.events =>

    HappensBefore(e1, e2)
      IFF
    Position(e1, wl) < Position(e2, wl)
}

INVARIANT CAUSAL_01:
Worldline ordering defines causal precedence.

INVARIANT CAUSAL_02:
Causality MUST NOT be redefined by Runtime or Kernel.

INVARIANT CAUSAL_03:
Branch and Merge MUST preserve causal consistency
(extended in Chron Semantic Extension).


-- ================================================================
-- 6. REPLAY LAWS
-- ================================================================

LAW ReplayDeterminism {

  FORALL wl IN Worldline =>

    Replay(wl) =
      Fold(ApplyEvent, wl.events)
}

LAW ReplayUniqueness {

  FORALL wl IN Worldline,
         s1, s2 IN State =>

    Replay(wl) = s1
    AND Replay(wl) = s2
    IMPLIES s1 = s2
}

INVARIANT REPLAY_LAW_01:
Replay MUST be deterministic.

INVARIANT REPLAY_LAW_02:
Replay MUST produce exactly one State
for a given Worldline.

INVARIANT REPLAY_LAW_03:
Replay MUST NOT introduce new Events.


-- ================================================================
-- 7. PROJECTION LAWS
-- ================================================================

LAW ProjectionIsViewOnly {

  FORALL s IN State,
         v IN Expression =>

    Projection(s, v) DOES NOT mutate s
}

INVARIANT PROJ_LAW_01:
Projection MUST NOT change State.

INVARIANT PROJ_LAW_02:
Projection MUST NOT define authority.


-- ================================================================
-- 8. CONSTITUTIONAL BOUNDARY INVARIANTS
-- ================================================================

INVARIANT CONST_01:
Constitution MUST NOT define Commit.

INVARIANT CONST_02:
Constitution MUST NOT define Runtime scheduling.

INVARIANT CONST_03:
Constitution MUST NOT define Kernel execution steps.

INVARIANT CONST_04:
Constitution MUST define:

  - CanonicalState mutation laws
  - Causality laws
  - Replay determinism

INVARIANT CONST_05:
Any layer above Constitution
(Chron Extension, Runtime, Kernel)
MUST conform to these laws
and MUST NOT override them.
