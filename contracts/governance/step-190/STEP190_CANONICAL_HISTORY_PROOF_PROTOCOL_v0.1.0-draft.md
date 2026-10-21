# Filing Record（ファイリングメタデータ — ドラフト本文の一部ではない）

FILED: 2026-10-21 (Asia/Tokyo)
FILING: D1 裁定に基づくファイリングフェーズ（../ADJUDICATIONS.md 参照）
FILING_STATUS: FILED_AS_DRAFT_ARTIFACT
NORMATIVE_STATUS: PROPOSED | ADOPTION_STATUS: NOT_ADOPTED | IMPLEMENTATION_STATUS: NOT_VERIFIED
FILING はステータスを変更しない。ARTIFACT_EXISTENCE != NORMATIVE_ADOPTION。
CANONICAL_MUTATION: NONE（ドラフトの記録であり、採択・実装・Freeze ではない）
SOURCE_PROVENANCE: ~/.hermes/pastes/paste_2_134928.txt lines 1-1043（同一コピー paste_3_141646.txt）
SOURCE_SHA256: dbd8746028c9cf448eb9782ac83a65746a50abc26a0778fbda4b4a46dbe9ff54
BODY_SHA256: dbd8746028c9cf448eb9782ac83a65746a50abc26a0778fbda4b4a46dbe9ff54
AUDIT_EVIDENCE: ~/audit-190/evidence_ledger_190.json (E-190-001..010), ~/audit-190/CLOSURE_REPORT_190.md (A190-E-REAL)
ANALYSIS: ~/design-step190/STEP190_SPEC_ANALYSIS.md, ~/design-step190/STEP190_DESIGN_PROPOSAL_v0.2.md
REPO_BASELINE: Chron-LLM @ b231635452dd6ccd75f9f4ec9fbb40c5de510afa (backup/home-2026-08-12-0219, worktree clean)
<<<FILING-END>>>

STEP-190 — Canonical History Proof Protocol / Checkpoint Finality / Verification Composition / Audit Decision Contract
STEP_ID: 190
VERSION: 0.1.0-draft
STATUS: DRAFT_COMPLETE
NORMATIVE_STATUS: PROPOSED
ADOPTION_STATUS: NOT_ADOPTED
IMPLEMENTATION_STATUS: NOT_VERIFIED
TEST_STATUS: NOT_EXECUTED
REPOSITORY_INSPECTION: NOT_PERFORMED
PROOF_OBJECT_VALIDATION: NOT_EXECUTED
CHECKPOINT_FINALITY_VALIDATION: NOT_EXECUTED
RANGE_PROOF_COMPOSITION_VALIDATION: NOT_EXECUTED
VERIFICATION_COMPOSITION_VALIDATION: NOT_EXECUTED
PROOF_INVALIDATION_VALIDATION: NOT_EXECUTED
AUDIT_DECISION_VALIDATION: NOT_EXECUTED
CANONICAL_MUTATION: NONE
GLOBAL_ACCEPTANCE: NOT_ASSESSED
FREEZE_STATUS: NOT_AUTHORIZED
TIMEZONE: Asia/Tokyo
1. PURPOSE
STEP-190 proposes the protocol that composes individual verification results into a bounded, evidence-backed decision about whether a specified downstream operation may proceed.
The central requirement is to prevent a valid proof of one property from being misinterpreted as proof of unrelated properties.
CANONICAL HISTORY
    -> TYPED CLAIMS
    -> INDIVIDUAL PROOFS
    -> PROOF VALIDATION
    -> COMPOSITION
    -> POLICY EVALUATION
    -> AUDIT DECISION
    -> SEPARATE AUTHORIZATION
    -> SEPARATE CANONICAL COMMIT, IF APPLICABLE
This is a proposed logical flow. It does not assert that the underlying mechanisms exist or that the sequence is implemented.
1.1 Architectural axioms
CANONICAL_HISTORY_IS_AUTHORITATIVE
PROOF_OBJECT_IS_EVIDENCE
PROOF_VALIDITY_IS_SCOPE_BOUND
SUBPROOF_VALIDITY_DOES_NOT_IMPLY_COMPOSITE_VALIDITY
VERIFICATION_IS_NOT_AUTHORIZATION
AUTHORIZATION_IS_NOT_COMMIT
CHECKPOINT_FINALITY_IS_NOT_HISTORY_FINALITY
PROOF_INVALIDATION_DOES_NOT_REWRITE_HISTORY
EXCEPTION_IS_NOT_REQUIREMENT_SATISFACTION
UNKNOWN_IS_NOT_PASS
1.2 Scope
Typed proof objects and claim identity.
Proof validity, scope, and provenance.
Checkpoint issuance, authorization, finality, and succession.
Range-proof composition and continuity.
Composition of integrity, authenticity, authority, policy, and semantic claims.
Proof invalidation and reassessment.
Profile compatibility and version pinning.
Audit decisions and downstream authorization boundaries.
Failure propagation and bounded impact.
Exceptions, acceptance evidence, and decision reproducibility.
1.3 Non-goals
Choosing a production proof system or cryptographic algorithm.
Declaring any existing checkpoint or verification report valid.
Implementing a commit protocol or modifying Canonical History.
Automatically resolving conflicting proofs.
Allowing an audit decision to bypass Commit Authority.
Establishing production acceptance or Freeze.
2. NORMATIVE LANGUAGE AND AUTHORITY BOUNDARY
MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are proposed normative keywords. They acquire binding force only after formal adoption.
Entity
Permitted role
Boundary
Proof producer
Construct a proof and identify its claims
Cannot certify its own proof merely by producing it
Proof verifier
Evaluate proof validity under a declared profile
Cannot expand the proof's scope
Composer
Combine verified claims under explicit rules
Cannot silently omit required claims
Policy evaluator
Determine whether requirements for a specified action are satisfied
Cannot establish canonical commit finality
Audit decision authority
Issue a bounded decision under its mandate
Cannot rewrite historical evidence
Commit Authority
Authorize and perform canonical mutation under the applicable contract
Cannot infer authorization solely from an audit result
Replay engine
Derive projections from eligible History
Cannot mutate Canonical History

A component MAY perform multiple roles only if its responsibilities, inputs, outputs, and authority boundaries remain independently identifiable and testable.
3. TYPED PROOF OBJECT MODEL
3.1 Proof object
A proof object MUST identify the claim it supports, the subject to which it applies, the verification profile, and the evidence needed to evaluate it.
Proposed schema:
proof_id: REQUIRED
proof_type: REQUIRED
subject_ref: REQUIRED
claim_id: REQUIRED
claim_scope: REQUIRED
history_id: REQUIRED
history_range: OPTIONAL
profile_id: REQUIRED
profile_version: REQUIRED
producer_identity: REQUIRED
evidence_refs: REQUIRED
dependency_proof_refs: REQUIRED
result: REQUIRED
limitations: REQUIRED
The schema is conceptual and has not been validated. Exact field types, cardinality, canonical serialization, and cryptographic bindings remain open design decisions.
3.2 Proof types
The proof system SHOULD distinguish at least:
CONTENT_INTEGRITY_PROOF
EVENT_AUTHENTICITY_PROOF
AUTHORIZATION_PROOF
CONTINUITY_PROOF
CHECKPOINT_PROOF
RANGE_COMPLETENESS_PROOF
POLICY_COMPLIANCE_PROOF
SEMANTIC_EVIDENCE_PROOF
REPLAY_EQUIVALENCE_PROOF
AUDIT_EXECUTION_PROOF
The type declares the intended claim class. It does not establish validity.
An object labelled AUTHORIZATION_PROOF MUST NOT be accepted as such unless its contents and verification procedure satisfy the authorization requirements of the adopted profile.
3.3 Claim identity
Claim identity MUST be stable enough to distinguish materially different assertions about the same subject.
At minimum, claim identity MUST account for:
subject identity;
property being asserted;
relevant History or range;
applicable profile;
relevant temporal or authority context, where material.
Two proofs about the same event but different properties MUST NOT be treated as interchangeable.
3.4 Proof result
The proposed proof result vocabulary is:
VALID
INVALID
INDETERMINATE
PARTIALLY_VALID
NOT_EVALUATED
VALID: the proof satisfies the declared verification procedure for its entire declared scope.
INVALID: a required assertion is disproved or a mandatory proof condition fails.
INDETERMINATE: evidence is insufficient to determine validity.
PARTIALLY_VALID: only an explicitly identified subset is verified.
NOT_EVALUATED: no verification result is available.
A proof producer's claimed result MUST NOT be treated as the verifier's result without the required verification execution.
3.5 Proof identity versus event identity
A proof object and the event it concerns MUST have distinct identities.
Multiple proofs MAY concern the same event. A proof MAY be superseded, invalidated, or retained for historical audit without changing the identity or contents of the original event.
A proof object's existence MUST NOT create a canonical event or modify a committed event.
4. PROOF VALIDITY, SCOPE, AND PROVENANCE
4.1 Scope containment
Every proof MUST declare the scope over which its conclusion holds.
A proof MUST NOT be applied to:
a different History;
an unproven event range;
a different claim type;
an incompatible verification profile;
an authority epoch or temporal context not covered by its evidence.
Any permitted scope extension MUST be supported by an explicit composition rule and verified evidence.
4.2 Scope containment rule
Let Sp be the scope established by proof p, and Sc the scope required by a downstream claim.
A proof may directly support that claim only if:

ScSp
and the claim type, profile, dependencies, and relevant context are compatible.
This relation is necessary but not sufficient. Scope containment alone does not prove that the proof is valid.
4.3 Provenance
Proof provenance MUST identify the producer, inputs, method or profile, and relevant execution evidence.
Where a proof depends on another proof, that dependency MUST reference the exact proof identity and version—not merely a mutable alias or descriptive label.
4.4 Self-asserted proof status
A proof object MUST NOT become valid because it contains result: VALID.
The verifier MUST derive its result from the declared proof contents, evidence, profile, and verification procedure.
4.5 Proof content immutability
Once a proof object has been issued and referenced by an audit decision, its content MUST NOT be silently changed.
A changed proof MUST receive a distinct identity or version, with an explicit relationship to the earlier object. Any affected downstream decision MUST be reevaluated according to the applicable policy.
5. CHECKPOINT ISSUANCE, AUTHORIZATION, AND FINALITY
5.1 Checkpoint lifecycle
The proposed checkpoint lifecycle is:
CHECKPOINT_CANDIDATE
  -> CHECKPOINT_VALIDATED
  -> CHECKPOINT_AUTHORIZED
  -> CHECKPOINT_ISSUED
  -> CHECKPOINT_VERIFIED
  -> CHECKPOINT_SUPERSEDED | CHECKPOINT_INVALIDATED
These are distinct states. A checkpoint may be issued but not yet verified by a particular verifier. Supersession does not necessarily mean invalidity.
5.2 Checkpoint identity and binding
A checkpoint MUST be bound to:
the logical history_id;
the exact History prefix or range;
the declared terminal event or sequence;
the commitment or proof construction used;
the governing checkpoint profile;
the issuing authority and applicable authority context;
the evidence needed to verify issuance and content.
5.3 Issuance versus verification
Checkpoint issuance is an act by a designated authority. Checkpoint verification is an assessment of the resulting evidence.
Neither may be substituted for the other.
ISSUED != VERIFIED
VERIFIED != AUTHORIZED
AUTHORIZED != COMMITTED
A checkpoint MAY be used as a trust anchor for a later range only when the adopted profile explicitly permits it and the required checkpoint authorization and verification claims pass.
5.4 Checkpoint finality
The contract MUST define the conditions under which an issued checkpoint is considered authoritative for its declared prefix.
Those conditions MUST address conflicting issuance, authority epochs, proof integrity, and the applicable commit or checkpoint protocol.
A checkpoint MUST NOT be declared final merely because it has been signed, replicated, timestamped, or observed by multiple nodes.
The precise checkpoint-finality protocol remains unresolved until the upstream Commit Finality and authority-transfer contracts are adopted and reconciled.
5.5 Checkpoint succession
A successor checkpoint MUST identify its predecessor or otherwise prove the required continuity relationship.
If the successor covers a larger range, the proof MUST establish that the new range extends the previously verified prefix under the adopted protocol.
A successor checkpoint MUST NOT silently replace a conflicting checkpoint. Conflicts require preservation of both records and an explicit adjudication path.
5.6 Checkpoint invalidation
A checkpoint MAY become unusable for a particular claim because its proof fails, its required trust assumptions are no longer satisfied, or later evidence establishes a conflict.
Invalidation MUST identify the reason, affected scope, evidence, and applicable policy.
Invalidating a checkpoint does not delete the underlying History and does not automatically establish that every event in the covered range was invalid.
6. RANGE-PROOF COMPOSITION AND VERIFIED-PREFIX RULES
6.1 Composition objective
Range-proof composition MUST establish that individually verified segments form a valid proof for the requested aggregate range.
The validity of every individual segment is necessary where every segment is required, but it is not sufficient. Composition MUST additionally establish compatible History identity, boundary alignment, ordering, continuity, and completeness.
P0: GENESIS -> CHECKPOINT A
P1: CHECKPOINT A -> CHECKPOINT B
P2: CHECKPOINT B -> CHECKPOINT C
                         |
                         v
              COMPOSITE RANGE PROOF
                         |
                         v
        IDENTITY + BOUNDARY + CONTINUITY
              + COMPLETENESS CHECKS
This diagram represents a possible composition pattern, not a selected production proof construction.
6.2 Composition preconditions
A composite proof MUST establish, as required by its profile:
Every required subproof has a distinct, resolvable identity.
Every required subproof is verified under a compatible profile.
All subproofs refer to the intended logical History.
Adjacent range boundaries match or have an explicitly verified transition.
Ordering and sequence semantics are compatible.
No required interval is omitted.
No conflicting or duplicate interval is silently accepted.
The composition rule itself is valid for the declared proof types.
Every dependency needed to establish completeness is resolved.
The composite proof identifies its complete input set.
6.3 Boundary semantics
The protocol MUST define whether range boundaries are inclusive or exclusive and how event sequence numbers, predecessor references, and terminal checkpoints are interpreted.
Two adjacent ranges MUST NOT be considered continuous merely because their displayed numeric boundaries appear adjacent. Their actual boundary references and the adopted ordering model must establish the relationship.
6.4 Gap and overlap handling
A range composition MUST explicitly detect:
missing intervals;
overlapping intervals;
conflicting event identities;
duplicate sequence positions;
incompatible predecessor references;
conflicting terminal checkpoints;
unsupported branch transitions.
An overlap MAY be accepted when the composition profile explicitly permits it and verifies that the overlapping content is consistent. An overlap MUST NOT be silently discarded to make the range appear continuous.
A gap MUST remain visible unless an adopted proof construction establishes that the apparent gap is valid under the relevant History model.
6.5 Composite result
The composite proof MUST retain references to all required subproofs and record the result of every mandatory composition condition.
The composite result MUST NOT be stronger than its verified dependencies and composition checks.
COMPOSITE_VALID
    requires
      ALL_REQUIRED_SUBPROOFS_VALID
      AND IDENTITY_COMPATIBILITY
      AND BOUNDARY_COMPATIBILITY
      AND CONTINUITY_ESTABLISHED
      AND REQUIRED_COMPLETENESS_ESTABLISHED
      AND COMPOSITION_RULE_VALID
If a required subproof is indeterminate, the composite MUST NOT be VALID unless the adopted profile explicitly establishes that the subproof is unnecessary for the specific claim.
6.6 Verified-prefix semantics
A verified prefix is a contiguous range whose required claims have been established from the declared genesis or an accepted, verified checkpoint.
The system MUST record the exact endpoint of that prefix. A verified prefix MUST NOT imply that the remainder of the History is verified.
If verification fails at event ek, a preceding range MAY remain verified if its proof dependencies are independent of the failed range. The system MUST determine the affected scope from the actual dependency graph rather than assuming either total invalidity or total independence.
6.7 Composite proof identity
Every composite proof MUST have its own identity and identify:
the requested aggregate scope;
the ordered subproof references;
the composition algorithm or rule-set version;
the compatibility decisions;
the resulting verified and unverified ranges;
the complete verification result.
Changing any material input or composition rule MUST produce a new composite proof or a new version under an explicitly defined immutable-version model.
7. VERIFICATION COMPOSITION ACROSS CLAIM TYPES
7.1 Claim dimensions
The protocol MUST represent distinct claims for distinct properties.
Claim dimension
Required question
Content integrity
Does the content satisfy its declared integrity commitment?
Authenticity
Does the evidence establish the relevant cryptographic identity relationship?
Authorization
Was the action authorized under the applicable authority and policy?
Continuity
Is the event connected to the declared History range?
Completeness
Is the required range present under the selected proof construction?
Policy compliance
Were the applicable normative constraints satisfied?
Semantic support
Does the evidence support the asserted interpretation?
Replay equivalence
Does replay produce the expected derived result under the declared profile?

These dimensions MUST NOT be collapsed into one undifferentiated proof type.
7.2 Required-claim manifest
Every composite verification request MUST identify the set of claims required for its intended decision.
Proposed manifest:
verification_request_id: REQUIRED
subject_ref: REQUIRED
requested_scope: REQUIRED
decision_purpose: REQUIRED
verification_profile_id: REQUIRED
required_claims: REQUIRED
optional_claims: REQUIRED
permitted_alternatives: REQUIRED
policy_ref: REQUIRED
A verifier MUST NOT silently remove a difficult claim from the required set. A permitted alternative MUST be explicitly declared by the governing profile and independently verified.
7.3 Claim dependency graph
The required claim set SHOULD be represented as a dependency graph. A claim MUST be considered established only when its own proof requirements and all mandatory dependencies are satisfied.
For example, a downstream authorization decision might require:
CONTENT INTEGRITY
        +
EVENT AUTHENTICITY
        +
HISTORY CONTINUITY
        +
COMMIT AUTHORIZATION
        +
APPLICABLE POLICY
        |
        v
ELIGIBILITY CLAIM
        |
        v
SEPARATE AUTHORIZATION DECISION
The graph is illustrative. The actual dependencies depend on the downstream operation and its adopted policy.
7.4 No implicit claim promotion
The system MUST NOT infer:
authorization from integrity;
continuity from a valid signature;
completeness from a valid terminal checkpoint alone;
semantic truth from replay equivalence;
commit finality from an authorization proof;
current trust from historical trust evidence without evaluating the relevant trust policy.
Any such inference requires an explicit normative rule and supporting evidence.
7.5 Contradictory claims
If two verified-looking proofs make incompatible claims about the same subject, scope, and relevant context, the composer MUST detect the conflict where the declared claim model permits that comparison.
The composer MUST NOT resolve the conflict using arbitrary priority, arrival order, producer reputation alone, or whichever result is more favorable.
The conflicting proofs MUST be retained, and the aggregate claim MUST remain unresolved until an applicable adjudication rule determines the result.
7.6 Semantic evidence boundary
A semantic-support proof establishes only the proposition defined by its claim and verification profile.
If an LLM produces a proposed interpretation, the proposal MUST NOT be treated as a verified semantic claim merely because it is syntactically valid or passes a schema validator.
The system MUST identify the evidence, deterministic checks, review requirements, and acceptance criteria needed to establish the relevant semantic claim.
8. PROOF INVALIDATION AND HISTORICAL REASSESSMENT
8.1 Invalidation triggers
A proof MAY require invalidation or reassessment when:
its content commitment fails verification;
required evidence is found to be forged or misattributed;
its authority context is invalidated;
a conflicting checkpoint or History fork is discovered;
a previously unknown dependency becomes material;
a verification algorithm or trust assumption is found inadequate;
the profile under which the proof was produced is withdrawn or superseded;
new evidence materially changes the supported claim.
These triggers do not all have identical effects. The adopted policy MUST define whether each trigger causes invalidation, restricted applicability, or reassessment.
8.2 Proof status versus historical event status
Proof invalidation and event invalidation MUST remain distinct.
PROOF_INVALIDATED
    != EVENT_ERASED
    != EVENT_NEVER_COMMITTED
    != EVENT_AUTOMATICALLY_INVALID
A proof may cease to establish a claim even though the underlying event remains part of Canonical History.
Whether the event was validly committed MUST be evaluated under the applicable commit and governance contracts.
8.3 Invalidation record
An invalidation record SHOULD contain:
invalidation_id: REQUIRED
target_proof_ref: REQUIRED
trigger_type: REQUIRED
affected_claim_refs: REQUIRED
affected_scope: REQUIRED
evidence_refs: REQUIRED
decision_authority_ref: REQUIRED
governing_policy_ref: REQUIRED
effective_scope: REQUIRED
reassessment_requirements: REQUIRED
The invalidation record MUST identify whether the decision concerns a specific proof, an entire proof family, a verification profile, or a broader set of claims.
8.4 Dependency propagation
When a proof is invalidated, dependent composite proofs and audit decisions MUST be identified through the recorded dependency graph.
The system MUST NOT assume that every downstream result is automatically invalid. It MUST evaluate whether the invalidated proof was a required dependency for each affected claim.
If the dependency graph is incomplete, the affected downstream scope MUST be marked unresolved rather than assumed unaffected.
8.5 Historical report preservation
Previously issued reports MUST remain identifiable after reassessment.
A new report MUST reference the prior report and state whether it:
confirms the previous result;
narrows its verified scope;
invalidates a previous claim;
adds a new limitation;
supersedes the earlier assessment under a new profile.
The system MUST NOT silently rewrite an old report to match the latest conclusion.
8.6 No automatic canonical mutation
Proof invalidation MUST NOT itself modify Canonical History.
If a resulting finding requires a correction or compensating event, that operation MUST use the separately adopted History correction and Commit Authority protocols.
9. VERIFICATION-PROFILE COMPATIBILITY AND VERSION PINNING
9.1 Profile identity
Every proof and composite decision MUST identify the exact verification profile and version under which its result was established.
A mutable profile alias such as latest MUST NOT be the only reference in an audit-critical record.
9.2 Compatibility determination
Two proofs are compatible only if their declared profiles permit composition for the intended claim.
Compatibility MUST account for, where material:
History identity and ordering model;
proof type and claim semantics;
schema versions;
cryptographic algorithms and parameters;
trust policies and authority epochs;
boundary and completeness semantics;
normalization and canonicalization rules;
relevant validator and composition versions.
Matching version numbers do not, by themselves, prove compatibility.
9.3 Profile evolution
A new profile version MUST identify the requirements it changes and the implications for existing proofs.
A profile update MUST NOT silently change the meaning of a proof already issued under an earlier profile.
Historical proofs MAY remain valid under their original profile while being insufficient for a new decision requiring stronger assurance. The system MUST report these as separate claims.
9.4 Reverification
When a new profile requires re-verification, the system MUST retain the original result and record the new verification execution separately.
The new result MUST identify its inputs, profile, verifier, scope, and differences from the prior assessment.
9.5 Unsupported profiles
If a required profile or dependency cannot be loaded or verified, the system MUST NOT silently downgrade to a weaker profile.
The decision MUST remain blocked or unresolved unless the governing policy explicitly permits an alternative profile and that alternative is independently identified and evaluated.
10. AUDIT DECISION CONTRACT
10.1 Decision purpose
An audit decision evaluates whether specified evidence satisfies the requirements for a named downstream action.
It does not itself grant unrestricted authority, create a canonical event, or establish facts beyond the verified claims.
10.2 Decision states
The proposed decision vocabulary is:
ALLOW
DENY
HOLD
ALLOW_WITH_EXCEPTION
NOT_EVALUATED
ALLOW: all mandatory requirements for the specified decision are satisfied.
DENY: an applicable policy or verified finding prohibits the requested action.
HOLD: evidence, dependency, conflict, or authority status remains unresolved.
ALLOW_WITH_EXCEPTION: a formally permitted exception has been authorized and recorded.
NOT_EVALUATED: no completed decision evaluation exists.
ALLOW_WITH_EXCEPTION MUST NOT be represented as ordinary full compliance. Its scope, authorization, expiry or review condition, and residual risk MUST be recorded.
10.3 Decision record
Proposed schema:
audit_decision_id: REQUIRED
decision_subject_ref: REQUIRED
decision_purpose: REQUIRED
requested_action: REQUIRED
requested_scope: REQUIRED
required_claim_manifest_ref: REQUIRED
composite_proof_refs: REQUIRED
policy_ref: REQUIRED
decision: REQUIRED
decision_reason_codes: REQUIRED
unresolved_claim_refs: REQUIRED
exception_ref: OPTIONAL
decision_authority_ref: REQUIRED
decision_time_evidence_ref: OPTIONAL
decision_evidence_ref: REQUIRED
The exact schema remains unvalidated. A decision MUST identify the action and scope it addresses; a general-purpose ALLOW without a declared target MUST NOT be accepted.
10.4 Decision derivation
The decision evaluator MUST apply a versioned, deterministic rule set to the required claims and applicable policy.
The evaluator MUST NOT infer missing evidence, repair invalid proofs, or silently reinterpret the requested action.
The evaluator MUST preserve the difference between a policy violation and an inability to establish compliance.
10.5 Decision versus authorization
An audit decision MAY be a prerequisite for authorization, but MUST NOT automatically be treated as authorization unless the adopted governance contract explicitly assigns that authority to the decision mechanism.
Where Commit Authority is separate, the decision MUST be supplied as evidence to the authorization process rather than bypassing it.
10.6 Decision expiry and re-evaluation
A decision MAY be time-limited or conditional on the continued validity of specified proofs.
Where the policy requires freshness, the decision MUST identify its validity conditions. A material proof invalidation, authority revocation, profile withdrawal, or scope change MUST trigger reevaluation when required by that policy.
A decision MUST NOT be treated as perpetually valid merely because it was once issued.
11. FAILURE PROPAGATION AND BOUNDED IMPACT ANALYSIS
11.1 Failure propagation model
The system MUST distinguish a failure in an individual proof from a failure in a composite claim, a downstream decision, or Canonical History itself.
PROOF FAILURE
    |
    v
DEPENDENCY GRAPH LOOKUP
    |
    v
AFFECTED CLAIM IDENTIFICATION
    |
    v
COMPOSITE PROOF REASSESSMENT
    |
    v
AUDIT DECISION REASSESSMENT
    |
    v
DOWNSTREAM ACTION CONTROL
This flow does not authorize automatic History modification.
11.2 Impact classes
The proposed impact classes are:
Class
Meaning
LOCAL_PROOF_IMPACT
A single proof or claim is affected.
RANGE_IMPACT
A declared History range or checkpoint dependency is affected.
COMPOSITE_IMPACT
A composite proof depends on affected evidence.
DECISION_IMPACT
A prior audit decision may no longer satisfy its requirements.
PROFILE_IMPACT
A verification profile or common rule affects multiple results.
HISTORY_INTEGRITY_IMPACT
Evidence indicates a possible canonical continuity or integrity problem.
IMPACT_UNKNOWN
The dependency graph or available evidence is insufficient to bound the impact.

These classes are proposed. Their exact transition and escalation rules require adoption.
11.3 Minimum affected scope
Impact analysis SHOULD identify the smallest scope that can be justified by the dependency graph and proof semantics.
The system MUST NOT claim that the impact is limited to a single proof if shared dependencies may affect other proofs and that possibility has not been evaluated.
Likewise, a localized failure MUST NOT be used to declare the entire History invalid without supporting evidence.
11.4 Shared dependency failure
If a shared verifier, trust anchor, schema, cryptographic primitive, or profile is found defective, the system MUST identify all known results that depend on the affected component.
Where dependency tracking is incomplete, the system MUST record the uncertainty and the scope requiring investigation.
11.5 Downstream action containment
If an affected proof was a mandatory prerequisite for a downstream action, the applicable policy MUST determine whether the action is blocked, suspended, reevaluated, or allowed to continue under a documented exception.
A past ALLOW decision MUST NOT automatically authorize new actions after a relevant prerequisite has been invalidated.
The system MUST distinguish a historical action already performed from a future action that has not yet occurred. A reassessment MUST NOT retroactively erase an action from history.
11.6 Impact report
An impact report SHOULD contain:
impact_report_id: REQUIRED
trigger_ref: REQUIRED
dependency_graph_version: REQUIRED
affected_proofs: REQUIRED
affected_claims: REQUIRED
affected_ranges: REQUIRED
affected_decisions: REQUIRED
unresolved_scope: REQUIRED
containment_actions: REQUIRED
evidence_refs: REQUIRED
The report MUST distinguish confirmed dependencies from possible dependencies and unexamined scope.
12. EXCEPTION GOVERNANCE
12.1 Exception conditions
An exception MAY be permitted only when the applicable governance policy explicitly allows it.
An exception MUST NOT be used to silently waive a hard invariant, manufacture a missing proof, or redefine a failed check as successful.
12.2 Required exception record
An exception SHOULD identify:
exception_id: REQUIRED
target_requirement_refs: REQUIRED
target_claim_refs: REQUIRED
requested_scope: REQUIRED
reason: REQUIRED
risk_assessment_ref: REQUIRED
compensating_controls: REQUIRED
authorizing_identity: REQUIRED
governing_policy_ref: REQUIRED
effective_conditions: REQUIRED
expiry_or_review_condition: REQUIRED
evidence_refs: REQUIRED
The exception schema and approval workflow remain design proposals.
12.3 Exception limits
An exception MUST be limited to the declared subject, scope, purpose, and conditions. It MUST NOT automatically propagate to other histories, ranges, profiles, or decisions.
An exception MUST NOT establish that an unmet technical requirement has been satisfied. It records a separate governance decision permitting a bounded departure from a requirement, where such departure is allowed.
12.4 Prohibited exceptions
Under this proposed contract, an exception MUST NOT:
fabricate or replace missing historical evidence;
silently rewrite Canonical History;
bypass a mandatory exclusive-authority requirement;
conceal a known conflicting History;
falsely label an unverified proof as verified;
convert an unresolved commit status into a confirmed commit;
suppress a required audit finding.
12.5 Exception expiry and revocation
An exception MUST have an explicit validity condition, expiry, or review mechanism. If its prerequisites cease to hold, the applicable decision MUST be reevaluated.
Exception revocation MUST be recorded as a new governance event or decision. It MUST NOT delete the historical record of the exception.
13. END-TO-END PROOF AND DECISION REPRODUCIBILITY
13.1 Reproduction objective
An independent evaluator SHOULD be able to reconstruct why a decision was reached from its declared inputs and rules, without relying on hidden mutable state.
The reproducibility target is the decision procedure and its evidence—not merely a summary sentence or a Boolean output.
13.2 Required reproducibility inputs
A reproducible decision record MUST identify, as required by its profile:
the requested action and scope;
the required-claim manifest;
all composite and subproof references;
the verification profiles and versions;
the applicable policy version;
the proof-composition rule version;
the decision evaluator version;
the relevant trust and schema bundles;
the recorded inputs and evaluation results;
any exception or override decision.
13.3 Deterministic evaluation
The decision evaluator SHOULD be deterministic for a fixed set of canonicalized inputs, profile versions, and policy rules.
If environmental or external state affects the decision, the evaluator MUST identify that state and record sufficient evidence to explain the observed outcome.
A nondeterministic evaluation MUST NOT be presented as deterministic merely because repeated runs happened to produce the same result.
13.4 Decision comparison
When two executions disagree, the comparison MUST identify differences in:
input proof identities or content;
verification outcomes;
policy and profile versions;
dependency resolution;
exception state;
evaluation environment;
decision rules.
The system MUST NOT select the favorable result without an explicit adjudication rule.
13.5 Audit trail
The system MUST preserve the relationship between the decision and the evidence used to reach it.
Where a later decision supersedes an earlier one, both decisions MUST remain distinguishable, and the superseding decision MUST identify its predecessor and reason.
13.6 Reproducibility limits
Reproducing a decision proves that the declared procedure yields a particular result from the declared inputs, subject to the execution and trust assumptions.
It does not independently prove that the inputs accurately represented external reality or that the decision policy itself was correct.
14. INVARIANTS — STI-190-01..20
All invariants below are proposed and unverified.
ID
Invariant
Violation consequence
STI-190-01
Every proof identifies a typed claim, subject, and scope.
Proof rejected
STI-190-02
Proof validity is established by verification, not by self-asserted status.
Result rejected
STI-190-03
Proof identity is distinct from event identity.
Identity conflict
STI-190-04
A proof cannot be applied outside its verified scope without an explicit composition rule.
Scope expansion rejected
STI-190-05
Checkpoint issuance and checkpoint verification remain distinct.
Checkpoint claim unresolved
STI-190-06
Checkpoint finality requires the adopted authority and finality conditions.
Finality not established
STI-190-07
A successor checkpoint cannot silently replace a conflicting checkpoint.
Conflict adjudication required
STI-190-08
Range composition verifies History identity, boundaries, continuity, and required completeness.
Composite proof rejected
STI-190-09
A verified prefix does not imply that the suffix is verified.
Scope claim rejected
STI-190-10
Composite validity requires every mandatory dependency and composition condition.
Composite proof invalid or unresolved
STI-190-11
Integrity, authenticity, authorization, continuity, policy, and semantic claims remain distinct.
Claim composition rejected
STI-190-12
Contradictory claims are not resolved by arrival order or arbitrary preference.
Claim remains unresolved
STI-190-13
Proof invalidation does not itself modify Canonical History.
Operation blocked
STI-190-14
Invalidated dependencies trigger bounded downstream reassessment.
Dependent decisions marked unresolved
STI-190-15
Proofs and decisions identify exact profile versions.
Compatibility unverified
STI-190-16
Unsupported profiles cannot silently downgrade verification requirements.
Decision blocked
STI-190-17
Audit decisions are scoped and distinct from authorization and commit.
Decision cannot authorize by implication
STI-190-18
Exceptions remain explicit, bounded, and separately authorized.
Exception rejected
STI-190-19
Decision reproducibility depends on identified inputs and versioned rules.
Reproducibility claim rejected
STI-190-20
Historical proofs, decisions, and adjudications remain traceable after reassessment.
Audit trail integrity violation

INVARIANT_SET:
  prefix: STI-190
  count: 20
  status: PROPOSED
  verification: NOT_EXECUTED
  acceptance: NOT_ASSESSED
15. TEST CANDIDATES — ST-190-01..20
These are proposed test cases. No test implementation or execution is claimed.
Test ID
Scenario
Expected result
ST-190-01
Submit a proof without a typed claim or explicit scope.
Proof rejected.
ST-190-02
Set a proof's declared result to VALID without verification evidence.
Self-asserted status is not accepted.
ST-190-03
Reuse a proof ID for materially different proof contents.
Identity conflict detected.
ST-190-04
Apply a valid proof to a different History.
Scope validation fails.
ST-190-05
Issue a checkpoint without satisfying the required finality conditions.
Finality remains unestablished.
ST-190-06
Verify a checkpoint signature without verifying its range and authority claims.
Only the verified dimensions pass.
ST-190-07
Supply conflicting successor checkpoints.
Both are preserved; adjudication required.
ST-190-08
Compose two ranges with an unexplained gap.
Composite continuity fails.
ST-190-09
Verify a prefix while the requested suffix remains unavailable.
Prefix may pass; suffix remains unverified.
ST-190-10
Compose valid subproofs using an incompatible composition profile.
Composite proof rejected.
ST-190-11
Supply an integrity proof without required authorization evidence.
Integrity may pass; authorization remains unverified.
ST-190-12
Supply contradictory claims about the same event and scope.
Conflict detected; no arbitrary winner.
ST-190-13
Invalidate a proof that does not affect an independent History range.
Only justified dependent scope is reassessed.
ST-190-14
Invalidate a proof required by a prior audit decision.
Dependency and decision impact identified.
ST-190-15
Replace a pinned verification profile with a different version.
Compatibility or re-verification required.
ST-190-16
Request verification using an unsupported profile.
No silent downgrade.
ST-190-17
Treat an audit ALLOW as a canonical commit authorization without the required authority.
Authorization boundary blocks the operation.
ST-190-18
Submit an exception without an authorized decision or defined scope.
Exception rejected.
ST-190-19
Repeat decision evaluation with changed policy inputs but unchanged input manifest.
Reproducibility or manifest validation fails.
ST-190-20
Supersede a decision after proof invalidation.
Prior decision remains traceable; new decision records the change.

15.1 Execution requirements
Every executed test MUST identify the implementation revision, test version, fixtures, applicable verification profile, expected behavior, observed behavior, and supporting evidence.
TEST_SET:
  prefix: ST-190
  count: 20
  status: NOT_EXECUTED
  recorded_pass_count: 0
  recorded_fail_count: 0
  acceptance: NOT_ASSESSED
16. OPEN ISSUES — OI-190-01..20
All issues remain open.
Issue ID
Unresolved decision
OI-190-01
Formal proof-object schema and identity semantics
OI-190-02
Proof immutability, versioning, and supersession rules
OI-190-03
Formal checkpoint-finality protocol
OI-190-04
Checkpoint authority, succession, and conflict resolution
OI-190-05
Selected range-proof construction and completeness semantics
OI-190-06
Formal composition rules for heterogeneous proof types
OI-190-07
Aggregate claim precedence and unresolved-state semantics
OI-190-08
Semantic evidence requirements and LLM proposal boundaries
OI-190-09
Proof invalidation triggers and effective scope
OI-190-10
Dependency graph completeness and downstream impact analysis
OI-190-11
Verification-profile compatibility algorithm
OI-190-12
Historical proof re-verification and profile migration
OI-190-13
Audit decision authority and separation from Commit Authority
OI-190-14
Decision freshness, expiry, and reevaluation conditions
OI-190-15
Exception eligibility, authority, and expiry policy
OI-190-16
Deterministic decision evaluation and canonical serialization
OI-190-17
Shared dependency failures and impact containment
OI-190-18
Decision supersession and long-term audit-trail retention
OI-190-19
Relationship between proof invalidation and prior downstream actions
OI-190-20
End-to-end compatibility with STEP-187, STEP-188, and STEP-189

OPEN_ISSUES:
  prefix: OI-190
  count: 20
  status: OPEN
  production_blocking: true
17. ACCEPTANCE GATES — AG-190-01..20
All gates remain NOT_ASSESSED.
Gate ID
Required evidence
AG-190-01
Validated proof schema and identity enforcement
AG-190-02
Proof verification independent of producer assertions
AG-190-03
Proof immutability and version-conflict tests
AG-190-04
Scope containment and scope-expansion rejection
AG-190-05
Checkpoint issuance and verification separation
AG-190-06
Checkpoint finality and authority validation
AG-190-07
Conflicting checkpoint preservation and adjudication
AG-190-08
Range-proof continuity and completeness tests
AG-190-09
Verified-prefix and unverified-suffix isolation
AG-190-10
Composite proof validation across all mandatory dependencies
AG-190-11
Cross-claim-type composition and non-escalation tests
AG-190-12
Contradictory-claim detection and adjudication
AG-190-13
Proof invalidation without canonical mutation
AG-190-14
Dependency-based downstream impact analysis
AG-190-15
Verification-profile pinning and compatibility checks
AG-190-16
Unsupported-profile and downgrade prevention
AG-190-17
Audit decision and Commit Authority separation
AG-190-18
Exception authorization and bounded-scope enforcement
AG-190-19
Reproducible audit decision execution
AG-190-20
End-to-end traceability and historical decision preservation

ACCEPTANCE:
  prefix: AG-190
  count: 20
  status: NOT_ASSESSED
  required_for_freeze: true
  automatic_acceptance: false
A gate MUST be backed by traceable verification evidence. A schema passing validation is insufficient to establish cryptographic correctness, semantic validity, or end-to-end authorization correctness.
An unresolved upstream protocol dependency MUST block the affected gate unless an explicit, formally adopted alternative satisfies the same requirement.
18. PROPOSED ARTIFACT TREE
The following layout is proposed. No files have been created, and no repository changes have been made.
contracts/
└── step-190/
    ├── canonical_history_proof_protocol_contract.md
    ├── schemas/
    │   ├── proof_object.schema.json
    │   ├── proof_claim.schema.json
    │   ├── checkpoint_record.schema.json
    │   ├── range_composition.schema.json
    │   ├── proof_invalidation.schema.json
    │   ├── audit_decision.schema.json
    │   └── exception_record.schema.json
    ├── invariants/
    │   └── sti-190.yaml
    ├── tests/
    │   ├── test_catalog.yaml
    │   ├── fixtures/
    │   ├── invalid_proofs/
    │   └── expected_results/
    ├── protocols/
    │   ├── checkpoint_finality.md
    │   ├── range_proof_composition.md
    │   ├── claim_composition.md
    │   ├── proof_invalidation.md
    │   └── failure_propagation.md
    ├── profiles/
    │   ├── proof_type_registry.yaml
    │   ├── profile_compatibility.yaml
    │   └── composition_rules.yaml
    ├── decisions/
    │   ├── audit_decision_contract.md
    │   ├── exception_governance.md
    │   └── decision_reproducibility.md
    ├── issues/
    │   └── oi-190.yaml
    ├── acceptance/
    │   └── ag-190.yaml
    └── adjudication/
        └── step-190-status.yaml
18.1 Artifact constraints
Schemas define structural constraints; dedicated validators MUST enforce cross-record invariants and proof composition.
Proof registries MUST NOT accept a proof type merely because its label is recognized.
Every composite proof MUST preserve references to its exact dependencies.
Every decision MUST identify its required claims, governing policy, and evaluation result.
Exceptions MUST be separate records and MUST NOT overwrite failed requirements.
Test fixtures MUST remain distinguishable from production verification evidence.
Artifact creation or successful schema validation MUST NOT imply formal adoption.
19. DEPENDENCY MATRIX
Dependency
Required relationship
Status
STEP-182
Earlier authority and governance requirements
NOT_VERIFIED
STEP-183
Earlier lifecycle and state requirements
NOT_VERIFIED
STEP-184
Validation and policy requirements
NOT_VERIFIED
STEP-185
Evidence and integrity requirements
NOT_VERIFIED
STEP-186
History and recovery requirements
NOT_VERIFIED
STEP-187
Distributed Commit, authority, ordering, recovery
DRAFT_DEPENDENCY; COMPATIBILITY NOT_VERIFIED
STEP-188
Commit finality, History correction, retention
DRAFT_DEPENDENCY; COMPATIBILITY NOT_VERIFIED
STEP-189
Verification claims, checkpoints, trust, audit reproducibility
DRAFT_DEPENDENCY; COMPATIBILITY NOT_VERIFIED
Commit Authority
Separate authorization and canonical mutation boundary
NOT_VERIFIED
Canonical History / WAL
Authoritative event identity and continuity
NOT_VERIFIED
Policy Registry
Versioned requirements and exception rules
NOT_VERIFIED
Trust / Key Lifecycle
Historical identity and cryptographic trust
NOT_VERIFIED
Proof / Verification Layer
Proof construction, validation, composition
NOT_VERIFIED
Audit / Evidence Store
Immutable evidence references and report retention
NOT_VERIFIED
Replay / Projection
Derived-state verification without canonical mutation
NOT_VERIFIED
Schema / Validator Layer
Structural and semantic contract enforcement
NOT_VERIFIED

19.1 Upstream dependency rule
STEP-190 does not assume that STEP-187, STEP-188, or STEP-189 has been adopted.
The following dependencies remain especially significant:
STEP-187: Commit Finality must be defined before checkpoint finality can rely on canonical commit evidence.
STEP-188: Correction, authority transfer, and evidence retention must define how historical changes in assessment are recorded.
STEP-189: Verification claims, trust evaluation, and proof provenance must provide the evidence consumed by the composition protocol.
A downstream contract MUST NOT convert an unresolved upstream requirement into an assumed guarantee.
20. ADJUDICATION
STEP_ID: 190

SPECIFICATION:
  draft_created: true
  proof_object_model_proposed: true
  checkpoint_protocol_proposed: true
  range_composition_rules_proposed: true
  claim_composition_rules_proposed: true
  invalidation_model_proposed: true
  audit_decision_model_proposed: true
  exception_governance_proposed: true
  invariants_catalogued: true
  test_candidates_catalogued: true
  open_issues_catalogued: true
  acceptance_gates_catalogued: true

REPOSITORY:
  inspection: NOT_PERFORMED
  artifacts_created: false
  schema_validation: NOT_EXECUTED
  implementation_validation: NOT_EXECUTED
  test_execution: NOT_EXECUTED

GOVERNANCE:
  normative_status: PROPOSED
  adoption: NOT_ADOPTED
  canonical_mutation: NONE
  dependency_closure: NOT_VERIFIED

ACCEPTANCE:
  verified_invariants: 0
  recorded_test_passes: 0
  accepted_gates: 0
  resolved_open_issues: 0
  global_acceptance: NOT_ASSESSED

FREEZE:
  status: NOT_AUTHORIZED
  blockers:
    - CHECKPOINT_FINALITY_PROTOCOL_UNRESOLVED
    - RANGE_PROOF_CONSTRUCTION_UNSELECTED
    - COMPOSITE_PROOF_RULES_UNVALIDATED
    - PROFILE_COMPATIBILITY_UNRESOLVED
    - AUDIT_DECISION_AUTHORITY_UNVERIFIED
    - EXCEPTION_GOVERNANCE_UNADOPTED
    - UPSTREAM_DEPENDENCY_COMPATIBILITY_UNVERIFIED
The zero counts represent the absence of verified results in this draft. They are not claims about uninspected repository state.
20.1 Design conclusion
STEP-190 proposes a separation of four mechanisms:
Proof verification establishes whether a declared proof supports a bounded claim.
Proof composition establishes whether the required claims jointly support a larger claim.
Audit decision evaluates those claims against a declared policy for a specified action.
Authorization and commit remain governed by their own authority and canonical mutation protocols.
This prevents the existence of a valid subproof, a successful audit, or a signed checkpoint from silently acquiring authority it was never granted.
STEP-190 status: draft complete. Adoption, implementation, validation, acceptance, and Freeze remain unestablished.
21. NEXT STEP
STEP-191 — Canonical History Decision Enforcement / Authorization Binding / Commit Admission / Policy Execution Contract
The next draft should define the boundary between a valid audit decision and the actual authorization and admission of an operation into Canonical History.
Planned scope:
Binding an audit decision to a specific action, subject, and scope.
Authorization tokens or decision evidence and their exact semantics.
Decision freshness, expiry, revocation, and replay prevention.
Policy evaluation and deterministic enforcement.
Commit admission preconditions and rejection semantics.
Atomic binding between authorization and the attempted operation.
Time-of-check/time-of-use (TOCTOU) prevention.
Idempotent authorization and commit retry behavior.
Separation of admission, authorization, and commit finality.
Auditable denial, exception, and recovery paths.
Governing constraints:
VALID_PROOF != AUDIT_DECISION
AUDIT_DECISION != AUTHORIZATION
AUTHORIZATION != COMMIT_ADMISSION
COMMIT_ADMISSION != COMMIT_FINALITY
STALE_DECISION != CURRENT_PERMISSION
REVOKED_AUTHORITY != VALID_AUTHORIZATION
REJECTION => NO_CANONICAL_MUTATION
STEP-191 must preserve the existing status discipline: all requirements remain proposals until explicitly adopted, implemented, and verified. No upstream draft may be treated as a production guarantee without evidence of compatibility and acceptance.
