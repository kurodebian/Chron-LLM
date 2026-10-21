# **STEP-188 — Canonical History Governance / Commit Finality / Authority Transfer / History Correction / Retention and Archival Contract**

STEP\_ID: 188  
VERSION: 0.1.0-draft  
STATUS: DRAFT\_COMPLETE  
NORMATIVE\_STATUS: PROPOSED  
ADOPTION\_STATUS: NOT\_ADOPTED  
IMPLEMENTATION\_STATUS: NOT\_VERIFIED  
TEST\_STATUS: NOT\_EXECUTED  
REPOSITORY\_INSPECTION: NOT\_PERFORMED  
COMMIT\_FINALITY\_VALIDATION: NOT\_EXECUTED  
AUTHORITY\_TRANSFER\_VALIDATION: NOT\_EXECUTED  
HISTORY\_CORRECTION\_VALIDATION: NOT\_EXECUTED  
RETENTION\_VALIDATION: NOT\_EXECUTED  
ARCHIVAL\_VALIDATION: NOT\_EXECUTED  
INTEGRITY\_REVERIFICATION: NOT\_EXECUTED  
LONG\_TERM\_REPLAY\_VALIDATION: NOT\_EXECUTED  
CANONICAL\_MUTATION: NONE  
GLOBAL\_ACCEPTANCE: NOT\_ASSESSED  
FREEZE\_STATUS: NOT\_AUTHORIZED  
TIMEZONE: Asia/Tokyo

## **1\. PURPOSE**

STEP-188 defines the proposed governance contract for Canonical History across its lifecycle, including commit finality, authority transfer, correction, retention, archival, evidence preservation, integrity re-verification, and long-term replay.

Primary objective:

Preserve canonical truth, authority provenance,  
historical interpretability, and verifiability  
across failures, authority changes, corrections,  
storage migration, and long-term retention.

### **1.1 Normative architectural axioms**

HISTORY\_IS\_CANONICAL  
PROJECTION\_IS\_DERIVED  
STATE \= FOLD(HISTORY)  
REPLAY\_DOES\_NOT\_MUTATE\_HISTORY  
CORRECTION\_DOES\_NOT\_REWRITE\_HISTORY  
PROPOSAL \!= COMMIT  
VALIDATION \!= AUTHORIZATION  
AUTHORIZATION \!= COMMIT\_FINALITY  
REPLICA\_AGREEMENT \!= AUTHORITY\_AUTHORIZATION  
RETENTION \!= VERIFIABILITY  
SIGNATURE\_VALIDITY \!= SEMANTIC\_VALIDITY  
UNKNOWN\_COMMIT\_STATUS \!= COMMIT\_FAILURE

### **1.2 Scope**

* Canonical History identity and continuity.  
* Commit finality and indeterminate commit status.  
* Commit Authority transfer, revocation, expiry, and recovery.  
* Correction through appended events rather than silent rewriting.  
* Retention, archival, migration, and restoration.  
* Evidence preservation, deletion, and legal holds.  
* Long-term integrity and authenticity re-verification.  
* Replay compatibility and historical interpretation.  
* Normative evolution without retroactively changing the meaning of previously committed evidence.

### **1.3 Non-goals**

* Selecting a production database or replication protocol.  
* Defining jurisdiction-specific legal retention periods.  
* Authorizing deletion of any existing artifact.  
* Modifying current repository files or Canonical History.  
* Declaring any existing commit, signature, archive, or replay valid without verification.  
* Establishing production readiness or Freeze.

## **2\. NORMATIVE LANGUAGE AND AUTHORITY BOUNDARY**

The terms `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY` are proposed normative keywords. They acquire binding force only after formal adoption.

| Actor | Permitted responsibility | Prohibited inference |
| ----- | ----- | ----- |
| LLM | Observe, explain, propose corrections | Cannot establish canonical truth |
| Validator | Deterministic structural and policy checks | Cannot infer missing evidence |
| Commit Authority | Authorize a commit under the applicable policy | Cannot retroactively legitimize an unauthorized event |
| History Store | Preserve and expose committed records | Storage presence alone does not prove valid authorization |
| Replica / Archive | Preserve copies and report integrity | Agreement among copies does not itself authorize a commit |
| Replay Engine | Derive historical state from eligible events | Cannot silently repair or rewrite History |
| Auditor | Verify evidence and report discrepancies | A successful check does not prove untested properties |

Canonical mutation MUST be mediated by the designated Commit Authority and the applicable commit protocol. Correction, replay, migration, and archival MUST NOT bypass that boundary.

## **3\. CANONICAL HISTORY IDENTITY AND TOPOLOGY**

### **3.1 Logical identity**

A Canonical History MUST have an explicit, stable identity independent of its physical storage path.

Proposed identity tuple:

history\_id: REQUIRED  
history\_genesis\_ref: REQUIRED  
history\_format\_id: REQUIRED  
governance\_profile\_id: REQUIRED  
authority\_epoch: REQUIRED

`history_id` identifies the logical history. `history_genesis_ref` anchors its origin. Storage location, replica identifier, archive filename, and migration destination MUST NOT independently redefine that identity.

### **3.2 Event identity and continuity**

Every committed event MUST be uniquely identifiable within its declared identity scope. The History MUST provide a verifiable continuity relation between its genesis and every event claimed to belong to that History.

GENESIS  
  \-\> COMMITTED EVENT  
  \-\> COMMITTED EVENT  
  \-\> ...  
  \-\> VERIFIED HISTORY PREFIX

The exact mechanism—sequence numbers, predecessor references, hash chaining, signed checkpoints, or a combination—remains a design decision until specified and tested.

### **3.3 Fork handling**

Two histories that share a prefix but diverge MUST be represented as distinct branches or conflicting histories unless a formally adopted resolution protocol authorizes a single continuation.

The system MUST NOT silently merge divergent histories or choose one solely because it is newer, larger, more available, or stored on a preferred replica.

### **3.4 Identity violations**

A history identity mismatch, genesis mismatch, duplicate canonical sequence, invalid predecessor, or unexplained gap MUST prevent the affected range from being certified as a complete canonical continuation.

A verifier MAY report a valid prefix while separately marking the remaining suffix unverified. It MUST NOT label the entire History verified merely because the prefix passed.

## **4\. COMMIT FINALITY**

### **4.1 Distinct lifecycle states**

The following states MUST remain distinct:

PROPOSED  
  \-\> VALIDATED  
  \-\> AUTHORIZED  
  \-\> COMMIT\_ATTEMPTED  
  \-\> COMMIT\_STATUS\_UNKNOWN | COMMITTED | REJECTED  
  \-\> DURABILITY\_VERIFIED  
  \-\> REPLICATION\_STATUS\_RECORDED  
  \-\> INTEGRITY\_VERIFIED

This is a conceptual state model, not a mandated implementation sequence. In particular, replication and integrity checks may occur after a canonical commit.

* `VALIDATED`: required checks passed.  
* `AUTHORIZED`: the designated authority issued an applicable authorization.  
* `COMMIT_ATTEMPTED`: a commit operation was initiated.  
* `COMMIT_STATUS_UNKNOWN`: available evidence cannot determine whether the canonical commit occurred.  
* `COMMITTED`: authoritative evidence establishes that the event was committed.  
* `REJECTED`: authoritative evidence establishes that the operation was rejected without canonical mutation.  
* `DURABILITY_VERIFIED`: the applicable durability condition has been verified.  
* `REPLICATION_STATUS_RECORDED`: replication state is explicitly recorded; this does not imply all replicas are current.  
* `INTEGRITY_VERIFIED`: the relevant committed data and evidence passed the declared integrity checks.

### **4.2 Finality rule**

An event is canonically committed only when the applicable commit protocol supplies sufficient authoritative evidence of the commit decision and the event's placement in the canonical History.

A successful validation, authorization token, request acknowledgement, network response, local buffer write, or replica receipt MUST NOT independently be treated as proof of canonical commit finality.

The precise relationship among atomic persistence, authority authorization, sequence allocation, and commit evidence remains an unresolved protocol requirement. It MUST be specified before production adoption.

### **4.3 Unknown commit status**

When the outcome of a commit attempt is unknown:

1. The caller MUST NOT infer rejection from a timeout or lost response.  
2. The caller MUST NOT blindly issue a new commit with a new identity.  
3. The system MUST reconcile the original `proposal_id`, event identity, authority epoch, and commit evidence against the authoritative History.  
4. If the original event is confirmed committed, retries MUST resolve to that event rather than create a duplicate.  
5. If authoritative evidence establishes rejection, a retry MAY be considered under the same applicable policy.  
6. If neither outcome can be established, the operation MUST remain indeterminate and MUST NOT be reported as definitively committed or rejected.

### **4.4 Finality versus durability**

Commit finality and durability are separate claims.

A commit may be authoritative while its replication is incomplete. Conversely, multiple durable copies may exist without valid authorization to establish a canonical commit.

The commit profile MUST declare which durability guarantees apply and what evidence proves them. A stronger guarantee MUST NOT be inferred from a weaker profile.

## **5\. COMMIT AUTHORITY TRANSFER, REVOCATION, AND RECOVERY**

### **5.1 Authority identity**

Every commit MUST be attributable to an authority identity and the applicable authority epoch or equivalent versioned governance context.

The system MUST be able to distinguish:

* the identity that authorized the commit;  
* the credential or mechanism used to establish that identity;  
* the policy under which authorization was granted;  
* the authority epoch in force;  
* the evidence used to verify the authorization.

A valid credential alone MUST NOT imply that the holder was authorized for every History, event type, time interval, or operation.

### **5.2 Transfer protocol**

An authority transfer MUST define:

TRANSFER\_REQUEST  
  \-\> SUCCESSOR\_VALIDATION  
  \-\> TRANSFER\_AUTHORIZATION  
  \-\> OLD\_AUTHORITY\_FENCING  
  \-\> EPOCH\_TRANSITION  
  \-\> SUCCESSOR\_ACTIVATION  
  \-\> TRANSFER\_EVIDENCE  
  \-\> POST-TRANSFER\_VERIFICATION

The concrete ordering and atomicity mechanism MUST be specified by the implementation contract. The sequence above is a proposed logical lifecycle.

### **5.3 Exclusivity and fencing**

At any point where the protocol requires a single active Commit Authority, the system MUST prevent an old or partitioned authority from continuing to commit under stale authority state.

A transfer MUST NOT be considered complete merely because the successor has received a key or configuration file. It requires evidence that the authority transition and the applicable fencing conditions have taken effect.

If exclusive authority cannot be established, the system MUST fail closed for operations requiring exclusivity.

### **5.4 Revocation and compromise**

Revocation MUST specify its effective scope and effective point. The system MUST distinguish:

* revocation of future authorization;  
* compromise discovered after an event was committed;  
* expiration of a credential;  
* invalidation of a signing key;  
* invalidation of an authority's governance mandate.

Revocation MUST NOT silently erase historical commits. Historical events MUST instead be evaluated under the applicable historical trust and revocation policy, with findings recorded separately.

### **5.5 Recovery**

Authority recovery MUST establish the authoritative History position, current authority epoch, unresolved commit attempts, and any known split-brain or compromise interval before new commits resume.

Recovery MUST NOT treat a replica's most recent timestamp or highest sequence as sufficient proof of canonical authority.

## **6\. HISTORY CORRECTION AND COMPENSATING EVENTS**

### **6.1 Immutability rule**

A committed event MUST NOT be silently overwritten, removed, reordered, or rewritten in place to make the History appear corrected.

If a committed event is erroneous, the correction MUST preserve the original event and append a correction record or compensating event under the applicable authority and policy.

E1: ORIGINAL COMMIT  
E2: CORRECTION / COMPENSATION  
E3: SUBSEQUENT COMMIT

The original remains part of the historical record. The derived state MAY change when the correction is applied during replay, but the underlying historical fact that the original event was committed MUST remain visible.

### **6.2 Correction record**

A correction record SHOULD contain:

correction\_id: REQUIRED  
target\_event\_refs: REQUIRED  
correction\_type: REQUIRED  
reason\_code: REQUIRED  
evidence\_refs: REQUIRED  
proposed\_by: REQUIRED  
authorized\_by: REQUIRED  
policy\_version: REQUIRED  
effective\_semantics: REQUIRED  
committed\_event\_ref: REQUIRED

This is a proposed schema shape, not an implemented schema. Fields, cardinality, and cryptographic requirements remain subject to contract validation.

### **6.3 Correction types**

The contract MUST distinguish at least:

* `FACTUAL_CORRECTION`: records that an earlier claim or value was incorrect.  
* `COMPENSATING_EVENT`: records a subsequent action that offsets a prior effect.  
* `INTERPRETATION_CORRECTION`: changes the interpretation of historical evidence without rewriting it.  
* `AUTHORIZATION_FINDING`: records that a prior action's authorization status is disputed, invalidated, or newly assessed.  
* `RETRACTION`: records that a prior claim is withdrawn while preserving its historical occurrence.

These categories MUST NOT be conflated. In particular, a compensating event does not establish that the original event never occurred.

### **6.4 Correction authorization**

Correction MUST undergo the applicable validation and authorization process. A request from the same actor who caused the original event MUST NOT automatically authorize its correction.

Correction evidence MUST identify the target event unambiguously. An ambiguous target, unsupported correction reason, missing required evidence, or invalid authority MUST block canonical correction.

### **6.5 Historical and derived views**

Consumers MUST be able to distinguish:

1. the original committed event;  
2. the correction or compensating event;  
3. the derived state before correction;  
4. the derived state after correction;  
5. the policy and replay rules used to calculate each view.

A corrected projection MUST NOT be presented as though the original event had never existed.

## **7\. RETENTION, ARCHIVAL, AND MIGRATION**

### **7.1 Retention policy**

Every governed History MUST have an explicit retention policy identifying its scope, version, responsible authority, applicable retention classes, and deletion constraints.

A missing retention policy MUST NOT be interpreted as permission to delete.

Retention periods and legally mandated exceptions are deployment-specific and are not established by this draft.

### **7.2 Archival**

Archival MAY relocate or re-encode stored data, but MUST preserve the ability to establish:

* logical History identity;  
* event identity and ordering;  
* provenance and authority evidence;  
* content integrity;  
* completeness of the archived range;  
* links to predecessor and successor ranges;  
* applicable schema and policy versions.

A successful copy operation alone MUST NOT be considered a verified archive.

### **7.3 Migration**

A migration MUST declare its source range, destination representation, transformation rules, tool/version identity, and verification results.

When the data format changes, the migration MUST preserve either the original canonical representation or sufficient authenticated evidence to verify the transformation against that representation.

A migration MUST NOT silently drop unknown fields, unresolved records, provenance, signatures, or evidence references.

If lossless transformation cannot be established, the output MUST be labeled as a derived or incomplete representation rather than silently replacing the authoritative source.

### **7.4 Archive restoration**

Restoration MUST verify identity, continuity, integrity, and required evidence before a restored range is admitted as an authoritative continuation.

A restored archive MUST NOT supersede a newer authoritative History solely because it is easier to access.

If two restored copies disagree, the discrepancy MUST be recorded and adjudicated. The system MUST NOT silently choose a winner.

### **7.5 Retention versus verifiability**

The system MUST separately record:

DATA\_RETAINED  
INTEGRITY\_VERIFIABLE  
AUTHORITY\_VERIFIABLE  
SCHEMA\_INTERPRETABLE  
REPLAY\_EXECUTABLE  
REPLAY\_EQUIVALENCE\_VERIFIED

These properties are independent. Retaining bytes does not guarantee that the required keys, schemas, validators, policy definitions, or replay engines remain available.

## **8\. EVIDENCE RETENTION, DELETION, AND LEGAL HOLD**

### **8.1 Evidence dependency**

Evidence required to establish commit authorization, event integrity, History continuity, correction validity, or historical interpretation MUST be governed by an explicit retention dependency.

Deleting an evidence object MUST NOT leave a record that falsely implies complete verifiability.

### **8.2 Deletion**

Deletion MAY proceed only when permitted by the applicable retention policy and higher-priority obligations. Before deletion, the system MUST evaluate whether the object is required by:

* an active or unresolved commit;  
* an integrity or authority verification;  
* a correction or dispute;  
* an audit or investigation;  
* a legal hold;  
* a dependent archive, checkpoint, or replay proof.

Where deletion is prohibited, the operation MUST be rejected or deferred with an auditable result.

Where deletion is permitted but evidence completeness is reduced, the resulting verification limitations MUST be recorded.

### **8.3 Legal hold**

A legal hold, where applicable, MUST identify its scope, authority, effective point, and release evidence. A hold MUST override ordinary deletion rules to the extent required by its governing policy.

The system MUST NOT infer that a hold has ended merely because a deadline passed or a related case is no longer visible.

### **8.4 Cryptographic key retention**

Long-term verification MUST account for key rotation, expiration, revocation, algorithm deprecation, and loss of access to historical verification material.

Private signing keys need not be retained indefinitely if an alternative evidence chain preserves historical verifiability. The required chain and trust assumptions MUST be explicitly specified.

## **9\. INTEGRITY, CONTINUITY, AND AUTHENTICITY RE-VERIFICATION**

### **9.1 Verification dimensions**

A History verification report MUST distinguish:

| Dimension | Question |
| ----- | ----- |
| Byte integrity | Do the stored bytes match the declared digest? |
| Event integrity | Does each event match its authenticated content reference? |
| Continuity | Is the claimed range connected without unexplained gaps or forks? |
| Authenticity | Can the required identity and signature evidence be verified? |
| Authorization | Was the signer or authority permitted to commit this event? |
| Policy validity | Did the event satisfy the applicable policy? |
| Semantic validity | Is the event's meaning supported by the required evidence? |
| Replay validity | Can the declared replay procedure reproduce the expected derived state? |

Passing one dimension MUST NOT be represented as passing all dimensions.

### **9.2 Re-verification report**

A verification report SHOULD include:

verification\_id: REQUIRED  
history\_id: REQUIRED  
range\_start: REQUIRED  
range\_end: REQUIRED  
verification\_profile\_id: REQUIRED  
verifier\_identity: REQUIRED  
verifier\_version: REQUIRED  
checked\_dimensions: REQUIRED  
verified\_ranges: REQUIRED  
unverified\_ranges: REQUIRED  
findings: REQUIRED  
evidence\_refs: REQUIRED  
verification\_time: REQUIRED

The report MUST identify the scope actually checked. Partial verification MUST NOT be reported as full-History verification.

### **9.3 Verification failure**

A mismatch MUST produce an explicit finding. The system MUST preserve relevant evidence and prevent the affected range from being represented as fully verified until adjudication.

Verification failure MUST NOT automatically trigger silent repair, deletion, reconstruction, or canonical rewrite.

A separately authorized repair of storage damage MAY restore bytes from a verified source, but MUST preserve the repair operation's provenance and MUST NOT change the logical event history.

### **9.4 Verification limits**

A digest establishes equality against a reference digest, not the correctness of the original content. A signature can establish a cryptographic relationship under stated key assumptions, but not semantic truth. A valid chain can still encode an unauthorized or semantically invalid event.

Reports MUST state these limits where they materially affect the conclusion.

## **10\. LONG-TERM REPLAY AND PROJECTION GOVERNANCE**

### **10.1 Replay contract**

Replay MUST operate on a declared History range and an explicit replay profile. The profile MUST identify the event schema versions, interpretation rules, policy dependencies, and relevant software versions.

Replay MUST be deterministic under a declared deterministic profile. If external inputs, nondeterministic operations, or unavailable dependencies prevent deterministic reproduction, the replay result MUST disclose that limitation.

### **10.2 Projection isolation**

CANONICAL HISTORY  
       |  
       v  
VALIDATION / INTERPRETATION PROFILE  
       |  
       v  
REPLAY  
       |  
       v  
DERIVED PROJECTION

Replay MUST NOT mutate Canonical History. A projection rebuild, cache update, index rebuild, or correction-aware state calculation MUST remain a derived operation.

A failed replay MUST NOT be used to silently rewrite the input events to match the expected output.

### **10.3 Historical semantics**

The system MUST distinguish:

* the policy that governed the original commit;  
* the schema used to encode the event;  
* the interpretation rules used at the time;  
* a later interpretation or replay profile;  
* the resulting projection.

A later policy version MUST NOT be retroactively substituted for the original commit policy without an explicit, auditable reinterpretation.

### **10.4 Replay compatibility**

When a legacy event cannot be interpreted using available rules, the system MUST preserve it as historical evidence and report the unresolved interpretation. It MUST NOT invent missing semantics or silently discard the event.

Replay compatibility failure is not, by itself, evidence that the original commit was invalid.

## **11\. NORMATIVE VERSIONING AND HISTORICAL INTERPRETATION**

### **11.1 Contract versioning**

Every normative contract and policy profile MUST have an explicit version identity. A version change MUST identify the affected rules, compatibility implications, migration requirements, and acceptance evidence.

### **11.2 No silent retroactivity**

A new rule MUST NOT silently alter the historical authorization or meaning assigned to an existing committed event.

If a new rule requires historical re-evaluation, the system MUST create a separately identifiable assessment with its own version, scope, and evidence.

### **11.3 Unknown legacy evidence**

When historical records lack fields required by a new contract, the system MUST distinguish:

LEGACY\_VALID\_UNDER\_ORIGINAL\_PROFILE  
LEGACY\_REQUIRES\_REINTERPRETATION  
LEGACY\_INSUFFICIENT\_EVIDENCE  
LEGACY\_INVALIDATED\_BY\_VERIFIED\_FINDING  
LEGACY\_STATUS\_UNKNOWN

These are proposed adjudication labels, not established repository enums. Their exact definitions and transition rules require formalization before adoption.

### **11.4 Normative precedence**

Conflicts between governance rules MUST be resolved by an explicit precedence model. The implementation MUST NOT resolve normative conflicts through file ordering, load ordering, model preference, or implicit “latest version wins” behavior.

## **12\. FAILURE AND RECOVERY MATRIX**

| Failure condition | Required behavior | Forbidden behavior |
| ----- | ----- | ----- |
| Commit response lost | Reconcile original attempt | Assume rejection and create duplicate |
| Authority transfer uncertain | Block exclusive-authority commits | Activate both authorities implicitly |
| Stale authority resumes | Apply fencing and record incident | Accept solely on signature validity |
| History fork detected | Preserve branches and adjudicate | Silent merge or arbitrary winner |
| Correction target ambiguous | Reject or hold correction | Guess the intended target |
| Archive digest mismatch | Mark range unverified | Claim archive success |
| Archive missing events | Report continuity gap | Treat partial range as complete |
| Evidence deletion blocked | Reject/defer and record result | Delete because ordinary retention expired |
| Key unavailable | Report authenticity-verification limitation | Claim signature verified |
| Replay mismatch | Preserve inputs and report divergence | Rewrite canonical events |
| Schema unavailable | Preserve raw evidence and mark interpretation unresolved | Invent semantics |
| Migration loses provenance | Reject canonical substitution | Silently drop provenance |

## **13\. INVARIANTS — STI-188-01..20**

All invariants below are proposed and remain unverified.

| ID | Invariant | Violation consequence |
| ----- | ----- | ----- |
| STI-188-01 | Canonical History has a stable logical identity independent of storage location. | Identity verification failure |
| STI-188-02 | Every canonical event has a unique identity within its declared scope. | Commit admission blocked |
| STI-188-03 | Canonical event ordering and continuity are verifiable. | Affected range unverified |
| STI-188-04 | Commit finality requires authoritative commit evidence. | Commit status unresolved |
| STI-188-05 | Unknown commit status is not equivalent to rejection. | Retry prohibited until reconciled |
| STI-188-06 | Retry cannot create duplicate canonical effects for one confirmed commit. | Idempotency violation |
| STI-188-07 | Authority transfer cannot silently create competing active authorities. | Exclusive commits blocked |
| STI-188-08 | Stale authority cannot commit where fencing is required. | Commit rejected or quarantined |
| STI-188-09 | Authority revocation does not silently erase historical events. | Historical integrity violation |
| STI-188-10 | Committed History is not silently rewritten to correct errors. | Canonical integrity violation |
| STI-188-11 | Every correction identifies its target and authorization evidence. | Correction rejected |
| STI-188-12 | Compensation does not imply non-occurrence of the original event. | Historical interpretation violation |
| STI-188-13 | Archive identity and continuity are independently verifiable. | Archive not certified |
| STI-188-14 | Migration preserves required provenance and verification evidence. | Canonical substitution prohibited |
| STI-188-15 | Retention policy absence does not authorize deletion. | Deletion blocked |
| STI-188-16 | Legal hold overrides conflicting ordinary deletion rules where applicable. | Deletion blocked |
| STI-188-17 | Evidence deletion cannot be represented as preserved verifiability. | Verification status downgraded |
| STI-188-18 | Integrity, authenticity, authorization, and semantic validity are distinct claims. | Report invalid |
| STI-188-19 | Replay and projection operations cannot mutate Canonical History. | Operation rejected or isolated |
| STI-188-20 | Normative changes cannot silently rewrite historical interpretation. | Historical reassessment required |

INVARIANT\_SET:  
  prefix: STI-188  
  count: 20  
  status: PROPOSED  
  verification: NOT\_EXECUTED  
  acceptance: NOT\_ASSESSED

## **14\. TEST CANDIDATES — ST-188-01..20**

These are test specifications to be implemented and executed, not evidence that tests already exist or pass.

| Test ID | Scenario | Expected result |
| ----- | ----- | ----- |
| ST-188-01 | Move a History to a different storage path. | Logical identity remains unchanged. |
| ST-188-02 | Insert duplicate event identity with conflicting content. | Duplicate/conflict detected; no silent overwrite. |
| ST-188-03 | Remove a predecessor reference from an archived range. | Continuity verification fails. |
| ST-188-04 | Submit authorization evidence without commit evidence. | Commit finality remains unproven. |
| ST-188-05 | Drop the response after a successful commit. | Reconciliation finds the original result or preserves unknown status. |
| ST-188-06 | Retry an event already confirmed committed. | No duplicate canonical effect. |
| ST-188-07 | Transfer authority while the previous authority is partitioned. | No unauthorized competing commits. |
| ST-188-08 | Attempt a commit with a stale authority epoch. | Fencing rejects or isolates the attempt. |
| ST-188-09 | Revoke a key used by historical events. | Historical records remain; trust findings are evaluated separately. |
| ST-188-10 | Attempt in-place replacement of a committed event. | Mutation is blocked or detected. |
| ST-188-11 | Submit a correction with no uniquely identified target. | Correction rejected or held. |
| ST-188-12 | Apply a compensating event to an earlier transaction. | Original event remains discoverable in History. |
| ST-188-13 | Alter archived bytes without updating the authenticated digest. | Archive verification fails. |
| ST-188-14 | Migrate a record while dropping provenance. | Migration is rejected as canonical substitution. |
| ST-188-15 | Request deletion without a retention policy. | Deletion denied or deferred. |
| ST-188-16 | Request deletion during an applicable legal hold. | Deletion denied or deferred. |
| ST-188-17 | Delete evidence that is required for historical verification. | Loss of verifiability is explicitly reported. |
| ST-188-18 | Provide a valid digest but invalid authorization evidence. | Integrity may pass; authorization must fail independently. |
| ST-188-19 | Run replay that attempts to write to the canonical store. | Write is prevented by the authority boundary. |
| ST-188-20 | Change interpretation rules and replay legacy events. | Original profile remains identifiable; reinterpretation is separately recorded. |

### **14.1 Test execution requirements**

Each test result MUST record:

test\_id: REQUIRED  
test\_version: REQUIRED  
implementation\_revision: REQUIRED  
fixture\_digest: REQUIRED  
preconditions: REQUIRED  
execution\_result: REQUIRED  
observed\_behavior: REQUIRED  
expected\_behavior: REQUIRED  
evidence\_refs: REQUIRED  
review\_status: REQUIRED

A test MUST NOT be marked `PASS` solely because the implementation returned success. Its observed behavior and evidence MUST satisfy the stated assertion.

TEST\_SET:  
  prefix: ST-188  
  count: 20  
  status: NOT\_EXECUTED  
  pass\_count: 0  
  fail\_count: 0  
  acceptance: NOT\_ASSESSED

The zero counts above indicate no results have been recorded in this draft; they do not establish that the tests have been run.

## **15\. OPEN ISSUES — OI-188-01..20**

All issues remain open. No issue is deemed resolved by this proposal.

| Issue ID | Unresolved decision |
| ----- | ----- |
| OI-188-01 | Exact definition of commit finality under crash and storage failure |
| OI-188-02 | Atomic relationship among authorization, persistence, sequence allocation, and commit evidence |
| OI-188-03 | Required durability guarantee for each commit profile |
| OI-188-04 | Authoritative reconciliation protocol for indeterminate commit status |
| OI-188-05 | Canonical History topology: single sequence, partitioned sequence, or another model |
| OI-188-06 | Formal fork detection and adjudication procedure |
| OI-188-07 | Authority-transfer linearization point |
| OI-188-08 | Required fencing mechanism and partition behavior |
| OI-188-09 | Revocation semantics for events committed before compromise discovery |
| OI-188-10 | Canonical schema and authorization requirements for correction records |
| OI-188-11 | Separation of factual correction, compensation, retraction, and reinterpretation |
| OI-188-12 | Retention classes and policy precedence |
| OI-188-13 | Archive checkpoint and range-completeness proof format |
| OI-188-14 | Migration equivalence proof and canonical-format preservation requirements |
| OI-188-15 | Legal-hold integration and release authorization |
| OI-188-16 | Evidence dependency graph and safe deletion determination |
| OI-188-17 | Long-term key, algorithm, and trust-anchor preservation strategy |
| OI-188-18 | Verification profile for authenticity versus authorization versus semantics |
| OI-188-19 | Deterministic replay compatibility across schema and engine versions |
| OI-188-20 | Normative precedence and historical reinterpretation governance |

OPEN\_ISSUES:  
  prefix: OI-188  
  count: 20  
  status: OPEN  
  blocking\_for\_production: true

## **16\. ACCEPTANCE GATES — AG-188-01..20**

All gates are currently `NOT_ASSESSED`. Acceptance requires evidence, not merely the existence of contract text.

| Gate ID | Required evidence |
| ----- | ----- |
| AG-188-01 | Stable History identity and genesis verification |
| AG-188-02 | Event identity uniqueness enforcement |
| AG-188-03 | Sequence, predecessor, gap, and fork detection |
| AG-188-04 | Explicit and testable commit-finality protocol |
| AG-188-05 | Correct handling of indeterminate commit status |
| AG-188-06 | Idempotent retry and duplicate-effect prevention |
| AG-188-07 | Exclusive authority-transfer protocol |
| AG-188-08 | Fencing and stale-authority rejection evidence |
| AG-188-09 | Revocation and historical trust reevaluation |
| AG-188-10 | Demonstration that committed History cannot be silently rewritten |
| AG-188-11 | Correction schema, authorization, and target-validation tests |
| AG-188-12 | Original-event preservation and compensation semantics |
| AG-188-13 | Archive identity, integrity, and continuity verification |
| AG-188-14 | Migration equivalence and provenance preservation |
| AG-188-15 | Retention policy and deletion enforcement |
| AG-188-16 | Legal-hold and release control evidence |
| AG-188-17 | Evidence-deletion impact and verifiability reporting |
| AG-188-18 | Independent verification dimensions and scoped reports |
| AG-188-19 | Replay isolation and reproducibility evidence |
| AG-188-20 | Normative versioning and historical interpretation controls |

ACCEPTANCE:  
  prefix: AG-188  
  count: 20  
  status: NOT\_ASSESSED  
  required\_for\_freeze: true  
  automatic\_acceptance: false

An unresolved critical issue MUST prevent the affected acceptance gate from passing. A passing test suite alone MUST NOT override a known specification gap.

## **17\. PROPOSED ARTIFACT TREE**

The following tree is a proposed deliverable layout. No files or directories have been created by this response.

contracts/  
└── step-188/  
    ├── canonical\_history\_governance\_contract.md  
    ├── schemas/  
    │   ├── history\_identity.schema.json  
    │   ├── commit\_finality\_evidence.schema.json  
    │   ├── authority\_transfer.schema.json  
    │   ├── history\_correction.schema.json  
    │   ├── retention\_policy.schema.json  
    │   ├── archive\_manifest.schema.json  
    │   └── verification\_report.schema.json  
    ├── invariants/  
    │   └── sti-188.yaml  
    ├── tests/  
    │   ├── test\_catalog.yaml  
    │   ├── fixtures/  
    │   └── expected\_results/  
    ├── governance/  
    │   ├── authority\_transfer.md  
    │   ├── correction\_and\_compensation.md  
    │   ├── retention\_and\_deletion.md  
    │   └── normative\_versioning.md  
    ├── verification/  
    │   ├── verification\_profile.md  
    │   ├── archive\_verification.md  
    │   └── replay\_compatibility.md  
    ├── issues/  
    │   └── oi-188.yaml  
    ├── acceptance/  
    │   └── ag-188.yaml  
    └── adjudication/  
        └── step-188-status.yaml

### **17.1 Artifact constraints**

1. The contract is the proposed normative source; schemas encode only the structural constraints they can actually express.  
2. Cross-record invariants, authority validation, cryptographic verification, and retention decisions require separately defined enforcement mechanisms.  
3. Test fixtures MUST NOT be treated as production evidence.  
4. Test results MUST reference the implementation revision and exact test artifact.  
5. Acceptance records MUST reference evidence for each gate.  
6. The adjudication record MUST distinguish specification completeness from implementation verification and formal adoption.  
7. No artifact may independently grant itself canonical authority by existing in the proposed directory.

## **18\. DEPENDENCY MATRIX**

| Dependency | Required relationship | Current status |
| ----- | ----- | ----- |
| STEP-182 | Earlier contract and authority-boundary dependencies | NOT\_VERIFIED |
| STEP-183 | Earlier lifecycle and state dependencies | NOT\_VERIFIED |
| STEP-184 | Earlier validation and governance dependencies | NOT\_VERIFIED |
| STEP-185 | Earlier evidence and integrity dependencies | NOT\_VERIFIED |
| STEP-186 | Preceding history/recovery dependencies | NOT\_VERIFIED |
| STEP-187 | Distributed Commit, replication, ordering, conflict, recovery | DRAFT\_DEPENDENCY; COMPATIBILITY NOT\_VERIFIED |
| Kernel / Commit Authority | Sole canonical mutation boundary | DESIGN ALIGNMENT REQUIRED |
| Canonical History / WAL | Event identity, ordering, continuity, durability | CONTRACT NOT\_VERIFIED |
| Policy Registry | Versioned authorization and retention rules | NOT\_VERIFIED |
| Trust and Key Lifecycle | Historical authenticity and revocation interpretation | NOT\_VERIFIED |
| Replication Layer | Replica state and divergence handling | NOT\_VERIFIED |
| Archive / Storage Layer | Retention, migration, restoration | NOT\_VERIFIED |
| Replay / Projection | Deterministic derivation without canonical mutation | NOT\_VERIFIED |
| Audit / Evidence Store | Evidence retention and verification reports | NOT\_VERIFIED |
| Schema / Validator Layer | Structural and cross-record validation | NOT\_VERIFIED |

### **18.1 Dependency resolution rule**

No dependency is considered satisfied merely because its name appears in prior conversation context or in this matrix.

Before adoption, each dependency MUST be mapped to an actual artifact and version, with its normative requirements and compatibility established. Any mismatch MUST be recorded as a specification gap.

STEP-187's unresolved definition of Commit Finality is a direct blocker for STEP-188's finality, durability, recovery, and authority-transfer acceptance gates.

## **19\. ADJUDICATION**

STEP\_ID: 188

SPECIFICATION:  
  draft\_created: true  
  proposed\_scope\_defined: true  
  invariants\_catalogued: true  
  test\_candidates\_catalogued: true  
  open\_issues\_catalogued: true  
  acceptance\_gates\_catalogued: true  
  artifact\_tree\_proposed: true

REPOSITORY:  
  inspection: NOT\_PERFORMED  
  artifacts\_created: false  
  existing\_contract\_compatibility: NOT\_VERIFIED  
  schema\_validation: NOT\_EXECUTED  
  test\_execution: NOT\_EXECUTED

GOVERNANCE:  
  canonical\_mutation: NONE  
  adoption: NOT\_ADOPTED  
  normative\_authority: NOT\_GRANTED  
  dependency\_closure: NOT\_VERIFIED

ACCEPTANCE:  
  invariants\_verified: 0  
  tests\_passed: 0  
  gates\_passed: 0  
  critical\_issues\_resolved: 0  
  global\_acceptance: NOT\_ASSESSED

FREEZE:  
  status: NOT\_AUTHORIZED  
  reason:  
    \- COMMIT\_FINALITY\_PROTOCOL\_UNRESOLVED  
    \- AUTHORITY\_TRANSFER\_PROTOCOL\_UNVERIFIED  
    \- CORRECTION\_SCHEMA\_UNVALIDATED  
    \- RETENTION\_AND\_ARCHIVE\_CONTROLS\_UNVERIFIED  
    \- LONG\_TERM\_VERIFICATION\_UNPROVEN  
    \- DEPENDENCY\_COMPATIBILITY\_UNVERIFIED

The zero counts indicate that this draft contains no verified results; they are not claims about the state of an uninspected repository.

### **19.1 Critical design conclusion**

The key unresolved problem is not simply how to preserve History. It is how to prove, over time, that a particular event:

1. belongs to the intended logical History;  
2. was committed under the correct authority and policy;  
3. has not been silently replaced or removed;  
4. remains connected to the authenticated historical sequence;  
5. can still be interpreted under an identified semantic contract;  
6. produces a reproducible derived state under a declared replay profile.

These are separate proof obligations. No single hash, signature, replica count, or successful replay can establish all six.

STEP-188 status: draft complete; adoption, implementation, validation, acceptance, and Freeze remain unestablished.

## **20\. NEXT STEP**

### **STEP-189 — Canonical History Verification / Long-Term Proof / Evidence Preservation / Audit Reproducibility Contract**

The next draft should formalize the verification protocol that connects commit evidence, historical trust, archive integrity, and replay reproducibility into a verifiable audit result.

Planned scope:

1. Verification claim model and assurance levels.  
2. Evidence-chain construction and proof dependencies.  
3. History checkpoints, range proofs, and continuity verification.  
4. Historical signature and trust-anchor verification.  
5. Key rotation, algorithm migration, and cryptographic re-verification.  
6. Verification of archives and restored History ranges.  
7. Reproducible audit reports and verifier identity.  
8. Evidence availability and verification limitations.  
9. Independent verification versus self-attestation.  
10. Evidence-backed acceptance and explicit failure adjudication.

The governing constraint remains:

VERIFY \!= AUTHORIZE  
VERIFY \!= COMMIT  
VERIFY \!= SEMANTIC TRUTH  
REPLAY \!= HISTORY REPAIR  
EVIDENCE ABSENCE \!= EVIDENCE OF INVALIDITY  
UNVERIFIED \!= VERIFIED

STEP-189 should not assume STEP-188's proposed mechanisms have been adopted. It must define its own dependencies as proposed, identify unresolved upstream requirements, and avoid granting canonical status to any unverified evidence.