# **STEP-189 — Canonical History Verification / Long-Term Proof / Evidence Preservation / Audit Reproducibility Contract**

STEP\_ID: 189  
VERSION: 0.1.0-draft  
STATUS: DRAFT\_COMPLETE  
NORMATIVE\_STATUS: PROPOSED  
ADOPTION\_STATUS: NOT\_ADOPTED  
IMPLEMENTATION\_STATUS: NOT\_VERIFIED  
TEST\_STATUS: NOT\_EXECUTED  
REPOSITORY\_INSPECTION: NOT\_PERFORMED  
HISTORY\_PROOF\_VALIDATION: NOT\_EXECUTED  
CHECKPOINT\_VALIDATION: NOT\_EXECUTED  
TRUST\_CHAIN\_VALIDATION: NOT\_EXECUTED  
CRYPTOGRAPHIC\_MIGRATION\_VALIDATION: NOT\_EXECUTED  
ARCHIVE\_VERIFICATION: NOT\_EXECUTED  
AUDIT\_REPRODUCIBILITY\_VALIDATION: NOT\_EXECUTED  
INDEPENDENT\_VERIFICATION: NOT\_EXECUTED  
CANONICAL\_MUTATION: NONE  
GLOBAL\_ACCEPTANCE: NOT\_ASSESSED  
FREEZE\_STATUS: NOT\_AUTHORIZED  
TIMEZONE: Asia/Tokyo

## **1\. PURPOSE**

STEP-189 proposes a normative contract for producing, preserving, independently verifying, and reproducing claims about Canonical History.

The objective is to establish an auditable relationship between:

CANONICAL HISTORY  
    \-\> COMMIT EVIDENCE  
    \-\> CONTINUITY / CHECKPOINT PROOFS  
    \-\> HISTORICAL TRUST MATERIAL  
    \-\> VERIFICATION EXECUTION  
    \-\> AUDIT REPORT  
    \-\> INDEPENDENT REPRODUCTION

The contract MUST distinguish a verification result from the truth of every claim that the result concerns. A verifier can establish that evidence satisfies a declared profile without proving that the underlying real-world event occurred as described.

### **1.1 Architectural axioms**

HISTORY\_IS\_CANONICAL  
PROJECTION\_IS\_DERIVED  
EVIDENCE\_IS\_NOT\_AUTHORITY  
VERIFICATION\_IS\_NOT\_AUTHORIZATION  
VERIFICATION\_IS\_NOT\_COMMIT  
CRYPTOGRAPHIC\_VALIDITY\_IS\_NOT\_SEMANTIC\_VALIDITY  
CHECKPOINT\_VALIDITY\_IS\_NOT\_FULL\_HISTORY\_VALIDITY  
REPLICA\_AGREEMENT\_IS\_NOT\_CANONICAL\_AUTHORITY  
AUDIT\_REPRODUCIBILITY\_REQUIRES\_DECLARED\_INPUTS  
UNAVAILABLE\_EVIDENCE\_MUST\_NOT\_BE\_INVENTED  
UNKNOWN\_STATUS\_MUST\_NOT\_BE\_PROMOTED\_TO\_VALID

### **1.2 Scope**

* Verification claims and assurance profiles.  
* Evidence dependency graphs.  
* History checkpoints, range proofs, and continuity verification.  
* Historical signature and trust-anchor validation.  
* Key rotation and cryptographic algorithm migration.  
* Archive and restored-range verification.  
* Reproducible audit reports.  
* Independent verification and verifier trust.  
* Evidence availability and limitations.  
* Verification failure classification and adjudication.

### **1.3 Non-goals**

* Declaring any existing History valid without inspecting its artifacts.  
* Selecting a specific production cryptographic algorithm or storage system.  
* Treating a cryptographically valid signature as proof of semantic correctness.  
* Reconstructing missing canonical events from projections.  
* Automatically repairing or modifying Canonical History.  
* Establishing legal admissibility or jurisdiction-specific compliance.  
* Declaring implementation, adoption, acceptance, or Freeze.

## **2\. NORMATIVE VOCABULARY AND CLAIM MODEL**

The keywords `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY` are proposed normative terms. They are not binding until formally adopted.

### **2.1 Verification claim**

Every verification result MUST be scoped to an explicit claim. A result MUST NOT be interpreted more broadly than its claim and evidence permit.

Proposed claim structure:

claim\_id: REQUIRED  
subject\_ref: REQUIRED  
claim\_type: REQUIRED  
scope: REQUIRED  
verification\_profile\_id: REQUIRED  
evidence\_refs: REQUIRED  
result: REQUIRED  
limitations: REQUIRED

`claim_type` MUST identify the property being evaluated, such as byte integrity, event authenticity, authorization, continuity, semantic validity, or replay reproducibility.

### **2.2 Verification outcomes**

The proposed outcome vocabulary is:

VERIFIED  
FAILED  
INDETERMINATE  
PARTIALLY\_VERIFIED  
NOT\_APPLICABLE  
NOT\_EVALUATED

* `VERIFIED`: all required checks for the declared claim and scope passed.  
* `FAILED`: sufficient evidence establishes that at least one required assertion is false.  
* `INDETERMINATE`: available evidence cannot determine the result.  
* `PARTIALLY_VERIFIED`: a strict subset of the declared scope passed, and the verified and unverified subsets are identified.  
* `NOT_APPLICABLE`: the claim does not apply under the declared profile, with justification.  
* `NOT_EVALUATED`: the check was not performed.

A missing evidence object MUST NOT automatically result in `FAILED` if the available information cannot establish the claim's falsity. It MUST NOT result in `VERIFIED` either.

### **2.3 Claim conjunction**

When an overall conclusion depends on several required claims, the aggregate result MUST preserve each constituent result.

OVERALL VERIFIED  
    iff every required claim is VERIFIED  
    and the required claim set is complete  
    and the evidence dependencies are satisfied.

If any required claim is `FAILED`, the aggregate MUST NOT be `VERIFIED`. If no required claim has failed but one or more required claims remain `INDETERMINATE`, `NOT_EVALUATED`, or incomplete, the aggregate MUST NOT be `VERIFIED`.

The exact aggregate-state precedence MUST be encoded in the adopted verification profile.

## **3\. ASSURANCE PROFILES**

### **3.1 Profile identity**

Every verification execution MUST identify a versioned verification profile specifying:

verification\_profile\_id: REQUIRED  
profile\_version: REQUIRED  
required\_claim\_types: REQUIRED  
required\_evidence\_types: REQUIRED  
accepted\_algorithms: REQUIRED  
trust\_policy\_ref: REQUIRED  
continuity\_policy\_ref: REQUIRED  
failure\_policy\_ref: REQUIRED

The profile MUST state what it verifies and what it explicitly does not verify.

### **3.2 Proposed assurance levels**

| Level | Minimum claim scope | Explicit limitation |
| ----- | ----- | ----- |
| `V0_DECLARED` | Inputs, scope, and verifier configuration are identified. | No integrity guarantee is implied. |
| `V1_INTEGRITY` | Declared bytes and content references are checked. | Does not establish authority or semantic truth. |
| `V2_AUTHENTICITY` | Required cryptographic and historical trust checks pass. | Does not independently establish authorization or policy compliance. |
| `V3_AUTHORIZED_HISTORY` | Integrity, authenticity, authority, and required continuity checks pass. | Does not establish semantic truth or real-world occurrence. |
| `V4_REPRODUCIBLE_AUDIT` | Required prior claims pass and the audit procedure is independently reproducible under its declared profile. | Does not guarantee that the original evidence accurately represented the external world. |

These levels are a proposed taxonomy, not a claim that any existing system meets them. A higher level MUST include all lower-level requirements declared by the profile, or explicitly document an approved alternative.

### **3.3 No implicit assurance escalation**

A successful check at one level MUST NOT be represented as proof of a higher level.

Examples:

DIGEST MATCH  
  \!= SIGNATURE VALID

SIGNATURE VALID  
  \!= AUTHORITY VALID

AUTHORITY VALID  
  \!= POLICY COMPLIANT

POLICY COMPLIANT  
  \!= SEMANTICALLY TRUE

REPLAY MATCH  
  \!= REAL-WORLD EVENT CONFIRMED

## **4\. EVIDENCE DEPENDENCY GRAPH**

### **4.1 Evidence graph**

Verification MUST model dependencies among claims and evidence explicitly.

Claim  
  |  
  \+--\> Subject bytes  
  |  
  \+--\> Content digest / commitment  
  |  
  \+--\> Event identity and sequence  
  |  
  \+--\> Commit evidence  
  |       |  
  |       \+--\> Authority identity  
  |       \+--\> Applicable policy  
  |       \+--\> Historical trust evidence  
  |  
  \+--\> Continuity / checkpoint proof  
  |  
  \+--\> Verification profile  
  |  
  \+--\> Verifier execution evidence

This is a conceptual graph. It does not prescribe a particular graph storage format or cryptographic construction.

### **4.2 Dependency requirements**

Every required dependency MUST resolve to an identified object or an explicit unresolved state.

The verifier MUST distinguish:

* dependency present and verified;  
* dependency present but invalid;  
* dependency absent;  
* dependency inaccessible;  
* dependency not required by the profile;  
* dependency not evaluated.

A dependency MUST NOT be marked verified solely because another record references it.

### **4.3 Cycles and ambiguous dependencies**

The adopted evidence model MUST define whether dependency cycles are prohibited or require a specific proof construction. An ordinary recursive reference MUST NOT be treated as a complete proof merely because every node is reachable.

If the required proof dependencies cannot be resolved without circular assumptions, the claim MUST remain unverified.

### **4.4 Provenance**

Evidence provenance SHOULD include origin, acquisition method, content digest, custody or transfer records where relevant, and any transformation performed before verification.

Provenance establishes the declared evidence path; it does not independently prove that the evidence's original content was semantically true.

## **5\. HISTORY CHECKPOINTS AND RANGE PROOFS**

### **5.1 Checkpoint purpose**

A checkpoint MAY summarize a verified History prefix to support efficient verification of a large History.

A checkpoint MUST identify the exact History and range it represents. It MUST NOT silently stand in for later events or an unverified suffix.

Proposed checkpoint record:

checkpoint\_id: REQUIRED  
history\_id: REQUIRED  
range\_start: REQUIRED  
range\_end: REQUIRED  
terminal\_event\_ref: REQUIRED  
commit\_sequence: REQUIRED  
history\_commitment: REQUIRED  
commit\_profile\_id: REQUIRED  
checkpoint\_authority\_ref: REQUIRED  
checkpoint\_evidence\_refs: REQUIRED  
created\_at: REQUIRED

The final field set and the meaning of `history_commitment` remain design decisions pending selection of the underlying proof construction.

### **5.2 Checkpoint verification**

A verifier MUST establish, as required by the selected profile:

1. The checkpoint is bound to the expected `history_id`.  
2. Its declared range and terminal event are consistent.  
3. Its commitment can be verified against the supplied evidence.  
4. The checkpoint authority and applicable authorization evidence are valid.  
5. The checkpoint does not conceal a known gap, fork, or conflicting range.  
6. The evidence supports the precise completeness claim being made.

A checkpoint that authenticates only a terminal digest MUST NOT automatically be interpreted as proof that every intermediate event is present unless the selected construction and accompanying evidence establish that property.

### **5.3 Range verification**

A range proof MUST declare its start and end boundaries and its relationship to the History genesis or a previously verified checkpoint.

The verifier MUST distinguish:

RANGE\_CONTENT\_VERIFIED  
RANGE\_BOUNDARIES\_VERIFIED  
RANGE\_CONTINUITY\_VERIFIED  
RANGE\_AUTHORITY\_VERIFIED  
RANGE\_COMPLETENESS\_VERIFIED

A range MAY pass some of these claims and fail others. The report MUST preserve the distinction.

### **5.4 Checkpoint conflicts**

If two checkpoints for the same History and overlapping range disagree, the verifier MUST report the conflict and preserve both pieces of evidence.

The verifier MUST NOT resolve the conflict solely by choosing the latest timestamp, largest sequence, most replicas, or most recently received object.

A resolution requires an explicit adjudication policy and evidence of the applicable authority decision.

### **5.5 Checkpoint freshness**

Checkpoint freshness and checkpoint validity are separate claims.

An older checkpoint can remain valid for the prefix it authenticates while being insufficient to establish the current History tip.

Reports MUST identify the verified prefix and MUST NOT imply that an old checkpoint proves the absence of subsequent events.

## **6\. HISTORICAL SIGNATURE AND TRUST-ANCHOR VERIFICATION**

### **6.1 Historical verification context**

A historical signature MUST be evaluated against an explicitly declared verification context, not merely against the current status of a key.

The context SHOULD identify:

signature\_ref: REQUIRED  
signed\_content\_ref: REQUIRED  
signing\_key\_ref: REQUIRED  
signing\_identity\_ref: REQUIRED  
signature\_algorithm: REQUIRED  
algorithm\_parameters: REQUIRED  
claimed\_signing\_time: REQUIRED  
trusted\_time\_evidence\_ref: OPTIONAL  
authority\_epoch: REQUIRED  
historical\_trust\_policy\_ref: REQUIRED  
revocation\_evidence\_refs: REQUIRED

A claimed signing time supplied by the signer MUST NOT be treated as independently authenticated time evidence.

### **6.2 Verification dimensions**

The verifier MUST separate:

1. Cryptographic signature validity.  
2. Binding between the key and the claimed identity.  
3. Trust-anchor validity under the selected trust policy.  
4. Authority scope at the relevant time.  
5. Revocation or compromise status.  
6. Binding between the signature and the exact committed content.  
7. Evidence supporting the asserted signing or commit time.

Passing one dimension MUST NOT automatically pass another.

### **6.3 Historical key status**

A key that is expired or revoked at the time of verification is not automatically proof that every earlier signature made with that key was invalid. Conversely, a signature that mathematically verifies does not establish that the key was trusted or authorized at the relevant time.

The verifier MUST apply the adopted historical trust policy and report the evidence supporting its conclusion.

Where the time of signing, commit, or compromise cannot be established with the required confidence, the affected historical trust claim MUST remain `INDETERMINATE` unless the governing policy explicitly defines another defensible result.

### **6.4 Trust-anchor changes**

Trust-anchor replacement, certificate-chain changes, and governance-policy updates MUST be versioned and auditable.

A current trust anchor MUST NOT silently be substituted for the trust anchor that governed a historical verification claim.

If an old trust anchor is no longer trusted, the system MUST distinguish:

* the historical result produced under the earlier trust policy;  
* the result under the current trust policy;  
* any new evidence that changes the assessment;  
* the reason for the reassessment.

Historical reports MUST remain identifiable even when a later report reaches a different conclusion.

### **6.5 Signature verification limits**

The verification report MUST state that a valid signature establishes a cryptographic relationship under specified assumptions. It does not independently prove:

* that the signer was authorized for the operation;  
* that the signed content was accurate;  
* that the claimed external event occurred;  
* that the commit protocol achieved its required finality;  
* that no unauthorized alternative History exists.

## **7\. CRYPTOGRAPHIC ALGORITHM MIGRATION AND LONG-TERM PROOFS**

### **7.1 Migration trigger**

Cryptographic migration MAY be required because of algorithm deprecation, key compromise, implementation weakness, policy changes, or the inability to verify legacy evidence with supported tooling.

Migration MUST be treated as an auditable transformation of verification evidence, not as an opportunity to silently replace historical facts.

### **7.2 Migration record**

A migration record SHOULD identify:

migration\_id: REQUIRED  
subject\_history\_ref: REQUIRED  
subject\_range: REQUIRED  
source\_algorithm\_profile: REQUIRED  
target\_algorithm\_profile: REQUIRED  
source\_evidence\_refs: REQUIRED  
transformation\_method: REQUIRED  
tool\_identity: REQUIRED  
tool\_version: REQUIRED  
execution\_evidence\_ref: REQUIRED  
target\_evidence\_refs: REQUIRED  
source\_verification\_result: REQUIRED  
target\_verification\_result: REQUIRED  
limitations: REQUIRED

This is a proposed record shape. It does not mandate a particular signature, timestamping, hashing, or proof-renewal scheme.

### **7.3 Preserve the source**

Where permitted by retention and security policy, migration MUST preserve the original evidence or retain an authenticated reference sufficient to identify exactly what was migrated.

New cryptographic evidence MUST be distinguishable from original commit evidence.

A newly generated signature over an old event MUST NOT be represented as the original signature or as proof that the new signing key authorized the historical commit.

### **7.4 Algorithm-transition proof**

The migration procedure MUST establish what the new evidence proves and what it cannot prove.

For example, re-hashing retained bytes with a new digest algorithm can establish a new content commitment to those bytes. It does not, by itself, prove that the bytes were unchanged during any period before the new commitment was created.

Likewise, signing an old record with a current key can attest to a present-day assessment of that record; it cannot independently establish historical authenticity at the original commit time.

### **7.5 Weak or compromised source evidence**

If the source algorithm or key is already considered compromised, the migration MUST NOT automatically claim that the source evidence has been securely validated.

The result MUST identify whether trust is derived from independent contemporaneous evidence, previously established checkpoints, trusted timestamp evidence, custody records, or other specified mechanisms.

If no adequate evidence exists to bridge the period of uncertainty, the relevant historical claim MUST remain unverified or indeterminate.

### **7.6 Migration failure**

A failed or incomplete migration MUST preserve the original evidence and record the failure. It MUST NOT downgrade the recorded result to `VERIFIED` merely because target evidence was generated.

The migration MUST NOT modify Canonical History unless a separate, explicitly authorized canonical operation is required by another adopted contract. Ordinary proof renewal is not itself a canonical commit.

## **8\. ARCHIVE AND RESTORED-RANGE VERIFICATION**

### **8.1 Archive manifest**

Every archive intended to support Canonical History verification SHOULD provide a manifest identifying:

* logical History identity;  
* covered event range;  
* first and last event references;  
* content commitments or equivalent integrity references;  
* relevant checkpoint references;  
* schema and event-format versions;  
* commit and trust-policy references;  
* known gaps or excluded objects;  
* archive-generation procedure and version;  
* verification evidence and known limitations.

The manifest MUST NOT claim complete coverage if the archive intentionally excludes required events or evidence.

### **8.2 Archive admission**

Before an archived range is admitted as verified input for replay or audit, the verifier MUST establish the properties required by the selected profile.

At minimum, the verifier MUST check the archive's identity binding, the integrity of the supplied contents, and the declared range boundaries.

Authority and continuity verification MUST also be performed where required by the claim being made.

### **8.3 Restoration**

Restoration MUST distinguish physical restoration from verification.

ARCHIVE COPIED  
    \!= ARCHIVE INTEGRITY VERIFIED

ARCHIVE INTEGRITY VERIFIED  
    \!= RANGE COMPLETENESS VERIFIED

RANGE COMPLETENESS VERIFIED  
    \!= AUTHORIZED HISTORY VERIFIED

AUTHORIZED HISTORY VERIFIED  
    \!= SEMANTIC VALIDITY VERIFIED

A restored archive MUST NOT become canonical merely because restoration completed successfully.

### **8.4 Conflicting restored ranges**

When restored ranges overlap and disagree, both inputs MUST be preserved as evidence until the conflict is adjudicated.

The system MUST record the conflict's range, affected claims, verification results, and resolution authority.

No silent overwrite, implicit merge, or selection by modification time is permitted under this proposal.

### **8.5 Missing archive evidence**

If an archive lacks required trust material, schema definitions, predecessor references, or proof dependencies, the verifier MUST report the exact affected claims.

The presence of intact event bytes does not justify a claim that the full range is authentic, complete, or reproducible.

## **9\. AUDIT EXECUTION AND REPRODUCIBILITY**

### **9.1 Audit execution identity**

Every audit MUST be represented as a distinct execution with an immutable identifier and a declared input set.

Proposed execution record:

audit\_execution\_id: REQUIRED  
audit\_profile\_id: REQUIRED  
audit\_profile\_version: REQUIRED  
subject\_history\_id: REQUIRED  
subject\_range: REQUIRED  
input\_manifest\_ref: REQUIRED  
input\_digests: REQUIRED  
verifier\_identity: REQUIRED  
verifier\_version: REQUIRED  
configuration\_ref: REQUIRED  
trust\_store\_ref: REQUIRED  
schema\_bundle\_ref: REQUIRED  
policy\_bundle\_ref: REQUIRED  
execution\_environment\_ref: REQUIRED  
start\_time: REQUIRED  
end\_time: REQUIRED  
result\_ref: REQUIRED

The precise schema and mandatory fields MUST be finalized before implementation acceptance.

### **9.2 Deterministic inputs**

The audit MUST identify all inputs that can materially affect its result, including schemas, policies, trust anchors, verification parameters, relevant keys or public-key material, and tool versions.

An audit MUST NOT depend on an undisclosed mutable configuration or implicit external state.

Where a dynamic dependency is unavoidable, its observed value or authenticated reference MUST be recorded to the extent required for reproducibility.

### **9.3 Reproducibility classes**

The proposed classification is:

* `BITWISE_REPRODUCIBLE`: repeated executions produce identical canonicalized result bytes under the declared procedure.  
* `SEMANTICALLY_REPRODUCIBLE`: repeated executions produce equivalent normalized claims and findings under a declared comparison rule.  
* `ENVIRONMENTALLY_REPRODUCIBLE`: the procedure and required environment can be reconstructed, but identical output is not guaranteed.  
* `NOT_REPRODUCIBLE`: necessary inputs or execution dependencies are missing, unavailable, or uncontrolled.  
* `NOT_TESTED`: reproducibility has not been evaluated.

These classes MUST NOT be conflated. A system MUST NOT label an audit bitwise reproducible merely because two human-readable summaries look alike.

### **9.4 Output normalization**

If result equivalence depends on canonical serialization, the audit profile MUST identify the serialization rules, field ordering rules where applicable, treatment of absent and null fields, number representation, encoding, and normalization behavior.

Normalization MUST NOT discard differences that are material to the verification claim.

### **9.5 Independent rerun**

An independent rerun MUST use the declared input set and a verifier implementation or execution context appropriate to the independence claim.

Two executions using the same faulty implementation do not, by themselves, establish independent correctness.

The report MUST disclose shared dependencies, shared trust anchors, common libraries, common operators, and other relevant correlated failure risks.

### **9.6 Reproducibility failure**

A mismatch between two audit executions MUST produce a discrepancy record identifying the differing claims, inputs, tools, or environmental factors where ascertainable.

The system MUST NOT select the more favorable result merely because it is newer or more complete-looking.

Until adjudicated, the affected reproducibility claim MUST remain unresolved.

## **10\. INDEPENDENT VERIFICATION AND VERIFIER TRUST**

### **10.1 Verifier identity**

Every verification execution MUST identify the verifier implementation and version. Where the verification claim depends on the operator, execution host, or deployment configuration, those dependencies MUST also be identified.

Verifier identity is provenance, not proof of correctness.

### **10.2 Independence dimensions**

The contract MUST distinguish at least:

| Dimension | Independence question |
| ----- | ----- |
| Implementation | Does the second verifier use an independently implemented verification path? |
| Execution | Does it operate in an independently controlled environment? |
| Inputs | Does it obtain and verify the inputs independently? |
| Trust | Does it rely on the same trust anchors and assumptions? |
| Governance | Is the verifier controlled by the same authority being audited? |
| Evidence acquisition | Does it rely on the same potentially compromised evidence source? |

A report MUST NOT describe verification as independent without stating which dimensions were independent and which remained shared.

### **10.3 Self-attestation**

A verifier's own assertion that it is trustworthy MUST NOT be sufficient to establish its trustworthiness.

Where verifier integrity is a required claim, the profile MUST define the required evidence, such as authenticated software identity, reproducible build evidence, execution attestation, independent review, or another explicitly justified mechanism.

The existence of such evidence does not automatically establish the verifier's semantic correctness.

### **10.4 Verification of the verifier**

A high-assurance profile SHOULD define how verifier behavior is tested against known fixtures, negative cases, malformed evidence, adversarial inputs, and independently calculated expected results.

A verifier that only accepts valid examples without rejecting invalid ones MUST NOT be considered adequately validated.

### **10.5 Independence failure**

If a purported independent verifier shares a compromised dependency or cannot establish the independence conditions required by the profile, the independence claim MUST fail or remain indeterminate.

The underlying cryptographic or structural results MAY still be reported separately, with the shared dependency and its consequences disclosed.

## **11\. AUDIT REPORT AND RESULT ATTESTATION**

### **11.1 Required report content**

Every completed audit MUST produce a report that identifies the claim scope, procedure, inputs, outcomes, limitations, and evidence.

Proposed report structure:

audit\_report\_id: REQUIRED  
audit\_execution\_id: REQUIRED  
history\_id: REQUIRED  
scope: REQUIRED  
verification\_profile\_id: REQUIRED  
verification\_profile\_version: REQUIRED  
claim\_results: REQUIRED  
aggregate\_result: REQUIRED  
verified\_ranges: REQUIRED  
unverified\_ranges: REQUIRED  
failed\_claims: REQUIRED  
indeterminate\_claims: REQUIRED  
not\_evaluated\_claims: REQUIRED  
dependency\_results: REQUIRED  
verifier\_identity: REQUIRED  
verifier\_version: REQUIRED  
input\_manifest\_ref: REQUIRED  
execution\_evidence\_refs: REQUIRED  
reproducibility\_class: REQUIRED  
limitations: REQUIRED  
report\_digest: REQUIRED

The report digest, where used, commits to the report representation under a declared digest scheme. It does not prove that the report's claims are correct.

### **11.2 Result attestation**

An audit report MAY be signed or otherwise authenticated. The authentication MUST bind to the exact report representation and identify the attesting authority or verifier.

An attested report establishes that the identified party issued the report under the applicable verification mechanism. It does not make every statement in the report true.

### **11.3 Aggregate-result rules**

An aggregate result MUST preserve the distinctions between:

* all required claims verified;  
* one or more required claims failed;  
* one or more required claims remain indeterminate;  
* only a subset of the requested scope was verified;  
* required checks were not performed.

The implementation MUST NOT collapse these conditions into a single Boolean `valid` field without retaining the underlying detailed results.

### **11.4 Report supersession**

A new audit report MAY supersede an earlier report for a specific decision or current assessment. It MUST NOT delete or silently replace the earlier report.

The relationship MUST identify the new report, the report it supersedes, the reason, and any changed evidence or policy.

Historical reports MUST remain distinguishable from current assessments.

## **12\. EVIDENCE AVAILABILITY, LOSS, AND LIMITATIONS**

### **12.1 Evidence states**

The evidence catalog SHOULD distinguish:

PRESENT\_AND\_ACCESSIBLE  
PRESENT\_BUT\_UNREADABLE  
PRESENT\_BUT\_INVALID  
MISSING  
ACCESS\_DENIED  
RETIRED\_UNDER\_POLICY  
DESTROYED\_WITH\_AUTHORIZATION  
LOCATION\_UNKNOWN  
NOT\_REQUIRED\_BY\_PROFILE

These are proposed classifications. Their transitions and evidentiary meaning MUST be defined by the adopted evidence policy.

### **12.2 Absence versus invalidity**

Missing evidence does not automatically prove that the historical event was invalid. However, if the evidence is required to establish a claim, the claim MUST NOT be marked `VERIFIED` without an approved alternative proof path.

The system MUST distinguish:

EVENT\_INVALID  
EVENT\_NOT\_PROVEN\_VALID  
EVENT\_STATUS\_UNKNOWN

A report MUST NOT use one of these as a synonym for another.

### **12.3 Evidence loss**

When required evidence becomes unavailable, the system MUST record:

* the affected evidence object or dependency;  
* the last known verification result, if established;  
* the current availability state;  
* the claims and ranges affected;  
* the known cause and supporting evidence;  
* any recovery or alternative verification attempt;  
* the residual limitations.

A previously established result MUST NOT be represented as though its underlying evidence were still available and independently re-verifiable when that is no longer true.

### **12.4 Authorized destruction**

Authorized destruction of evidence MUST have an auditable decision record identifying the policy, authorization, scope, and resulting verification limitations, subject to applicable confidentiality and legal requirements.

The destruction record MUST NOT contain a claim that the destroyed evidence was successfully reverified unless the required verification was actually performed and supported by retained evidence.

### **12.5 No synthetic proof**

A verifier MUST NOT generate substitute event content, invented provenance, inferred signatures, or fabricated historical evidence to fill a missing dependency.

An alternative proof MAY be accepted only if the verification profile explicitly permits it and the alternative independently satisfies the required claim.

## **13\. FAILURE CLASSIFICATION AND ADJUDICATION**

### **13.1 Failure classes**

The proposed failure taxonomy is:

| Class | Meaning | Required handling |
| ----- | ----- | ----- |
| `INPUT_INVALID` | Inputs violate required structural or identity constraints. | Stop affected verification. |
| `EVIDENCE_INVALID` | Evidence fails a required assertion. | Record the failing claim and evidence. |
| `EVIDENCE_MISSING` | A required dependency is unavailable. | Mark affected claims unresolved. |
| `TRUST_UNRESOLVED` | Historical trust cannot be established. | Preserve evidence and report uncertainty. |
| `CONTINUITY_FAILURE` | A required ordering, linkage, or completeness claim fails. | Isolate the affected range. |
| `PROFILE_INCOMPATIBLE` | Required schema, algorithm, or policy is unsupported. | Do not silently downgrade requirements. |
| `VERIFIER_FAILURE` | The verifier fails to complete reliably. | Record execution failure; do not infer subject validity. |
| `REPRODUCIBILITY_MISMATCH` | Repeated or independent runs disagree. | Preserve both results and investigate. |
| `SCOPE_INCOMPLETE` | Only part of the requested scope was checked. | Report verified and unverified portions. |
| `ADJUDICATION_REQUIRED` | Conflicting evidence requires an authorized decision. | Preserve competing evidence pending resolution. |

### **13.2 Failure isolation**

A failure in one range MUST NOT automatically invalidate unrelated ranges unless the governing proof construction establishes a dependency that makes them affected.

Conversely, successful verification of an unaffected prefix MUST NOT be used to conceal a failure in a later range.

The verifier MUST identify the minimum known affected scope without making unsupported claims about the scope of damage.

### **13.3 Adjudication authority**

Adjudication MUST be performed by an authority permitted under the applicable governance contract. A verifier MAY report evidence and proposed conclusions but MUST NOT unilaterally rewrite Canonical History.

An adjudication record SHOULD include:

adjudication\_id: REQUIRED  
subject\_claim\_refs: REQUIRED  
conflicting\_evidence\_refs: REQUIRED  
decision\_authority\_ref: REQUIRED  
governing\_policy\_ref: REQUIRED  
decision: REQUIRED  
reason: REQUIRED  
limitations: REQUIRED  
decision\_evidence\_ref: REQUIRED

### **13.4 Adjudication does not erase evidence**

Adjudication MUST preserve the evidence and previous results that led to the dispute.

A decision may resolve the current governance status of a claim without making conflicting historical evidence disappear.

### **13.5 Fail-closed boundary**

If verification is required to authorize a downstream action and the required result is not `VERIFIED`, that action MUST be blocked unless an explicitly adopted policy defines a narrower permitted exception.

Such an exception MUST be recorded as an exception decision; it MUST NOT be mislabeled as successful verification.

## **14\. INVARIANTS — STI-189-01..20**

All invariants are proposed. None has been verified by implementation or test execution.

| ID | Invariant | Violation consequence |
| ----- | ----- | ----- |
| STI-189-01 | Every verification result is bound to an explicit claim and scope. | Report rejected |
| STI-189-02 | Verification outcomes distinguish failure, uncertainty, partial verification, and non-execution. | Result invalid |
| STI-189-03 | Aggregate verification cannot exceed the assurance of its required claims. | Aggregate downgraded |
| STI-189-04 | Assurance levels cannot be inferred from weaker checks. | Assurance claim rejected |
| STI-189-05 | Required evidence dependencies are explicitly resolved or marked unresolved. | Claim remains unverified |
| STI-189-06 | Evidence references alone do not establish evidence validity. | Dependency verification required |
| STI-189-07 | Checkpoints are bound to a specific History identity and range. | Checkpoint rejected |
| STI-189-08 | A checkpoint does not imply completeness beyond its verified scope. | Scope claim rejected |
| STI-189-09 | Conflicting checkpoints are preserved and explicitly adjudicated. | Affected range unresolved |
| STI-189-10 | Historical signature validity is distinct from historical authorization. | Authorization claim evaluated separately |
| STI-189-11 | Historical trust decisions identify the applicable trust policy and evidence. | Trust claim indeterminate |
| STI-189-12 | Cryptographic migration does not silently replace original evidence. | Migration rejected |
| STI-189-13 | New signatures do not impersonate historical commit authorization. | Provenance violation |
| STI-189-14 | Archive restoration does not automatically establish canonical status. | Canonical admission blocked |
| STI-189-15 | Audit executions identify material inputs and relevant versions. | Reproducibility claim rejected |
| STI-189-16 | Reproducibility classes are explicitly distinguished. | Report classification invalid |
| STI-189-17 | Independent verification claims disclose shared dependencies. | Independence claim downgraded |
| STI-189-18 | Report authentication does not imply the report's semantic truth. | Claim scope corrected |
| STI-189-19 | Missing evidence cannot be replaced by fabricated or inferred proof. | Verification rejected |
| STI-189-20 | Adjudication preserves conflicting evidence and prior reports. | Adjudication invalid |

INVARIANT\_SET:  
  prefix: STI-189  
  count: 20  
  status: PROPOSED  
  verification: NOT\_EXECUTED  
  acceptance: NOT\_ASSESSED

## **15\. TEST CANDIDATES — ST-189-01..20**

These tests remain proposals. No execution or test results are claimed.

| Test ID | Scenario | Expected result |
| ----- | ----- | ----- |
| ST-189-01 | Submit a verification report without an explicit claim scope. | Reject the report. |
| ST-189-02 | Remove a required evidence dependency. | Result becomes unresolved, not verified. |
| ST-189-03 | Combine one verified claim with one required failed claim. | Aggregate is not verified. |
| ST-189-04 | Supply a matching digest but no required signature evidence. | Integrity may pass; authenticity remains unverified. |
| ST-189-05 | Supply an evidence reference pointing to unavailable content. | Dependency is marked unavailable. |
| ST-189-06 | Supply present evidence with an invalid digest. | Evidence integrity fails. |
| ST-189-07 | Bind a valid checkpoint to the wrong History identity. | Checkpoint rejected. |
| ST-189-08 | Verify a prefix using a checkpoint that does not cover the requested suffix. | Suffix remains unverified. |
| ST-189-09 | Supply conflicting checkpoints for overlapping ranges. | Conflict recorded; no silent selection. |
| ST-189-10 | Use a mathematically valid signature from an unauthorized identity. | Cryptographic validity and authorization produce distinct results. |
| ST-189-11 | Verify an old signature without the required historical trust evidence. | Historical trust remains unresolved. |
| ST-189-12 | Re-sign historical content with a new key and label it the original commit signature. | Provenance assertion rejected. |
| ST-189-13 | Attempt migration without adequate source-evidence verification. | Migration cannot claim full historical proof renewal. |
| ST-189-14 | Restore an archive with intact bytes but missing required range evidence. | Integrity may pass; completeness remains unverified. |
| ST-189-15 | Change a material audit input without updating the input manifest. | Execution or reproducibility validation fails. |
| ST-189-16 | Produce differing normalized results under a claimed bitwise-reproducible profile. | Bitwise reproducibility claim fails. |
| ST-189-17 | Claim independent verification while using a declared compromised shared dependency. | Independence claim fails or remains indeterminate. |
| ST-189-18 | Authenticate a report containing a false or unsupported semantic assertion. | Authentication passes only within its cryptographic scope; semantic claim does not automatically pass. |
| ST-189-19 | Attempt to fill a missing evidence dependency using LLM-generated content. | Synthetic proof rejected. |
| ST-189-20 | Resolve a checkpoint conflict by adjudication. | Both source results remain available and the decision is separately recorded. |

### **15.1 Test result requirements**

Every executed test MUST record its test version, implementation revision, fixture digest, profile version, execution outcome, observed behavior, expected behavior, and evidence references.

TEST\_SET:  
  prefix: ST-189  
  count: 20  
  status: NOT\_EXECUTED  
  recorded\_pass\_count: 0  
  recorded\_fail\_count: 0  
  acceptance: NOT\_ASSESSED

Zero recorded results means that this draft contains no execution evidence. It does not establish the state of any repository test suite.

## **16\. OPEN ISSUES — OI-189-01..20**

All issues remain open.

| Issue ID | Unresolved decision |
| ----- | ----- |
| OI-189-01 | Formal schema for verification claims and aggregate-result precedence |
| OI-189-02 | Assurance-level composition and permitted exceptions |
| OI-189-03 | Canonical representation of evidence dependency graphs |
| OI-189-04 | Required proof construction for checkpoint completeness |
| OI-189-05 | Checkpoint signing and authorization protocol |
| OI-189-06 | Fork detection and conflicting-checkpoint adjudication |
| OI-189-07 | Historical trust policy and trusted-time requirements |
| OI-189-08 | Historical revocation and compromise interpretation |
| OI-189-09 | Cryptographic algorithm migration and proof-renewal procedure |
| OI-189-10 | Treatment of weak source evidence during migration |
| OI-189-11 | Archive manifest and range-proof format |
| OI-189-12 | Requirements for restoration admission |
| OI-189-13 | Audit execution environment identity and reproducibility guarantees |
| OI-189-14 | Canonical result serialization and normalization rules |
| OI-189-15 | Definition and measurement of verifier independence |
| OI-189-16 | Evidence requirements for verifier integrity and correctness |
| OI-189-17 | Long-term evidence availability and authorized destruction |
| OI-189-18 | Verification-result retention and supersession rules |
| OI-189-19 | Failure isolation across dependent History ranges |
| OI-189-20 | Relationship between verification adjudication and downstream authorization |

OPEN\_ISSUES:  
  prefix: OI-189  
  count: 20  
  status: OPEN  
  production\_blocking: true

## **17\. ACCEPTANCE GATES — AG-189-01..20**

All gates are `NOT_ASSESSED`.

| Gate ID | Required evidence |
| ----- | ----- |
| AG-189-01 | Claim schema and explicit scope enforcement |
| AG-189-02 | Complete outcome-state and aggregate-result validation |
| AG-189-03 | Assurance-level non-escalation tests |
| AG-189-04 | Evidence dependency resolution and failure tests |
| AG-189-05 | Checkpoint identity and range binding verification |
| AG-189-06 | Checkpoint completeness and boundary proof |
| AG-189-07 | Conflicting checkpoint preservation and adjudication |
| AG-189-08 | Historical signature and trust-policy verification |
| AG-189-09 | Historical revocation and compromise handling |
| AG-189-10 | Cryptographic migration with original-evidence preservation |
| AG-189-11 | Archive manifest and integrity verification |
| AG-189-12 | Restoration and range-completeness validation |
| AG-189-13 | Deterministic audit input identification |
| AG-189-14 | Reproducibility classification and rerun evidence |
| AG-189-15 | Independent verification with disclosed shared dependencies |
| AG-189-16 | Verifier validation against positive and negative fixtures |
| AG-189-17 | Evidence-loss and destruction impact reporting |
| AG-189-18 | Authenticated audit report and claim-level traceability |
| AG-189-19 | Failure isolation and unresolved-claim preservation |
| AG-189-20 | Adjudication provenance and downstream authorization separation |

ACCEPTANCE:  
  prefix: AG-189  
  count: 20  
  status: NOT\_ASSESSED  
  required\_for\_freeze: true  
  automatic\_acceptance: false

A gate MUST NOT pass without traceable evidence. An unresolved critical issue MUST block the affected gate unless a formally authorized and documented exception applies. An exception MUST NOT be presented as proof that the original requirement was satisfied.

## **18\. PROPOSED ARTIFACT TREE**

The following layout is proposed only. No repository files or directories have been created.

contracts/  
└── step-189/  
    ├── canonical\_history\_verification\_contract.md  
    ├── schemas/  
    │   ├── verification\_claim.schema.json  
    │   ├── verification\_profile.schema.json  
    │   ├── evidence\_dependency.schema.json  
    │   ├── history\_checkpoint.schema.json  
    │   ├── cryptographic\_migration.schema.json  
    │   ├── audit\_execution.schema.json  
    │   └── audit\_report.schema.json  
    ├── invariants/  
    │   └── sti-189.yaml  
    ├── tests/  
    │   ├── test\_catalog.yaml  
    │   ├── fixtures/  
    │   ├── negative\_cases/  
    │   └── expected\_results/  
    ├── profiles/  
    │   ├── assurance\_levels.yaml  
    │   ├── historical\_trust\_profile.yaml  
    │   └── reproducibility\_profile.yaml  
    ├── verification/  
    │   ├── checkpoint\_verification.md  
    │   ├── evidence\_dependency\_rules.md  
    │   ├── cryptographic\_migration.md  
    │   ├── archive\_verification.md  
    │   └── verifier\_independence.md  
    ├── audit/  
    │   ├── execution\_contract.md  
    │   ├── report\_contract.md  
    │   └── adjudication\_contract.md  
    ├── issues/  
    │   └── oi-189.yaml  
    ├── acceptance/  
    │   └── ag-189.yaml  
    └── adjudication/  
        └── step-189-status.yaml

### **18.1 Artifact constraints**

1. JSON Schema MUST be used only for constraints it can express; cross-record proofs and cryptographic checks require separate validation.  
2. Verification profiles MUST explicitly enumerate required claims and permitted proof mechanisms.  
3. Fixture data MUST be distinguished from production evidence.  
4. Every audit report MUST reference the exact profile and execution inputs used.  
5. A report's own digest or signature MUST NOT be treated as independent proof of its contents.  
6. No artifact may grant itself canonical authority or establish its own acceptance status.  
7. A generated verification result MUST NOT modify Canonical History as a side effect.

## **19\. DEPENDENCY MATRIX**

| Dependency | Required relationship | Status |
| ----- | ----- | ----- |
| STEP-182 | Earlier governance and authority requirements | NOT\_VERIFIED |
| STEP-183 | Earlier lifecycle and state requirements | NOT\_VERIFIED |
| STEP-184 | Earlier validation requirements | NOT\_VERIFIED |
| STEP-185 | Earlier evidence and integrity requirements | NOT\_VERIFIED |
| STEP-186 | History and recovery dependencies | NOT\_VERIFIED |
| STEP-187 | Distributed Commit, ordering, replication, recovery | DRAFT\_DEPENDENCY; COMPATIBILITY NOT\_VERIFIED |
| STEP-188 | History governance, finality, correction, retention | DRAFT\_DEPENDENCY; COMPATIBILITY NOT\_VERIFIED |
| Canonical History / WAL | Stable identity, sequence, continuity | NOT\_VERIFIED |
| Commit Authority | Authoritative commit and authorization evidence | NOT\_VERIFIED |
| Policy Registry | Versioned governance and verification profiles | NOT\_VERIFIED |
| Trust / Key Lifecycle | Historical identity and cryptographic trust | NOT\_VERIFIED |
| Archive / Storage | Evidence availability and range preservation | NOT\_VERIFIED |
| Replay / Projection | Reproducible derived-state generation | NOT\_VERIFIED |
| Audit / Evidence Store | Immutable report references and evidence retrieval | NOT\_VERIFIED |
| Schema / Validator Layer | Structural and cross-record validation | NOT\_VERIFIED |

### **19.1 Dependency closure**

STEP-189 depends on STEP-188's proposed governance model but does not assume it has been adopted.

The following upstream requirements are especially important:

* STEP-187: commit finality and authoritative commit evidence.  
* STEP-188: historical trust interpretation, evidence retention, and correction governance.  
* STEP-189: the proof obligations needed to verify claims produced under those contracts.

Until these relationships are reconciled against actual versioned artifacts, cross-STEP compatibility remains unverified.

## **20\. ADJUDICATION**

STEP\_ID: 189

SPECIFICATION:  
  draft\_created: true  
  verification\_claim\_model\_proposed: true  
  assurance\_profiles\_proposed: true  
  evidence\_dependencies\_defined: true  
  checkpoint\_contract\_proposed: true  
  historical\_trust\_contract\_proposed: true  
  cryptographic\_migration\_contract\_proposed: true  
  audit\_reproducibility\_contract\_proposed: true  
  invariants\_catalogued: true  
  test\_candidates\_catalogued: true  
  open\_issues\_catalogued: true  
  acceptance\_gates\_catalogued: true

REPOSITORY:  
  inspection: NOT\_PERFORMED  
  artifacts\_created: false  
  schema\_validation: NOT\_EXECUTED  
  implementation\_validation: NOT\_EXECUTED  
  test\_execution: NOT\_EXECUTED

GOVERNANCE:  
  normative\_status: PROPOSED  
  adoption: NOT\_ADOPTED  
  canonical\_mutation: NONE  
  dependency\_closure: NOT\_VERIFIED

ACCEPTANCE:  
  verified\_invariants: 0  
  recorded\_test\_passes: 0  
  accepted\_gates: 0  
  resolved\_open\_issues: 0  
  global\_acceptance: NOT\_ASSESSED

FREEZE:  
  status: NOT\_AUTHORIZED  
  blockers:  
    \- COMMIT\_FINALITY\_DEPENDENCY\_UNVERIFIED  
    \- HISTORICAL\_TRUST\_POLICY\_UNRESOLVED  
    \- CHECKPOINT\_PROOF\_CONSTRUCTION\_UNRESOLVED  
    \- CRYPTOGRAPHIC\_MIGRATION\_UNVALIDATED  
    \- AUDIT\_REPRODUCIBILITY\_UNPROVEN  
    \- VERIFIER\_INDEPENDENCE\_UNPROVEN  
    \- RETENTION\_AND\_EVIDENCE\_DEPENDENCIES\_UNVERIFIED

The zero counts refer only to evidence recorded in this draft. They do not establish the state of any uninspected repository.

### **20.1 Design conclusion**

STEP-189 establishes a proposed distinction between four different questions:

1. Integrity: Is the evidence consistent with its declared content commitments?  
2. Authority: Was the relevant operation authorized under the applicable historical rules?  
3. Interpretation: What does the evidence support, and under which semantic contract?  
4. Reproducibility: Can another verifier reproduce the declared result from the identified inputs?

A system that answers only the first question cannot claim to have answered all four.

STEP-189 status: draft complete. Adoption, implementation, validation, acceptance, and Freeze remain unestablished.

## **21\. NEXT STEP**

### **STEP-190 — Canonical History Proof Protocol / Checkpoint Finality / Verification Composition / Audit Decision Contract**

STEP-190 should connect the governance and verification contracts into an explicit protocol for deciding when a verification result is sufficient for a downstream action.

Planned scope:

1. Formal proof-object model and typed verification claims.  
2. Checkpoint issuance, authorization, finality, and succession.  
3. Range-proof composition and verified-prefix rules.  
4. Proof invalidation and historical reassessment.  
5. Verification-profile compatibility and version pinning.  
6. Composition of integrity, authority, continuity, and semantic claims.  
7. Verification decision versus downstream authorization.  
8. Failure propagation and bounded impact analysis.  
9. Audit decision records and exception governance.  
10. Acceptance evidence for end-to-end proof composition.

Governing constraints:

PROOF\_OBJECT \!= CANONICAL EVENT  
CHECKPOINT \!= COMPLETE HISTORY  
VALID SUBPROOF \!= VALID COMPOSITE PROOF  
VERIFICATION RESULT \!= AUTHORIZATION  
AUTHORIZATION \!= COMMIT  
PROOF INVALIDATION \!= HISTORY REWRITE  
EXCEPTION \!= REQUIREMENT SATISFACTION

STEP-190 must retain the current status distinctions: design proposal, implementation, testing, adoption, canonical mutation, acceptance, and Freeze are independent states. No upstream draft may be treated as an adopted dependency without explicit evidence.