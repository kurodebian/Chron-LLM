# integration-verification.spec
SPEC: IntegrationVerification
VERSION: 1.6.0

USES:
  BaseTypes

DESCRIPTION:
  統合検証規約。
  End-to-End Proof-Carrying State Transition (Proposed → Validated → Committed)。

TYPES:
  ENUM ValidationJudgement = CheckSucceeded | CheckFailed

  TYPE CheckEvidence = {
    proposal_id : String,
    check_name  : String,
    result      : ValidationJudgement,
    evidence    : String
  }

  ENUM ProposalPhaseKind = Proposed | Validated | Committed

  # 状態ごとの Proof-Carrying データ構造
  TYPE ProposedProposal = {
    proposal_id : String,
    payload     : String
  }

  # Validated 状態は「全件 Pass 証明」を内包する
  TYPE ValidatedProposal = {
    base   : ProposedProposal,
    checks : List<CheckEvidence>,
    proof  : Forall(e ∈ checks, (e.result == CheckSucceeded) ∧ (e.proposal_id == base.proposal_id))
  }

  # Committed 状態は ValidatedProposal と CommitCapability を含む証明オブジェクト
  TYPE CommittedProposal(graph : DelegationGraph) = {
    validated  : ValidatedProposal,
    capability : CommitCapability(graph)
  }

OPERATIONS:
  DEF validate(
    proposal : ProposedProposal,
    checks   : List<CheckEvidence>,
    proof    : Forall(e ∈ checks, (e.result == CheckSucceeded) ∧ (e.proposal_id == proposal.proposal_id))
  ) -> ValidatedProposal

  DEF commit(
    graph      : DelegationGraph,
    validated  : ValidatedProposal,
    capability : CommitCapability(graph)
  ) -> CommittedProposal(graph)

# LAYER 0: LEAN KERNEL MATHEMATICAL THEOREMS
THEOREMS:
  # End-to-End 不変量定理: CommittedProposal に含まれる証明は自動的に健全である
  THEOREM PROPOSAL.TRANSITION_SOUNDNESS.001:
    ∀ (graph : DelegationGraph) (c : CommittedProposal(graph)),
    graph.allows(c.capability.grant.source, c.capability.grant.execution)