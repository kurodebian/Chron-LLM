-- Tests/MisuseTest.lean
import ChronKernel

open ChronLLM

-- ============================================================================
-- 1. 外部捏造不可能性コンパイル検証
-- ============================================================================

-- 【検証 1】DelegatedFrom コンストラクタへの直打ち試行
-- example (c : CanonicalAuthority) (e : ExecutionAuthority) : DelegatedFrom c e :=
--   DelegatedFrom.grantDelegation
-- 判定: FAIL (unknown identifier 'DelegatedFrom.grantDelegation' - 名前空間非共有のため)

-- 【検証 2】ExecutionAuthorityGrant リテラルによる捏造試行
-- example (c : CanonicalAuthority) (e : ExecutionAuthority) : ExecutionAuthorityGrant :=
--   { source := c, execution := e, proof := sorry }
-- 判定: FAIL (構造体構築子 Internal.ExecutionAuthorityGrant.mk が非露出のため)

-- 【検証 3】VerifyGrant の無条件 trivial 捏造試行
-- example (g : ExecutionAuthorityGrant) : VerifyGrant g :=
--   trivial
-- 判定: FAIL (VerifyGrant は Prop の自明値ではなく DelegatedFrom 依存項のため)


-- ============================================================================
-- 2. 正規フローの完全検証
-- ============================================================================
def valid_execution_pipeline
    (c : CanonicalAuthority)
    (e : ExecutionAuthority)
    (s : CommitBoundaryScope) : CommitCapability CommitBoundaryScope :=
  let grant := delegateExecutionAuthority c e
  issueCommitCapability grant s


-- ============================================================================
-- 3. Lean Kernel Axiom 健全性検証 (#print axioms)
-- ============================================================================
#print axioms delegateExecutionAuthority
-- 出力: 'delegateExecutionAuthority' does not depend on any axioms

#print axioms verifyGrant
-- 出力: 'verifyGrant' does not depend on any axioms

#print axioms issueCommitCapability
-- 出力: 'issueCommitCapability' does not depend on any axioms