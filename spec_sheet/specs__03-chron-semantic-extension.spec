MODULE ChronSemanticExtension
EXTENDS Constitution
DEFINES SpecOS::ChronUniverse

-- ================================================================
-- 0. SCOPE OF CHRON SEMANTIC EXTENSION
-- ================================================================

ChronSemanticExtension defines:

- Evidence
- Proposal
- Commit
- CommitResult
- Branch
- Fork
- Merge
- SharedPrefix

It SHALL:

- define what constitutes an authoritative transition (Commit)
- define how Branch / Fork / Merge are semantically understood
- define CommitResult as the semantic outcome of a Commit

It SHALL NOT:

- execute Commit (Kernel responsibility)
- schedule CommitRequest (Runtime responsibility)
- mutate CanonicalState (Kernel responsibility)
- define Runtime or Kernel policies


-- ================================================================
-- 1. IDENTIFIERS
-- ================================================================

TYPE EvidenceID =
  IDType(NamespacedID("evidence"))

TYPE ProposalID =
  IDType(NamespacedID("proposal"))

TYPE CommitID =
  IDType(NamespacedID("commit"))

TYPE CommitResultID =
  IDType(NamespacedID("commit-result"))

TYPE BranchID =
  IDType(NamespacedID("branch"))

TYPE MergeID =
  IDType(NamespacedID("merge"))

TYPE SharedPrefixID =
  IDType(NamespacedID("shared-prefix"))


-- ================================================================
-- 2. EVIDENCE MODEL
-- ================================================================

ENTITY Evidence {

  evidence_id :
    EvidenceID

  payload :
    Expression

  source :
    Expression
}

INVARIANT EVIDENCE_01:
Evidence MUST be immutable.

INVARIANT EVIDENCE_02:
Evidence MAY support Proposal,
but does NOT define authority directly.


-- ================================================================
-- 3. PROPOSAL MODEL
-- ================================================================

ENTITY Proposal {

  proposal_id :
    ProposalID

  evidence :
    List<Reference<Evidence>>

  intent :
    Expression

  target_state :
    Expression
}

INVARIANT PROPOSAL_01:
Proposal describes a candidate transition.

INVARIANT PROPOSAL_02:
Proposal MUST NOT mutate CanonicalState.

INVARIANT PROPOSAL_03:
Proposal MUST NOT define Commit authority.


-- ================================================================
-- 4. COMMIT MODEL
-- ================================================================

ENTITY Commit {

  commit_id :
    CommitID

  proposal :
    Reference<Proposal>

  authority_scope :
    Expression

  justification :
    Expression
}

INVARIANT COMMIT_01:
Commit defines the semantic meaning
of an authorized transition.

INVARIANT COMMIT_02:
Commit MUST be derived from Proposal
and applicable Evidence.

INVARIANT COMMIT_03:
Commit MUST NOT directly mutate CanonicalState.

INVARIANT COMMIT_04:
Commit MUST NOT create Event by itself
(Kernel executes Commit).


-- ================================================================
-- 5. COMMIT RESULT MODEL
-- ================================================================

ENTITY CommitResult {

  result_id :
    CommitResultID

  commit :
    Reference<Commit>

  status :
    ENUM { Accepted, Rejected, Failed }

  effect_summary :
    Expression
}

INVARIANT COMMIT_RESULT_01:
CommitResult is the semantic outcome
of executing a Commit.

INVARIANT COMMIT_RESULT_02:
CommitResult MUST reference exactly one Commit.

INVARIANT COMMIT_RESULT_03:
CommitResult MUST NOT mutate CanonicalState directly.

INVARIANT COMMIT_RESULT_04:
CommitResult MAY be used by Kernel
to derive Event.


-- ================================================================
-- 6. BRANCH MODEL
-- ================================================================

ENTITY Branch {

  branch_id :
    BranchID

  base_worldline :
    Reference<Worldline>

  fork_point :
    Reference<Event>

  branch_worldline :
    Reference<Worldline>
}

INVARIANT BRANCH_01:
Branch MUST preserve the shared prefix
up to fork_point.

INVARIANT BRANCH_02:
BranchWorldline MUST diverge only
after fork_point.

INVARIANT BRANCH_03:
Branch MUST NOT alter base_worldline.


-- ================================================================
-- 7. FORK MODEL
-- ================================================================

ENTITY Fork {

  branch :
    Reference<Branch>

  new_worldline :
    Reference<Worldline>
}

INVARIANT FORK_01:
ForkWorldline MUST share a prefix
with base_worldline of Branch.

INVARIANT FORK_02:
Fork MUST create a new identity
for the diverging worldline.

INVARIANT FORK_03:
Fork MUST NOT modify Events
in the shared prefix.


-- ================================================================
-- 8. MERGE MODEL
-- ================================================================

ENTITY Merge {

  merge_id :
    MergeID

  left_worldline :
    Reference<Worldline>

  right_worldline :
    Reference<Worldline>

  shared_prefix :
    Reference<SharedPrefix>

  merged_worldline :
    Reference<Worldline>
}

ENTITY SharedPrefix {

  prefix_id :
    SharedPrefixID

  events :
    List<Reference<Event>>
}

INVARIANT MERGE_01:
Merge MUST require a SharedPrefix
between left_worldline and right_worldline.

INVARIANT MERGE_02:
SharedPrefix MUST be immutable.

INVARIANT MERGE_03:
Merge MUST preserve causal consistency
of both input worldlines.

INVARIANT MERGE_04:
MergedWorldline MUST contain SharedPrefix
as its initial segment.


-- ================================================================
-- 9. BRANCH / MERGE CAUSALITY INVARIANTS
-- ================================================================

INVARIANT BRANCH_CAUSAL_01:
ForkPreservesAncestorHistory:

  FORALL branch IN Branch =>
    SharedPrefix(branch.base_worldline,
                 branch.branch_worldline)
    IS prefix up to branch.fork_point.


INVARIANT BRANCH_CAUSAL_02:
PostForkIndependence:

  AFTER branch.fork_point,
  branch.branch_worldline
  MAY diverge independently
  without altering base_worldline.


INVARIANT MERGE_CAUSAL_01:
MergeRequiresCommonAncestor:

  FORALL merge IN Merge =>
    EXISTS sp IN SharedPrefix =>
      sp = merge.shared_prefix
      AND sp IS prefix of merge.left_worldline
      AND sp IS prefix of merge.right_worldline.


INVARIANT MERGE_CAUSAL_02:
MergePreservesCausalConsistency:

  merged_worldline
  MUST respect ordering constraints
  of both left_worldline and right_worldline
  over SharedPrefix and divergent segments.


-- ================================================================
-- 10. CHRON BOUNDARY INVARIANTS
-- ================================================================

INVARIANT CHRON_BOUNDARY_01:
ChronSemanticExtension MUST NOT execute Commit.

INVARIANT CHRON_BOUNDARY_02:
ChronSemanticExtension MUST NOT mutate CanonicalState.

INVARIANT CHRON_BOUNDARY_03:
ChronSemanticExtension MUST define:

  - Commit meaning
  - CommitResult semantics
  - Branch / Fork / Merge semantics

INVARIANT CHRON_BOUNDARY_04:
Runtime MUST use CommitRequest
to request Commit execution.

INVARIANT CHRON_BOUNDARY_05:
Kernel MUST execute Commit
according to Commit semantics
defined in this module,
WITHOUT redefining them.
