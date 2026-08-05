# pipeline-orchestration.spec
SPEC: PipelineOrchestration
VERSION: 1.1.1

USES:
  BaseTypes
  BaseInvariants
  BaseExcludes
  BaseHistory
  ABIRegistry

DESCRIPTION:
  ReplayContext を用いた決定論的オーケストレーション仕様。

TYPES:
  TYPE ProjectionOrigin =
      HistoryProjection
    | ABIProjection
    | SemanticProjection
    | GraphProjection

  TYPE DerivedData = Frozen<{
    representation : String,
    origin         : ProjectionOrigin
  }>

  TYPE ProjectionState = Frozen<{ data : DerivedData, authority : NonAuthoritative }>
  TYPE SemanticState   = Frozen<{ data : DerivedData, authority : NonAuthoritative }>
  TYPE GraphState      = Frozen<{ data : DerivedData, authority : NonAuthoritative }>

  TYPE PipelineState = Frozen<{
    projection_model : ProjectionState,
    semantic_model   : SemanticState,
    graph            : GraphState
  }>

  TYPE ReplayContext = Frozen<{
    history              : History,
    abi_snapshot         : ABIRegistrySnapshot,
    constitution_version : Version
  }>

  TYPE PipelineExecutionError = InvalidContext | StepExecutionFailed(String)

OPERATIONS:
  DEF execute_pipeline(
    ctx : ReplayContext
  ) -> Result<PipelineState, PipelineExecutionError>

INVARIANTS:

  INV_DEF PIPE.CORE.001: pure_stage_transformations(
    d_op         : Function,
    interpret_op : Function,
    graph_op     : Function
  )
    THEOREM: PUR-001(d_op) ∧ PUR-001(interpret_op) ∧ PUR-001(graph_op)

  INV_DEF PIPE.CORE.002: replay_context_deterministic(
    pipeline_op : Function,
    ctx1        : ReplayContext,
    ctx2        : ReplayContext
  )
    THEOREM: (ctx1 = ctx2) ⇒ (pipeline_op(ctx1) = pipeline_op(ctx2))

EXCLUDES:
  EXCLUDE: WallClockTime
  EXCLUDE: HiddenState
  EXCLUDE: MutableGlobal

CONFORMANCE:
  ASSERT: ∀ ctx state, (execute_pipeline(ctx) = Success(state)) ⇒ (state.projection_model.authority == NonAuthoritative)