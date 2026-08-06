-- ChronLLM/Authority.lean (v2.9.4 Lean 4 Compile Closure)
import ChronLLM
import ChronLLM.Causal

namespace ChronLLM.Authority

open ChronLLM
open ChronLLM.Causal

class SignatureScheme (M PubKey Sig : Type) where
  verify : PubKey → M → Sig → Prop

structure SignedAuthorityPayload where
  authorityRef  : AuthorityRef
  causalContext : CausalContext
  deriving Repr, DecidableEq

structure AuthorityEvidence (M PubKey Sig : Type) [SignatureScheme M PubKey Sig] where
  payload   : M
  pubKey    : PubKey
  signature : Sig
  verified  : SignatureScheme.verify pubKey payload signature

/--
  `AuthorityRegistry`:
  権限インデックスの有効性を判定する基底構造体。`ChronLLM.Causal.CausalContext` に依存。
-/
structure AuthorityRegistry where
  valid : CausalContext → AuthorityRef → Prop

/--
  `toCryptoRegistry`:
  署名証拠群から `AuthorityRegistry` を生成する独立関数。
-/
def toCryptoRegistry {PubKey Sig : Type} [SignatureScheme SignedAuthorityPayload PubKey Sig]
    (evidences : List (AuthorityEvidence SignedAuthorityPayload PubKey Sig)) : AuthorityRegistry where
  valid := fun cctx ref =>
    ∃ ev ∈ evidences,
      ev.payload.authorityRef = ref ∧
      ev.payload.causalContext = cctx ∧
      ev.verified

end ChronLLM.Authority