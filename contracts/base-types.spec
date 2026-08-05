# base-types.spec
SPEC: BaseTypes
VERSION: 1.1.5

DESCRIPTION:
  Chron-LLM 基底型定義。
  【v1.1.5】DelegatedFrom および ExecutionAuthorityGrant のコンストラクタ封印（Sealing）。
  KernelInternal モジュール境界による可視性制御と、無制限な証明項捏造の型システムレベル遮断。

TYPES:
  TYPE UInt64 = NativeUInt64
  TYPE Int32  = NativeInt32
  TYPE String = NativeString
  TYPE Unit   = NativeUnit

  TYPE Result<T, E> = Success(T) | Failure(E)
  TYPE Option<T>     = Some(T) | None

  TYPE CommitIndex = UInt64
  TYPE Version     = SemVer(String)

  # Inductive Authority Universe (型レベル分離)
  TYPE AuthorityKind =
      CausalKind
    | InterpretationKind
    | ExecutionKind
    | ObservationKind
    | NonAuthoritativeKind

  TYPE Authority(k : AuthorityKind) = Inductive {
    MkAuthority(k : AuthorityKind)
  }

  TYPE CausalAuthority         = Authority(CausalKind)
  TYPE InterpretationAuthority = Authority(InterpretationKind)
  TYPE ExecutionAuthority      = Authority(ExecutionKind)
  TYPE ObservationAuthority    = Authority(ObservationKind)
  TYPE NonAuthoritative        = Authority(NonAuthoritativeKind)

  # 根源権威（Canonical Truth）
  TYPE CanonicalAuthority = {
    causal         : CausalAuthority,
    interpretation : InterpretationAuthority
  }

  # 【v1.1.5 改修】密封型有向委譲関係 (Sealed Prop)
  # コンストラクタ GrantDelegation は KernelInternal 外からの直接呼び出し禁止
  TYPE DelegatedFrom(source : CanonicalAuthority, target : ExecutionAuthority) = Sealed Inductive {
    PrivateGrantDelegation(source : CanonicalAuthority, target : ExecutionAuthority)
  }

  # 【v1.1.5 改修】密封構造体 Grant
  # レコードリテラル { source := ..., execution := ..., proof := ... } による直接生成を禁止
  TYPE ExecutionAuthorityGrant = PrivateConstructor<{
    source    : CanonicalAuthority,
    execution : ExecutionAuthority,
    proof     : DelegatedFrom(source, execution)
  }>

  # Scope Universe
  TYPE ScopeKind = WorldlineScopeKind | BranchScopeKind | CommitBoundaryScopeKind
  TYPE WorldlineScope      = ScopeMarker<WorldlineScopeKind>
  TYPE BranchScope         = ScopeMarker<BranchScopeKind>
  TYPE CommitBoundaryScope = ScopeMarker<CommitBoundaryScopeKind>

  UNION ValidCommitScope = CommitBoundaryScope

  # g.proof に依存する真の証明型
  TYPE VerifyGrant(g : ExecutionAuthorityGrant) = Inductive {
    GrantVerified(
      g     : ExecutionAuthorityGrant,
      proof : DelegatedFrom(g.source, g.execution)
    )
  }

  # 【v1.1.5 改修】密封構造体 CommitCapability
  TYPE CommitCapability<S : ValidCommitScope> = PrivateConstructor<{
    grant       : ExecutionAuthorityGrant,
    scope       : S,
    grant_proof : VerifyGrant(grant)
  }>

OPERATIONS:
  DEF semver_compare(v1 : Version, v2 : Version) -> Int32

  # 唯一の正規委譲権限発行操作 (Kernel Trusted Code Base)
  OP delegate_execution_authority(
    canonical : CanonicalAuthority,
    execution : ExecutionAuthority
  ) -> ExecutionAuthorityGrant

  OP issue_commit_capability<S : ValidCommitScope>(
    grant       : ExecutionAuthorityGrant,
    scope       : S,
    grant_proof : VerifyGrant(grant)
  ) -> CommitCapability<S>

THEOREMS:
  # 証明項捏造不能性の型理論的証明
  THEOREM AUTH.SEAL.001:
    ∀ s : CanonicalAuthority, ∀ e : ExecutionAuthority,
    CANNOT_INSTANTIATE_WITHOUT_FACTORY(DelegatedFrom(s, e))

  # 一方向性の型理論的証明
  THEOREM AUTH.DELEGATE.001:
    ∀ e : ExecutionAuthority, NOT_EXISTS(s : CanonicalAuthority, DECOMPOSABLE(e, s))

  # Capability の型論理閉包
  THEOREM AUTH.CAP.001:
    ∀ a : CanonicalAuthority, ∀ S, NOT_COERCIBLE(a, CommitCapability<S>)