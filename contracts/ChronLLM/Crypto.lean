-- ChronLLM/Crypto.lean (v2.9.4 Lean 4 Compile Closure)
import ChronLLM
import ChronLLM.Replay

namespace ChronLLM.Crypto

open ChronLLM
open ChronLLM.Replay

universe u v

-- -----------------------------------------------------------------------------
-- AA-0: SPEC-PACKED TYPED COMMITMENTS & UNIVERSE-POLYMORPHIC SCHEMES
-- -----------------------------------------------------------------------------

inductive HashAlgorithm where
  | sha256
  | blake3
  deriving DecidableEq, Repr

structure CommitmentSpec where
  algorithm : HashAlgorithm
  domainTag : String
  deriving DecidableEq, Repr

structure RawHashCommitment (spec : CommitmentSpec) where
  digest       : ByteArray
  valid_length : digest.size = 32
  deriving Repr, DecidableEq

/--
  `TypedHashCommitment` (v2.9.4 UNIVERSE POLYMORPHIC):
  `α : Type v` により `History` (`Type (u + 1)`) のハッシュ化に伴う Universe Mismatch を防止。
-/
structure TypedHashCommitment (α : Type v) (spec : CommitmentSpec) where
  raw : RawHashCommitment spec
  deriving Repr, DecidableEq

class HashScheme (α : Type v) (spec : CommitmentSpec) where
  hash : α → TypedHashCommitment α spec

-- -----------------------------------------------------------------------------
-- AA-1: CRYPTOGRAPHIC BOUNDARY & API ALIAS
-- -----------------------------------------------------------------------------

namespace Internal

structure CertificateData {kctx : KernelContext} {PM : ProjectionModel}
    {initial final : PM.Projection} {cctx : CausalContext}
    (spec : CommitmentSpec)
    (result : ReplayResult PM initial final cctx) where
  commitment : TypedHashCommitment (History PM initial final) spec

end Internal

/--
  `CryptographicCertificate`:
  `Internal.CertificateData` への完全透明な型エイリアス（API エイリアス）。
-/
abbrev CryptographicCertificate {kctx : KernelContext} {PM : ProjectionModel}
    {initial final : PM.Projection} {cctx : CausalContext}
    (spec : CommitmentSpec)
    (result : ReplayResult PM initial final cctx) : Type :=
  Internal.CertificateData spec result

/--
  `sealReplay`:
  `ReplayResult` の `History` からコミットメントを生成する標準公開 API。
-/
def sealReplay {kctx : KernelContext} {PM : ProjectionModel}
    {initial final : PM.Projection} {cctx : CausalContext}
    {spec : CommitmentSpec} [HashScheme (History PM initial final) spec]
    (result : ReplayResult PM initial final cctx) :
    CryptographicCertificate spec result :=
  { commitment := HashScheme.hash result.history }

end ChronLLM.Crypto