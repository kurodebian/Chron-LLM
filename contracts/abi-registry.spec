# abi-registry.spec
SPEC: ABIRegistry
VERSION: 1.3.0

USES:
  BaseTypes

DESCRIPTION:
  Interpretation Authority の中央管理仕様。
  Definitional Equality (`rfl`) で完結する Catamorphism 仕様。

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

# LAYER 0: LEAN KERNEL MATHEMATICAL THEOREMS
THEOREMS:
  THEOREM ABI.PROJ.CATAMORPHISM.001:
    project_registry(EmptyHistory) == []
    PROOF BY rfl

  THEOREM ABI.PROJ.CATAMORPHISM.002:
    ∀ h e, project_registry(AppendHistory(h, e)) == apply_event(project_registry(h), e)
    PROOF BY rfl

# LAYER 1: REPOSITORY CONSTITUTION
POLICIES:
  POLICY: ABI.APPEND_ONLY.001
    DESCRIPTION: ABI 履歴の変更は常に末尾追加 (AppendHistory) のみによって行われなければならない。

# LAYER 2: BUILD & CI ENFORCEMENT
ENFORCEMENT:
  ENFORCE: CI.CATAMORPHISM_RFL_CHECK
    METHOD: Lean Compiler Check
    RULE: Confirm that projection theorems compile purely with `rfl`.