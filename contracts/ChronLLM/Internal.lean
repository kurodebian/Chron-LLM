-- ChronLLM/Internal.lean (v2.7.1 Final Frozen - Proof-Carrying Indexed Affine Causal Calculus)
namespace ChronLLM.Internal

-- 1. トークン状態と権限構造
inductive TokenState where
  | available
  | consumed
  deriving DecidableEq

inductive AuthorityKind where
  | causal
  | interpretation
  | execution
  | observation
  deriving DecidableEq

structure Authority (k : AuthorityKind) where
  id : Nat
  deriving DecidableEq

abbrev ExecutionAuthority      := Authority AuthorityKind.execution
abbrev CausalAuthority         := Authority AuthorityKind.causal
abbrev InterpretationAuthority := Authority AuthorityKind.interpretation

structure CanonicalAuthority where
  causal         : CausalAuthority
  interpretation : InterpretationAuthority

structure DelegationGraph where
  allows : CanonicalAuthority → ExecutionAuthority → Prop

structure KernelContext where
  delegation : DelegationGraph

-- 2. Intent, Projection, Action, Executable
inductive Intent where
  | mutateState (key : String) (value : String)
  | delegateAuthority (source : CanonicalAuthority) (target : ExecutionAuthority)
  deriving DecidableEq

structure Projection where
  stateMap : List (String × String)
  deriving DecidableEq

def initialProjection : Projection := { stateMap := [] }

def applyIntentToMap (intent : Intent) (m : List (String × String)) : List (String × String) :=
  match intent with
  | Intent.mutateState k v => (k, v) :: m
  | Intent.delegateAuthority _ _ => m

structure KernelAction (ctx : KernelContext) where
  name   : String
  intent : Intent

inductive Executable (ctx : KernelContext) : KernelAction ctx → Prop where
  | validAction (act : KernelAction ctx) : Executable ctx act

-- 3. Observation & EventFact (State Correctness + Authority Correctness)
structure Observation (p p' : Projection) where
  beforeProj : Projection
  afterProj  : Projection
  h_before   : beforeProj = p
  h_after    : afterProj = p'

structure EventFact (ctx : KernelContext) (p p' : Projection) (act : KernelAction ctx) where
  actionName      : String
  observation     : Observation p p'
  transitionProof : p' = { stateMap := applyIntentToMap act.intent p.stateMap }
  authorityProof  : Executable ctx act

structure Event (ctx : KernelContext) (p p' : Projection) where
  eventId : String
  act     : KernelAction ctx
  fact    : EventFact ctx p p' act

-- 4. Inductive History GADT (Projection-indexed)
inductive History (ctx : KernelContext) : Projection → Type where
  | empty : History ctx initialProjection
  | append {p p' : Projection} : History ctx p → Event ctx p p' → History ctx p'

def project {ctx : KernelContext} {p : Projection} (_ : History ctx p) : Projection := p

-- 5. InternalCapability
structure ExecutionAuthorityGrant (ctx : KernelContext) where
  source    : CanonicalAuthority
  execution : ExecutionAuthority
  proof     : ctx.delegation.allows source execution

private structure InternalCapability (ctx : KernelContext) where
  grant         : ExecutionAuthorityGrant ctx
  scopeBoundary : String
  allowedAction : KernelAction ctx → Prop
  executable    : ∀ a, allowedAction a → Executable ctx a

-- 6. Runtime Inductive Family (Available 引数の明示化 & Terminal Consumed)
inductive Runtime (ctx : KernelContext) : TokenState → Type where
  | available (p : Projection) (h : History ctx p) (cap : InternalCapability ctx) : Runtime ctx TokenState.available
  | consumed : Runtime ctx TokenState.consumed

-- 7. Affine State Transition API
def stepRuntime
    (ctx : KernelContext)
    (rt : Runtime ctx TokenState.available)
    (act : KernelAction ctx)
    (h_allowed : match rt with | Runtime.available _ _ cap => cap.allowedAction act) :
    (Runtime ctx TokenState.consumed) × 
    (Sigma (fun (p' : Projection) => Runtime ctx TokenState.available)) :=
  match rt with
  | Runtime.available p h cap =>
    let nextP : Projection := { stateMap := applyIntentToMap act.intent p.stateMap }
    let obs : Observation p nextP := { beforeProj := p, afterProj := nextP, h_before := rfl, h_after := rfl }
    let authProof : Executable ctx act := cap.executable act h_allowed
    let fact : EventFact ctx p nextP act := {
      actionName      := act.name,
      observation     := obs,
      transitionProof := rfl,
      authorityProof  := authProof
    }
    let evt : Event ctx p nextP := { eventId := act.name, act := act, fact := fact }
    let nextHistory : History ctx nextP := History.append h evt
    (Runtime.consumed, ⟨nextP, Runtime.available nextP nextHistory cap⟩)

end ChronLLM.Internal