-- ChronLLM/HistoryFold.lean (v2.8.0-A Final - History Fold Kernel)
import ChronLLM.Internal

namespace ChronLLM.Fold

open ChronLLM.Internal

-- 1. Intent Application Operator (過去状態に対する実計算演算子)
def applyEvent (intent : Intent) (current : Projection) : Projection :=
  { stateMap := applyIntentToMap intent current.stateMap }

-- 2. Dynamic History Fold (真の再帰的因果畳み込み評価器)
-- 過去の評価結果 (foldHistory prev) に対して Intent の状態更新を順次計算適用する
def foldHistory {ctx : KernelContext} {p : Projection} (h : History ctx p) : Projection :=
  match h with
  | History.empty => initialProjection
  | History.append prev evt => applyEvent evt.act.intent (foldHistory prev)

-- -----------------------------------------------------------------------------
-- 3. CORE THEOREMS
-- -----------------------------------------------------------------------------

-- THEOREM HISTORY.FOLD_APPEND_PRESERVATION.001
-- (Append 操作に対する Fold の畳み込み計算保存)
theorem fold_append_preservation
    {ctx : KernelContext} {p p' : Projection}
    (h : History ctx p) (e : Event ctx p p') :
    foldHistory (History.append h e) = applyEvent e.act.intent (foldHistory h) :=
  rfl

-- THEOREM HISTORY.FOLD_DETERMINISM.001
-- (評価器の確定性)
theorem fold_determinism
    {ctx : KernelContext} {p p' : Projection}
    (h : History ctx p) :
    foldHistory h = foldHistory h :=
  rfl

-- THEOREM HISTORY.FOLD_INDEX_CORRESPONDENCE.001
-- (主定理: 動的畳み込み計算 foldHistory h と 静的型インデックス p の一致証明)
theorem fold_index_correspondence
    {ctx : KernelContext} {p : Projection}
    (h : History ctx p) :
    foldHistory h = p := by
  induction h with
  | empty =>
    -- Base Case: initialProjection への約元一致
    rfl
  | append prev evt ih =>
    -- Step Case: 過去の評価値 (foldHistory prev) に対する applyEvent の展開
    dsimp [foldHistory, applyEvent]
    -- 帰納法の仮定 (ih : foldHistory prev = p) を適用して過去状態を型インデックス p に置き換える
    rw [ih]
    -- EventFact に内包された証明 (transitionProof : p' = { stateMap := applyIntentToMap ... p.stateMap })
    -- を用いて、計算結果が遷移先型インデックス p' に等しいことを直交証明
    exact evt.fact.transitionProof.symm

end ChronLLM.Fold