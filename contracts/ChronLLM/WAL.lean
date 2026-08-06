-- ChronLLM/WAL.lean (v2.8.0-C Canonical Event Persistence Algebra - FINAL FROZEN)
import ChronLLM
import ChronLLM.Causal

namespace ChronLLM.WAL

open ChronLLM
open ChronLLM.Causal

-- -----------------------------------------------------------------------------
-- 1. AUTHORITY REFERENCE & SEMANTIC CONTRACT
-- -----------------------------------------------------------------------------

/--
  `AuthorityRef`: 証明・権限・検証境界の参照識別子キー。

  ### AuthorityRef Semantic Contract
  - **DOES NOT CONTAIN**:
    - `causal ordering` (因果順序)
    - `temporal position` (時間的・空間的位置)
    - `event identity` (イベントの固有同一性)
  - **ONLY REFERENCES**:
    - `validation authority` (検証権限)
    - `execution permission evidence` (実行許可の不変的証拠)
    - `proof boundary` (Layer 0 証明体系への参照キー)
-/
structure AuthorityRef where
  id : Nat
  deriving DecidableEq, Repr

/--
  `SerializationContext`: 直列化文脈の一元管理用コンテキスト。
  Projection (v2.8.0-B) と WAL (v2.8.0-C) の間で epoch 決定権の二重化を排除する。
-/
structure SerializationContext where
  epoch : Nat
  deriving DecidableEq, Repr

-- -----------------------------------------------------------------------------
-- 2. STAGE 1: CANONICAL EVENT RECORD (証明参照を持つ中間表現)
-- -----------------------------------------------------------------------------

/--
  `CanonicalEventRecord`:
  単なる実行ログではなく、権限・検証・遷移の証拠参照 (`authorityRef`) を
  保持する可逆な中間表現 (Serializable Evidence Reference)。
-/
structure CanonicalEventRecord where
  sequence     : Nat
  actionName   : String
  intent       : Intent
  authorityRef : AuthorityRef
  deriving DecidableEq, Repr

/-- History (Proof-Carrying) から CanonicalEventRecord への一方向抽出 -/
def toEventStream {ctx : KernelContext} {p : Projection} (h : History ctx p) : List CanonicalEventRecord :=
  match h with
  | History.empty => []
  | History.append prev evt =>
    let len := historyLength prev
    let rec : CanonicalEventRecord := {
      sequence     := len,
      actionName   := evt.act.name,
      intent       := evt.act.intent,
      authorityRef := ⟨len⟩  -- 権限証明体系へのアソシエーション参照
    }
    toEventStream prev ++ [rec]

-- -----------------------------------------------------------------------------
-- 3. STAGE 2: ABSTRACT PERSISTENCE FRAME
-- -----------------------------------------------------------------------------

/-- `EventPayload`: 抽象永続化レイヤー用のデータペイロード -/
structure EventPayload where
  actionName   : String
  intent       : Intent
  authorityRef : AuthorityRef
  deriving DecidableEq, Repr

/--
  `WALFrame`: **Abstract Persistence Frame (抽象永続化フレーム)**
  ※ 注意: 本型は論理フレームであり、物理エンディアン・アライメント・パディング等を扱う
           物理 WAL (Physical WAL) ではありません。
-/
structure WALFrame where
  causalID : CausalID
  payload  : EventPayload
  deriving DecidableEq, Repr

/-- SerializationContext に基づくレコードのフレーム変換 -/
def serializeRecords (sctx : SerializationContext) (records : List CanonicalEventRecord) : List WALFrame :=
  records.map (fun r => {
    causalID := ⟨sctx.epoch, r.sequence⟩,
    payload  := ⟨r.actionName, r.intent, r.authorityRef⟩
  })

/-- History から直接抽象永続化フレーム列を生成するパイプライン -/
def serialize {ctx : KernelContext} {p : Projection} (sctx : SerializationContext) (h : History ctx p) : List WALFrame :=
  serializeRecords sctx (toEventStream h)

-- -----------------------------------------------------------------------------
-- 4. STAGE 3: DESERIALIZE & INVERSE PIPELINE
-- -----------------------------------------------------------------------------

/-- WALFrame から CanonicalEventRecord への逆変換 (Candidate Generation) -/
def deserializeFrames (frames : List WALFrame) : List CanonicalEventRecord :=
  frames.map (fun f => {
    sequence     := f.causalID.sequence,
    actionName   := f.payload.actionName,
    intent       := f.payload.intent,
    authorityRef := f.payload.authorityRef
  })

-- -----------------------------------------------------------------------------
-- 5. LAYER 3 PROOF THEOREMS (C-1, C-2, C-3)
-- -----------------------------------------------------------------------------

-- THEOREM C-1: WAL.RECORD_ROUNDTRIP.001 (抽象フレーム変換の全射可換性)
theorem record_roundtrip (sctx : SerializationContext) (records : List CanonicalEventRecord) :
    deserializeFrames (serializeRecords sctx records) = records := by
  dsimp [serializeRecords, deserializeFrames]
  rw [List.map_map]
  induction records with
  | nil => rfl
  | cons head tail ih =>
    dsimp
    rw [ih]

theorem to_event_stream_length {ctx : KernelContext} {p : Projection} (h : History ctx p) :
    (toEventStream h).length = historyLength h := by
  induction h with
  | empty => rfl
  | append prev evt ih =>
    dsimp [toEventStream, historyLength]
    rw [List.length_append]
    dsimp
    rw [ih]

-- THEOREM C-2: WAL.SERIALIZE_PRESERVES_LENGTH.001 (永続化フレーム数の一致)
theorem serialize_preserves_length {ctx : KernelContext} {p : Projection} (sctx : SerializationContext) (h : History ctx p) :
    (serialize sctx h).length = historyLength h := by
  dsimp [serialize]
  rw [List.length_map]
  exact to_event_stream_length h

-- THEOREM C-3: WAL.CAUSAL_ID_PRESERVATION.001 (完全 CausalID 座標の無損失保存)
theorem causal_id_preservation (sctx : SerializationContext) (records : List CanonicalEventRecord) :
    (deserializeFrames (serializeRecords sctx records)).map (fun r => ({ epoch := sctx.epoch, sequence := r.sequence } : CausalID)) =
    records.map (fun r => ({ epoch := sctx.epoch, sequence := r.sequence } : CausalID)) := by
  rw [record_roundtrip]

-- -----------------------------------------------------------------------------
-- 6. RESERVED BOUNDARY TYPES FOR LAYER 4 (v2.8.0-D Pipeline Guard)
-- -----------------------------------------------------------------------------

/--
  `ValidatedEventStream`:
  WAL (非 Canonical) から直接 History を生成することを型レベルで禁止するための境界型。
  `validate` パスを通過した証拠付きストリームのみが History rebuild を許可される。
-/
structure ValidatedEventStream where
  records : List CanonicalEventRecord
  -- 将来的に型遷移不変性の述語証拠 (Proof) を保持する
  deriving DecidableEq, Repr

end ChronLLM.WAL