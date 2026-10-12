# A1A Semantic Coverage Audit Contract

**Contract ID:** `A1A-SCA`  
**Version:** `0.1.0-draft`  
**Status:** `DRAFT / NOT FROZEN`  
**Normative target:** A-1a canonical unit artifact  
**Mutation policy:** `READ_ONLY`

## 1. Purpose

A1A Semantic Coverage Audit (A1A-SCA) independently evaluates whether meaningful source content is represented by the canonical units produced by A-1a.

A1A-SCA detects candidate omissions and records evidence. It does not redefine, repair, or extend the A-1a boundary observation contract.

## 2. Authority and Scope

1. The original source bytes are the authority for source content.
2. The supplied A-1a artifact is the authority for the observed unit boundaries and unit content.
3. A1A-SCA findings are audit records, not canonical source content.
4. A1A-SCA MUST NOT modify the source, A-1a artifact, manifest, or existing canonical records.
5. A1A-SCA MUST NOT trigger segmentation, normalization, re-extraction, or automatic repair.
6. A1A-SCA MUST NOT promote an LLM-generated classification to canonical truth without the specified validation and review process.

## 3. Non-Goals

A1A-SCA does not:

- require every source line to belong to a unit;
- treat every uncovered line as a defect;
- infer missing source text;
- generate replacement units or boundaries;
- alter A-1a schemas, prompts, validators, or Freeze status;
- establish semantic correctness solely from structural validation;
- interpret a finding as authorization to modify canonical artifacts.

## 4. Inputs and Identity

The audit input consists of:

- `document_id`: an explicit, stable document identifier;
- `source`: the original source byte sequence;
- `artifact`: the original A-1a artifact byte sequence;
- `audit_rules_version`: the version of the audit rules;
- `candidate_input`: optional proposed semantic findings, when candidate generation is performed separately.

The audit MUST calculate:

- `source_digest`: SHA-256 of the exact source bytes;
- `artifact_digest`: SHA-256 of the exact artifact bytes.

Digests MUST use lowercase hexadecimal encoding. Input bytes MUST NOT be newline-normalized, text-normalized, or reserialized before hashing.

The document identifier MUST come from an authoritative manifest or an explicit caller-supplied identifier. It MUST NOT be silently regenerated from a filesystem path.

If an expected digest is supplied and does not match the corresponding input, the audit MUST terminate with `INPUT_INVALID`. The audit MUST NOT continue semantic classification with mismatched inputs.

The audit MUST NOT silently substitute a different source or artifact when a path, identifier, or digest cannot be resolved.

## 5. Read-Only and No-Repair Requirements

The audit MUST be observational.

It MUST NOT:

- edit or overwrite any input;
- fill source gaps;
- adjust unit spans;
- split or merge units;
- repair malformed JSON;
- reinterpret invalid input as valid;
- infer missing content from neighboring units;
- convert an uncertain semantic judgment into a definitive fact without evidence.

A detected defect MUST be reported as a finding or an audit-level failure. It MUST NOT be repaired in place.

## 6. Coverage Model

Coverage is evaluated against source line ranges and the source text represented by the supplied units.

Uncovered source content is not automatically defective. The audit MUST distinguish:

1. non-semantic gaps;
2. structural omissions;
3. whole semantic-unit omissions;
4. partial semantic-unit omissions;
5. ambiguous cases.

The audit MUST preserve the distinction between:

- **structural validity**: the artifact satisfies the applicable A-1a structural contract;
- **semantic coverage**: meaningful source content is represented by the artifact;
- **semantic correctness**: the represented content is interpreted correctly.

Passing structural validation MUST NOT be interpreted as proof of semantic completeness or semantic correctness.

## 7. Finding Classifications

### 7.1 `NON_SEMANTIC_GAP`

Use when uncovered content does not constitute a meaningful semantic omission under the applicable audit rules, such as a blank separator or purely decorative delimiter.

The classification MUST be supported by source evidence. Uncertainty MUST NOT be concealed by assigning this classification by default.

### 7.2 `STRUCTURAL_GAP`

Use when an uncovered structural element, such as a heading, is missing from the observed units, but the available evidence does not establish that an entire semantic unit has been omitted.

A heading-only omission MUST NOT automatically be classified as a whole-unit omission.

### 7.3 `WHOLE_UNIT_OMISSION`

Use when an identifiable, semantically coherent source unit is entirely absent from the observed units.

The finding MUST identify the source range and provide evidence supporting the unit boundary and omission judgment.

### 7.4 `PARTIAL_UNIT_OMISSION`

Use when a portion of a semantic unit is represented by the artifact's surrounding content, but another meaningful portion is absent.

The finding MUST distinguish directly observed source text from the audit's interpretation of the relationship between covered and uncovered content.

### 7.5 `AMBIGUOUS`

Use when the available evidence does not support a sufficiently reliable choice among the preceding classifications.

The finding MUST preserve the uncertainty and identify the evidence or decision needed for resolution.

## 8. Finding Granularity

Finding granularity MUST follow semantic units rather than uncovered line counts.

1. A single omitted heading SHOULD produce one finding.
2. A coherent omitted section SHOULD produce one finding for the section.
3. Individual bullets within a section MUST NOT automatically become separate findings merely because they occupy separate lines.
4. A partial omission SHOULD identify the smallest source range supported by the evidence.
5. Separate omissions MUST be recorded separately when the evidence establishes that they are independent semantic units.
6. The audit MUST NOT merge unrelated omissions solely to reduce the finding count.

For the initial regression corpus:

- `SC-T01`: Constitution line 709 — `STRUCTURAL_GAP` candidate.
- `SC-T02`: Constitution line 756 — `STRUCTURAL_GAP` candidate.
- `SC-T03`: Graph Runtime Context line 493 — `PARTIAL_UNIT_OMISSION` candidate.
- `SC-T04`: R0 API lines 373–381 — `WHOLE_UNIT_OMISSION` candidate.

These cases remain test expectations until the applicable source identity, artifact identity, evidence, and classification rules have been validated.

## 9. Finding Record

Each finding MUST contain:

- `finding_id`
- `classification`
- `source_line_start`
- `source_line_end`
- `covered_by_units`
- `evidence`
- `reason`
- `confidence`
- `review_required`

Requirements:

- Line numbers MUST be one-based and inclusive.
- `source_line_start` MUST NOT exceed `source_line_end`.
- `covered_by_units` MUST contain only unit IDs present in the supplied artifact.
- An empty `covered_by_units` array is valid when no related units exist.
- Evidence MUST be traceable to the source or artifact.
- Reasons MUST distinguish observations from interpretations.
- Confidence MUST be one of `HIGH`, `MEDIUM`, or `LOW`.
- `review_required` MUST be a Boolean.
- Finding IDs MUST be unique within a report and deterministically assigned.

`covered_by_units` identifies relevant observed units; it MUST NOT imply that those units cover the finding's missing source lines.

## 10. Audit-Level Status

The report status MUST be one of:

### `COMPLETED`

The audit completed according to the applicable procedure. Zero findings is valid.

`COMPLETED` MUST NOT be interpreted as proof that the source is semantically complete.

### `INPUT_INVALID`

The source, artifact, identity, or input structure failed a required validation. Semantic auditing MUST NOT proceed using the invalid input.

### `AUDIT_FAILED`

The inputs passed the required input validation, but the audit could not complete according to the applicable procedure.

An audit-level failure MUST NOT be represented as a successful report with an empty finding list.

## 11. Deterministic Validation

The deterministic validator MUST check, at minimum:

1. report schema and required fields;
2. allowed status, classification, and confidence values;
3. line-range type and ordering constraints;
4. finding ID uniqueness;
5. unit ID references;
6. deterministic finding order;
7. summary counts against the finding list;
8. report input identity against the actual source and artifact digests;
9. required evidence fields and their structural validity.

The validator MUST reject invalid records. It MUST NOT repair, reinterpret, or infer the intended record.

JSON Schema MAY enforce structural constraints, but constraints requiring cross-field comparisons, source access, artifact access, digest computation, or semantic judgment MUST be enforced outside JSON Schema.

Deterministic validation MUST NOT claim to prove that a semantic classification is correct merely because the report passes structural checks.

## 12. Separation of Candidate Generation and Validation

Candidate generation and deterministic validation MUST be separate operations.

If an LLM is used, its output MUST be treated as a candidate proposal.

The candidate-generation stage MUST NOT directly mutate the source, artifact, or final report.

The validation stage MUST reject malformed candidates rather than repair them.

Semantic judgments requiring human review MUST remain explicitly reviewable. A validator MUST NOT resolve ambiguous semantic classifications by inference.

## 13. Reproducibility

Given identical:

- source bytes;
- artifact bytes;
- document identifier;
- audit rules version;
- candidate input;
- deterministic configuration;

the deterministic report-finalization process MUST produce the same finding order, finding IDs, summary counts, and serialized output under the same serialization rules.

Findings MUST be ordered by `source_line_start`, then `source_line_end`, followed by a documented deterministic tie-breaker.

Finding IDs MUST be assigned after deterministic ordering, not according to nondeterministic candidate arrival order.

If candidate generation is nondeterministic, the contract MUST distinguish candidate-generation reproducibility from deterministic validation and report-finalization reproducibility.

## 14. Summary Integrity

The report summary MUST be derivable from the final finding list.

Classification counts MUST equal the number of findings assigned to each classification.

The total finding count MUST equal the length of the final finding list.

Summary fields MUST NOT be independently asserted without validation against the actual records.

## 15. Regression Requirements

The initial regression set MUST include:

- `SC-T01`: omitted heading; expected `STRUCTURAL_GAP`;
- `SC-T02`: omitted heading; expected `STRUCTURAL_GAP`;
- `SC-T03`: partial sentence omission; expected `PARTIAL_UNIT_OMISSION` or an explicitly unresolved `AMBIGUOUS` result;
- `SC-T04`: omitted invariant section; expected `WHOLE_UNIT_OMISSION` candidate;
- `SC-T05`: non-semantic gap; expected `NON_SEMANTIC_GAP`;
- `SC-T06`: valid partial coverage; no defect MUST be inferred solely from uncovered lines;
- `SC-T07`: insufficient evidence; expected `AMBIGUOUS`;
- `SC-T08`: invalid input artifact; expected `INPUT_INVALID`, with no semantic audit or repair.

Tests MUST verify both expected findings and prohibited behavior, including input mutation, automatic repair, and forced full-line coverage.

## 16. Freeze and Change Control

This document is a draft and is not frozen.

No implementation, schema freeze, A-1a modification, re-extraction, or canonical artifact mutation is authorized solely by this draft.

Before Freeze, the contract MUST be reviewed for consistency with the existing A-1a contract, the actual input artifact format, and the deterministic validator requirements.

Any subsequent normative change MUST update the contract version and applicable regression expectations.

**End of draft.**