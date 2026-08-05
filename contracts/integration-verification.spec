# integration-verification.spec
SPEC: IntegrationVerification
VERSION: 1.1.5

USES:
  BaseTypes
  BaseInvariants
  BaseExcludes
  BaseHistory
  ABIRegistry
  PipelineOrchestration

DESCRIPTION:
  統合検証規約。
  Proposal Phase FSM、Inductive Pass Relation、および ProofOf 構造体項の展開。

TYPES:
  TYPE ValidationJudgement = CheckSucceeded | CheckFailed

  TYPE CheckEvidence = {
    check_name : String,
    result     : ValidationJudgement,
    evidence   : DerivedData
  }

  TYPE ProposalPhaseKind = PhaseProposedKind | PhaseValidatedKind | PhaseCommittedKind
  TYPE PhaseProposedMarker  = ScopeMarker<PhaseProposedKind>
  TYPE PhaseValidatedMarker = ScopeMarker<PhaseValidatedKind>
  TYPE PhaseCommittedMarker = ScopeMarker<PhaseCommittedKind>

  TYPE StateProposal<Phase> = {
    proposal_id  : String,
    phase_marker : Phase,
    payload      : DerivedData
  }

  TYPE ProposedProposal  = StateProposal<PhaseProposedMarker>
  TYPE ValidatedProposal = StateProposal<PhaseValidatedMarker>
  TYPE CommittedProposal = StateProposal<PhaseCommittedMarker>

  TYPE CheckIsSuccessful(e : CheckEvidence) = Inductive {
    EvSucceeded(e : CheckEvidence)
  }

  TYPE CheckMatchesProposal(e : CheckEvidence, p : ValidatedProposal) = Inductive {
    EvMatches(e : CheckEvidence, p : ValidatedProposal)
  }

  TYPE ChecksPass(p : ValidatedProposal, checks : List<CheckEvidence>) = Inductive {
    NilPass(p : ValidatedProposal)

    ConsPass(
      head          : CheckEvidence,
      tail          : List<CheckEvidence>,
      head_ok       : CheckIsSuccessful(head),
      head_matches  : CheckMatchesProposal(head, p),
      tail_ok       : ChecksPass(p, tail)
    )
  }

  TYPE ProofOf(p : ValidatedProposal) = {
    checks : List<CheckEvidence>,
    valid  : ChecksPass(p, checks)
  }

  TYPE ValidationWitness = Sigma<{
    proposal : ValidatedProposal,
    proof    : ProofOf(proposal)
  }>

  TYPE ValidationError = ProofValidationFailed(String) | IncompleteCheck
  TYPE CommitError      = InvalidProof | CapabilityInvalid | ScopeMismatch

STATE:
  CanonicalTruth : CanonicalAuthority

OPERATIONS:
  DEF create_proposal(
    id      : String,
    payload : DerivedData
  ) -> ProposedProposal

  DEF validate(
    proposal : ProposedProposal
  ) -> Result<ValidationWitness, ValidationError>

  DEF commit<S : ValidCommitScope>(
    witness    : ValidationWitness,
    capability : CommitCapability<S>
  ) -> Result<CommittedProposal, CommitError>

THEOREMS:
  THEOREM PROPOSAL.SIGMA.001:
    ∀ w : ValidationWitness, TYPEOF(w.proof) == ProofOf(w.proposal)

  THEOREM PROPOSAL.FSM.001:
    (PhaseProposedMarker != PhaseValidatedMarker) ∧
    (PhaseValidatedMarker != PhaseCommittedMarker) ∧
    (PhaseProposedMarker != PhaseCommittedMarker)

CONFORMANCE:
  ASSERT: ∀ w cap, (commit(w, cap) == Success(c)) ⇒ (TYPEOF(w.proof) == ProofOf(w.proposal))