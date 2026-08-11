# base-types.spec
SPEC: BaseTypes
VERSION: 1.6.0

DESCRIPTION:
  Chron-LLM 基底型定義。
  【v1.6.0】Proof-Carrying Engine Specification。
  DelegationGraph による委譲関係の抽象化 (Relation vs Data 分離)、
  Nat 識別子、およびシステム全体の代数的証明モデル。

TYPES:
  TYPE Nat    = NativeNat
  TYPE String = NativeString

  ENUM AuthorityKind =
      CausalKind
    | InterpretationKind
    | ExecutionKind
    | ObservationKind

  TYPE Authority(k : AuthorityKind) = {
    id : Nat
  }

  TYPE ExecutionAuthority      = Authority(ExecutionKind)
  TYPE CausalAuthority         = Authority(CausalKind)
  TYPE InterpretationAuthority = Authority(InterpretationKind)

  TYPE CanonicalAuthority = {
    causal         : CausalAuthority,
    interpretation : InterpretationAuthority
  }

  # 抽象委譲グラフ (Abstract Relation Model)
  TYPE DelegationGraph = {
    allows : CanonicalAuthority -> ExecutionAuthority -> Prop
  }

  # 抽象関係に基づく証明内包構造体
  TYPE ExecutionAuthorityGrant(graph : DelegationGraph) = {
    source    : CanonicalAuthority,
    execution : ExecutionAuthority,
    proof     : graph.allows(source, execution)
  }

  # Commit 境界専用 Capability (Grant に密結合)
  TYPE CommitCapability(graph : DelegationGraph) = {
    grant : ExecutionAuthorityGrant(graph)
  }

OPERATIONS:
  OP delegate_execution_authority(
    graph     : DelegationGraph,
    source    : CanonicalAuthority,
    execution : ExecutionAuthority,
    proof     : graph.allows(source, execution)
  ) -> ExecutionAuthorityGrant(graph)

  OP verify_grant(
    graph : DelegationGraph,
    grant : ExecutionAuthorityGrant(graph)
  ) -> graph.allows(grant.source, grant.execution)

  OP issue_commit_capability(
    graph : DelegationGraph,
    grant : ExecutionAuthorityGrant(graph)
  ) -> CommitCapability(graph)

# -----------------------------------------------------------------------------
# LAYER 0: LEAN KERNEL MATHEMATICAL THEOREMS
# -----------------------------------------------------------------------------
THEOREMS:
  # 健全性定理: Grant 項が存在するならば、そのグラフ上で関係 allows が確実に成立する
  THEOREM AUTH.SOUNDNESS.001:
    ∀ (graph : DelegationGraph) (g : ExecutionAuthorityGrant(graph)),
    graph.allows(g.source, g.execution)

# -----------------------------------------------------------------------------
# LAYER 1: REPOSITORY CONSTITUTION & ARCHITECTURAL POLICIES
# -----------------------------------------------------------------------------
POLICIES:
  POLICY: TCB.ISOLATION.001
    DESCRIPTION: 非 TCB モジュールは "ChronLLM.Internal" を import してはならない。

  POLICY: AUTH.FACTORY_ONLY.001
    DESCRIPTION: Grant の構築は抽象グラフ証明を伴う公式 API を経由すること。

# -----------------------------------------------------------------------------
# LAYER 2: CI & BUILD SYSTEM ENFORCEMENT
# -----------------------------------------------------------------------------
ENFORCEMENT:
  ENFORCE: CI.GREP_INTERNAL_IMPORT
    METHOD: AST / Shell Linter
    TARGET: non-TCB directories
    RULE: Reject if match "import ChronLLM.Internal"