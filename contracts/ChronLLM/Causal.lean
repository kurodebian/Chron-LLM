-- ChronLLM/Causal.lean (v2.8.0-B Final Frozen Edition)
import ChronLLM

namespace ChronLLM.Causal

open ChronLLM

-- 1. Causal Coordinate (正規線形位置座標)
structure CausalID where
  epoch    : Nat
  sequence : Nat
  deriving DecidableEq, Repr

-- 2. Event Identity (親参照リンク)
structure EventIdentity where
  causalID : CausalID
  parentID : Option CausalID
  deriving DecidableEq, Repr

-- 3. Identified Event Wrapper (Digest は v2.8.1 に留保)
structure IdentifiedEvent (ctx : KernelContext) (p p' : Projection) where
  identity : EventIdentity
  event    : Event ctx p p'

-- 4. Causal Identity Projection (位置情報のみを保持する Derived View)
structure CausalIdentityNode where
  identity   : EventIdentity
  actionName : String
  deriving DecidableEq, Repr

structure CausalIdentityProjection where
  sourceHistoryLength : Nat
  sourceEpoch         : Nat  -- [補正箇所] 座標系自体の出自エポック
  nodes               : List CausalIdentityNode
  deriving DecidableEq, Repr

-- 5. Projection Helper & Extraction Functions
def historyLength {ctx : KernelContext} {p : Projection} (h : History ctx p) : Nat :=
  match h with
  | History.empty => 0
  | History.append prev _ => historyLength prev + 1

def extractNodes {ctx : KernelContext} {p : Projection} (h : History ctx p) (epoch : Nat) : List CausalIdentityNode :=
  match h with
  | History.empty => []
  | History.append prev evt =>
    let len := historyLength prev
    let currentID : CausalID := ⟨epoch, len⟩
    let parentID  : Option CausalID := if len == 0 then none else some ⟨epoch, len - 1⟩
    let node : CausalIdentityNode := {
      identity   := ⟨currentID, parentID⟩,
      actionName := evt.act.name
    }
    extractNodes prev epoch ++ [node]

/-- Unidirectional Projection: History -> CausalIdentityProjection -/
def extractProjection {ctx : KernelContext} {p : Projection} (h : History ctx p) (epoch : Nat := 0) : CausalIdentityProjection := {
  sourceHistoryLength := historyLength h,
  sourceEpoch         := epoch,
  nodes               := extractNodes h epoch
}

-- -----------------------------------------------------------------------------
-- Core Theorems
-- -----------------------------------------------------------------------------

theorem extract_nodes_length {ctx : KernelContext} {p : Projection} (h : History ctx p) (epoch : Nat) :
    (extractNodes h epoch).length = historyLength h := by
  induction h with
  | empty => rfl
  | append prev evt ih =>
    dsimp [extractNodes, historyLength]
    rw [List.length_append]
    dsimp
    rw [ih]

theorem projection_length_matches_history {ctx : KernelContext} {p : Projection} (h : History ctx p) (epoch : Nat) :
    (extractProjection h epoch).nodes.length = (extractProjection h epoch).sourceHistoryLength := by
  dsimp [extractProjection]
  exact extract_nodes_length h epoch

end ChronLLM.Causal