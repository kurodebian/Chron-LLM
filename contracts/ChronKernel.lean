-- ChronKernel.lean : Chron-LLM v1.1.5 Authority Sealing Layer

namespace ChronLLM

-- 1. Inductive Authority Universe (型レベル分離)
inductive AuthorityKind where
  | CausalKind
  | InterpretationKind
  | ExecutionKind
  | ObservationKind
  | NonAuthoritativeKind

inductive Authority (k : AuthorityKind) : Type where
  | mk : Authority k

abbrev CausalAuthority         := Authority AuthorityKind.CausalKind
abbrev InterpretationAuthority := Authority AuthorityKind.InterpretationKind
abbrev ExecutionAuthority      := Authority AuthorityKind.ExecutionKind

structure CanonicalAuthority where
  causal         : CausalAuthority
  interpretation : InterpretationAuthority

-- 2. Kernel Internal Sealing Namespace ( Trusted Computing Base )
namespace KernelInternal

  -- 委譲証明項のコンストラクタ封印 (private grantDelegation)
  inductive DelegatedFrom (source : CanonicalAuthority) (target : ExecutionAuthority) : Prop where
    | private grantDelegation : DelegatedFrom source target

  -- Grant 構造体のコンストラクタ封印 (private mk)
  structure ExecutionAuthorityGrant where
    private mk ::
    source    : CanonicalAuthority
    execution : ExecutionAuthority
    proof     : DelegatedFrom source execution

  -- TCB 内部限定の正規 Mint 関数
  def mintGrant (src : CanonicalAuthority) (exe : ExecutionAuthority) : ExecutionAuthorityGrant :=
    ExecutionAuthorityGrant.mk src exe DelegatedFrom.grantDelegation

end KernelInternal

-- 外部公開アクセサおよび型エイリアス
abbrev DelegatedFrom := KernelInternal.DelegatedFrom
abbrev ExecutionAuthorityGrant := KernelInternal.ExecutionAuthorityGrant

def ExecutionAuthorityGrant.source (g : ExecutionAuthorityGrant) : CanonicalAuthority :=
  g.source

def ExecutionAuthorityGrant.execution (g : ExecutionAuthorityGrant) : ExecutionAuthorityKind :=
  g.execution

-- 外部へ唯一提供される正規発行 API
def delegateExecutionAuthority
    (src : CanonicalAuthority)
    (exe : ExecutionAuthority) : ExecutionAuthorityGrant :=
  KernelInternal.mintGrant src exe

-- 3. Proof-Indexed Verification (g.proof 必須型依存)
inductive VerifyGrant (g : ExecutionAuthorityGrant) : Prop where
  | verified (p : DelegatedFrom g.source g.execution) : VerifyGrant g

theorem verify_grant_from_proof (g : ExecutionAuthorityGrant) : VerifyGrant g :=
  VerifyGrant.verified g.proof

-- 4. Scope Universe & Sealed CommitCapability
inductive ScopeKind where
  | CommitBoundaryScopeKind

inductive ScopeMarker (k : ScopeKind) : Type where
  | mk : ScopeMarker k

abbrev CommitBoundaryScope := ScopeMarker ScopeKind.CommitBoundaryScopeKind

namespace KernelInternal

  structure CommitCapability (S : Type) where
    private mk ::
    grant       : ExecutionAuthorityGrant
    scope       : S
    grant_proof : VerifyGrant grant

  def mintCapability {S : Type} (g : ExecutionAuthorityGrant) (s : S) : CommitCapability S :=
    CommitCapability.mk g s (verify_grant_from_proof g)

end KernelInternal

abbrev CommitCapability := KernelInternal.CommitCapability

def issueCommitCapability {S : Type} (g : ExecutionAuthorityGrant) (s : S) : CommitCapability S :=
  KernelInternal.mintCapability g s

-- 5. Free Monoid Catamorphism Verification
inductive ABIRegistryHistory where
  | EmptyHistory : ABIRegistryHistory
  | AppendHistory : ABIRegistryHistory → String → ABIRegistryHistory

def applyEvent (snapshot : List String) (event : String) : List String :=
  event :: snapshot

def foldHistory (h : ABIRegistryHistory) (init : List String) : List String :=
  match h with
  | ABIRegistryHistory.EmptyHistory => init
  | ABIRegistryHistory.AppendHistory prev ev => applyEvent (foldHistory prev init) ev

def projectRegistry (h : ABIRegistryHistory) : List String :=
  foldHistory h []

-- Kernel Reduction Proofs (rfl)
theorem abi_proj_catamorphism_empty : projectRegistry ABIRegistryHistory.EmptyHistory = [] :=
  rfl

theorem abi_proj_catamorphism_append (h : ABIRegistryHistory) (e : String) :
    projectRegistry (ABIRegistryHistory.AppendHistory h e) = applyEvent (projectRegistry h) e :=
  rfl

end ChronLLM