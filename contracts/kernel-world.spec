# kernel-world.spec
SPEC: KernelWorld
VERSION: 2.7.1
FINAL_FROZEN: True

DESCRIPTION:
  Chron-LLM 核心仕様 (Layer 0 Frozen Specification)。
  【v2.7.1】Proof-Carrying Indexed Affine Causal Calculus Specification。
  - State Correctness + Authority Correctness を内包する EventFact
  - Terminal Consumed Runtime (No Index/No Resource)
  - Explicit Parameterized Runtime.available
  - Sigma-Typed Transition API

TYPES:
  TYPE Nat    = NativeNat
  TYPE String = NativeString

  ENUM TokenState = Available | Consumed

  ENUM AuthorityKind = CausalKind | InterpretationKind | ExecutionKind | ObservationKind

  TYPE Authority(k : AuthorityKind) = { id : Nat }
  TYPE ExecutionAuthority      = Authority(ExecutionKind)
  TYPE CausalAuthority         = Authority(CausalKind)
  TYPE InterpretationAuthority = Authority(InterpretationKind)

  TYPE CanonicalAuthority = {
    causal         : CausalAuthority,
    interpretation : InterpretationAuthority
  }

  TYPE DelegationGraph = {
    allows : CanonicalAuthority -> ExecutionAuthority -> Prop
  }

  TYPE KernelContext = {
    delegation : DelegationGraph
  }

  ENUM Intent =
      MutateState(key : String, value : String)
    | DelegateAuthority(source : CanonicalAuthority, target : ExecutionAuthority)

  TYPE Projection = {
    state_map : List<(String, String)>
  }

  TYPE KernelAction(ctx : KernelContext) = {
    name   : String,
    intent : Intent
  }

  TYPE Executable(ctx : KernelContext, action : KernelAction(ctx)) : Prop

  # 1. Dependent Observation & Proof-Carrying EventFact (State + Authority Proof)
  TYPE Observation(p1 : Projection, p2 : Projection) = {
    before_proj : Projection,
    after_proj  : Projection,
    h_before    : before_proj == p1,
    h_after     : after_proj  == p2
  }

  TYPE EventFact(ctx : KernelContext, p1 : Projection, p2 : Projection, act : KernelAction(ctx)) = {
    action_name      : String,
    obs              : Observation(p1, p2),
    transition_proof : p2 == apply_intent(act.intent, p1),
    authority_proof  : Executable(ctx, act)
  }

  TYPE Event(ctx : KernelContext, p1 : Projection, p2 : Projection) = {
    event_id : String,
    act      : KernelAction(ctx),
    fact     : EventFact(ctx, p1, p2, act)
  }

  # 2. Inductive History GADT (Indexed by Projection)
  INDUCTIVE History(ctx : KernelContext) : Projection -> Type =
      Empty : History(ctx, initialProjection)
    | Append(p1 p2 : Projection, prev : History(ctx, p1), evt : Event(ctx, p1, p2)) : History(ctx, p2)

  # 3. Internal Capability
  TYPE InternalCapability(ctx : KernelContext) = {
    grant          : CanonicalAuthority,
    scope_boundary : String,
    allowed_action : KernelAction(ctx) -> Prop,
    executable     : Forall(a : KernelAction(ctx), allowed_action(a) -> Executable(ctx, a))
  }

  # 4. Runtime Inductive Family
  INDUCTIVE Runtime(ctx : KernelContext) : TokenState -> Type =
      Available(p : Projection, h : History(ctx, p), cap : InternalCapability(ctx)) : Runtime(ctx, TokenState.Available)
    | Consumed : Runtime(ctx, TokenState.Consumed)

OPERATIONS:
  OP project(ctx : KernelContext, p : Projection, h : History(ctx, p)) -> Projection

  OP step_runtime(
    ctx       : KernelContext,
    rt        : Runtime(ctx, TokenState.Available),
    act       : KernelAction(ctx),
    h_allowed : Proof
  ) -> (
    Runtime(ctx, TokenState.Consumed) *
    Sigma(p' : Projection, Runtime(ctx, TokenState.Available))
  )

# -----------------------------------------------------------------------------
# LAYER 0 THEOREMS
# -----------------------------------------------------------------------------
THEOREMS:
  # 1. History Index Consistency
  THEOREM HISTORY.INDEX_HOMOMORPHISM.001:
    ∀ (ctx : KernelContext) (p : Projection) (h : History(ctx, p)),
    project(ctx, p, h) == p

  # 2. Transition State Determinism
  THEOREM RUNTIME.TRANSITION_INDEX_CORRECTNESS.001:
    ∀ (ctx : KernelContext) (rt : Runtime(ctx, TokenState.Available)) (act : KernelAction(ctx)) (h_allowed : Proof),
    let (_, <nextP, nextRt>) = step_runtime(ctx, rt, act, h_allowed);
    nextP == apply_intent(act.intent, rt.p)