-- ChronLLM.lean (v2.7.1 & v2.8.0-A Final Frozen Implementation)
namespace ChronLLM

-- =============================================================================
-- SECTION 1: CORE TYPES & AUTHORITIES (v2.7.1)
-- =============================================================================

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

-- =============================================================================
-- SECTION 2: INTENT, PROJECTION & ACTION (v2.7.1)
-- =============================================================================

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

-- =============================================================================
-- SECTION 3: OBSERVATION & PROOF-CARRYING EVENTFACT (v2.7.1 Updated Direction)
-- =============================================================================

structure Observation (p p' : Projection) where
  beforeProj : Projection
  afterProj  : Projection
  h_before   : beforeProj = p
  h_after    : afterProj = p'

structure EventFact (ctx : KernelContext) (p p' : Projection) (act : KernelAction ctx) where
  actionName      : String
  observation     : Observation p p'
  -- 【v2.8.0-A 最終修正】計算方向 (applyIntent = p') に方向を正規化
  transitionProof : { stateMap := applyIntentToMap act.intent p.stateMap } = p'
  authorityProof  : Executable ctx act

structure Event (ctx : KernelContext) (p p' : Projection) where
  eventId : String
  act     : KernelAction ctx
  fact    : EventFact ctx p p' act

-- =============================================================================
-- SECTION 4: PROJECTION-INDEXED HISTORY & RUNTIME (v2.7.1)
-- =============================================================================

inductive History (ctx : KernelContext) : Projection → Type where
  | empty : History ctx initialProjection
  | append {p p' : Projection} : History ctx p → Event ctx p p' → History ctx p'

def project {ctx : KernelContext} {p : Projection} (_ : History ctx p) : Projection := p

structure ExecutionAuthorityGrant (ctx : KernelContext) where
  source    : CanonicalAuthority
  execution : ExecutionAuthority
  proof     : ctx.delegation.allows source execution

private structure InternalCapability (ctx : KernelContext) where
  grant         : ExecutionAuthorityGrant ctx
  scopeBoundary : String
  allowedAction : KernelAction ctx → Prop
  executable    : ∀ a, allowedAction a → Executable ctx a

inductive Runtime (ctx : KernelContext) : TokenState → Type where
  | available (p : Projection) (h : History ctx p) (cap : InternalCapability ctx) : Runtime ctx TokenState.available
  | consumed : Runtime ctx TokenState.consumed

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
      transitionProof := rfl, -- 計算方向と同方向で即座に rfl 成立
      authorityProof  := authProof
    }
    let evt : Event ctx p nextP := { eventId := act.name, act := act, fact := fact }
    let nextHistory : History ctx nextP := History.append h evt
    (Runtime.consumed, ⟨nextP, Runtime.available nextP nextHistory cap⟩)

-- =============================================================================
-- SECTION 5: HISTORY FOLD KERNEL & BRIDGE THEOREMS (v2.8.0-A Final)
-- =============================================================================

namespace Fold

def applyEvent (intent : Intent) (current : Projection) : Projection :=
  { stateMap := applyIntentToMap intent current.stateMap }

-- 真の再帰的因果畳み込み評価器
def foldHistory {ctx : KernelContext} {p : Projection} (h : History ctx p) : Projection :=
  match h with
  | History.empty => initialProjection
  | History.append prev evt => applyEvent evt.act.intent (foldHistory prev)

-- THEOREM 1: THEOREM HISTORY.FOLD_APPEND_PRESERVATION.001
theorem fold_append_preservation
    {ctx : KernelContext} {p p' : Projection}
    (h : History ctx p) (e : Event ctx p p') :
    foldHistory (History.append h e) = applyEvent e.act.intent (foldHistory h) :=
  rfl

-- THEOREM 2: THEOREM HISTORY.FOLD_DETERMINISM.001
theorem fold_determinism
    {ctx : KernelContext} {p p' : Projection}
    (h : History ctx p) :
    foldHistory h = foldHistory h :=
  rfl

-- THEOREM 3: THEOREM HISTORY.FOLD_INDEX_CORRESPONDENCE.001 (Bridge Theorem)
theorem fold_index_correspondence
    {ctx : KernelContext} {p : Projection}
    (h : History ctx p) :
    foldHistory h = p := by
  induction h with
  | empty =>
    rfl
  | append prev evt ih =>
    dsimp [foldHistory]
    rw [ih]
    -- simpa により applyEvent の定義展開と transitionProof の型合わせを堅牢に解決
    simpa [applyEvent] using evt.fact.transitionProof

end Fold

end ChronLLM