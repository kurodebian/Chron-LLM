# abi-registry.spec
SPEC: ABIRegistry
VERSION: 1.1.5

USES:
  BaseTypes
  BaseInvariants
  BaseExcludes

DESCRIPTION:
  Interpretation Authority の中央管理仕様。
  Definitional Equality (`rfl`) で完結する Free Monoid Catamorphism。

TYPES:
  TYPE EventType   = String
  TYPE EventSchema = String
  TYPE ABIOpKind   = RegisterABI

  TYPE EventABI = {
    event_type : EventType,
    version    : Version,
    schema     : EventSchema
  }

  TYPE ABIRegistryEvent = {
    op  : ABIOpKind,
    abi : EventABI
  }

  TYPE ABIRegistryHistory =
      EmptyHistory
    | AppendHistory(
        previous : ABIRegistryHistory,
        event    : ABIRegistryEvent
      )

  TYPE ABIRegistrySnapshot = List<EventABI>

  TYPE HistoryTransition = {
    before : ABIRegistryHistory,
    after  : ABIRegistryHistory,
    op     : ABIRegistryEvent
  }

  TYPE ABIRegistrationError = VersionConflict | DuplicateABI | InvalidSchema
  TYPE ABIResolutionError   = ABINotFound | CorruptedSchema

STATE:
  RegistryHistory   : ABIRegistryHistory
  RegistryAuthority : InterpretationAuthority

OPERATIONS:
  DEF empty_history() -> ABIRegistryHistory = EmptyHistory

  DEF append_history(
    history : ABIRegistryHistory,
    event   : ABIRegistryEvent
  ) -> ABIRegistryHistory = AppendHistory(history, event)

  DEF apply_event(
    snapshot : ABIRegistrySnapshot,
    event    : ABIRegistryEvent
  ) -> ABIRegistrySnapshot

  DEF fold_history(
    history : ABIRegistryHistory,
    initial : ABIRegistrySnapshot,
    folder  : Function
  ) -> ABIRegistrySnapshot =
    MATCH history WITH
      EmptyHistory          => initial
    | AppendHistory(h, e)   => folder(fold_history(h, initial, folder), e)

  DEF project_registry(
    history : ABIRegistryHistory
  ) -> ABIRegistrySnapshot =
    fold_history(history, [], apply_event)

THEOREMS:
  THEOREM ABI.PROJ.CATAMORPHISM.001:
    project_registry(EmptyHistory) == []
    PROOF BY rfl

  THEOREM ABI.PROJ.CATAMORPHISM.002:
    ∀ h e, project_registry(AppendHistory(h, e)) == apply_event(project_registry(h), e)
    PROOF BY rfl

INVARIANTS:
  INV_DEF ABI.REG.001: registry_history_append_only(t : HistoryTransition)
    THEOREM: t.after == AppendHistory(t.before, t.op)

EXCLUDES:
  EXCLUDE: WallClockTime
  EXCLUDE: MutableGlobal
  EXCLUDE: ExternalIO

CONFORMANCE:
  ASSERT: ∀ t : HistoryTransition, registry_history_append_only(t)