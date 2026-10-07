# DM-2-6 Validation Contract

**Document:** `dm2-validation-contract.md`
**Version:** 1.0
**Status:** Finalized
**Scope:** Chron-LLM Specification Organizer — DM-2 Semantic Extraction
**Layer:** DM-2-6 Validation

---

# 0. Purpose

DM-2-6 defines the deterministic validation boundary for semantic extraction records produced from A-1a-N canonical units.

DM-2-6 validates conformance to:

* DM-2-0 Canonical Unit Input;
* DM-2-1 Semantic Unit Definition;
* DM-2-2 Closed Vocabulary;
* DM-2-3 Extraction Record;
* DM-2-4 Evidence / Provenance;
* DM-2-5 Unknown / Ambiguous.

DM-2-6 does not perform semantic interpretation.

DM-2-6 does not repair invalid records.

DM-2-6 does not modify canonical input.

---

# 1. Validation Authority

The validator is deterministic.

The validator MUST evaluate the supplied record against explicit normative rules.

The validator MUST NOT use:

* LLM judgment;
* probabilistic classification;
* semantic similarity;
* model confidence;
* corpus frequency;
* inferred document intent;
* undocumented heuristics.

Validation MUST be reproducible for identical inputs.

---

# 2. Validation Input

DM-2-6 validates at minimum:

canonical_unit
semantic_extraction_record

The canonical unit is the authoritative source for:

unit_id
line_start
line_end
source_text

The semantic extraction record is the candidate output being validated.

The validator MUST have access to the canonical source text when validating evidence and provenance.

---

# 3. Validation Layers

Validation is divided into:

V0  Record transport / JSON validity
V1  Schema validity
V2  Canonical identity/span integrity
V3  Evidence / provenance integrity
V4  Semantic vocabulary integrity
V5  Semantic attribute integrity
V6  Unknown / Ambiguous integrity
V7  Boundary integrity
V8  Forbidden-content integrity

All layers are deterministic.

Failure of any mandatory layer results in rejection.

---

# 4. V0 — Record Transport Validity

The candidate MUST be valid JSON before semantic validation begins.

The validator MUST reject:

* malformed JSON;
* non-object root where an object is required;
* truncated JSON;
* duplicate-key ambiguity if the parser exposes duplicate keys as an error condition.

The validator MUST NOT repair malformed JSON.

---

# 5. V1 — Schema Validity

The candidate MUST conform to the applicable DM-2 semantic extraction record schema.

The validator MUST reject:

* missing required fields;
* invalid field types;
* invalid enum values;
* invalid `unit_id` format;
* unexpected properties;
* invalid nested objects.

For the current DM-2-3 record schema:

additionalProperties = false

is normative.

Unknown fields MUST therefore be rejected.

---

# 6. V2 — Canonical Identity / Span Integrity

The following fields are inherited from A-1a-N:

unit_id
line_start
line_end
source_text

They MUST be identical between canonical input and extraction record.

The validator MUST verify:

record.unit_id
==
canonical.unit_id

record.line_start
==
canonical.line_start

record.line_end
==
canonical.line_end

record.source_text
==
canonical.source_text

Any mismatch MUST cause rejection.

The validator MUST NOT reconstruct or repair these values.

---

# 7. V2 — Span Validity

The canonical span MUST satisfy:

line_start >= 1
line_end >= line_start

DM-2-6 MUST NOT alter the span.

Document-level range validation remains an upstream A-1a responsibility when the canonical unit itself is produced.

If a canonical unit is supplied with an invalid span, DM-2 MUST reject it rather than repair it.

---

# 8. V3 — Evidence Phrase Integrity

Every value in:

semantic_evidence.phrases

MUST be an exact substring of:

source_text

The comparison MUST be exact.

The validator MUST NOT:

* normalize whitespace;
* normalize Unicode;
* ignore punctuation;
* perform case folding;
* translate;
* paraphrase;
* apply fuzzy matching.

Conceptually:

phrase in source_text

MUST evaluate using exact string containment.

If false, the record MUST be rejected.

---

# 9. V3 — Empty Evidence Phrase

An empty:

"phrases": []

is structurally valid.

DM-2-6 MUST NOT invent a phrase to satisfy an evidence requirement.

Whether empty evidence is semantically acceptable for a particular classification is governed by the explicit DM-2 semantic rules and MUST NOT be inferred by the validator.

---

# 10. V3 — Evidence Line Integrity

Every value in:

semantic_evidence.lines

MUST satisfy:

line_start <= evidence_line <= line_end

An evidence line outside the canonical unit span MUST cause rejection.

The validator MUST NOT move an invalid evidence line into the span.

---

# 11. V3 — Evidence Line Uniqueness

The current schema defines:

uniqueItems = true

for:

semantic_evidence.lines

Therefore duplicate evidence line numbers MUST be rejected.

---

# 12. V3 — Phrase / Line Positional Mapping

The validator MUST NOT assume:

phrases[i] ↔ lines[i]

The current record structure does not define such a mapping.

Therefore the validator MUST validate the two arrays independently:

phrases → exact substring of source_text

lines → contained within canonical span

No additional positional invariant may be imposed.

---

# 13. V4 — Semantic Kind Integrity

`semantic_kind` MUST belong to the closed DM-2 vocabulary:

Heading
Requirement
Constraint
Definition
Description
Procedure
State
Event
Exception
Unclassified

The validator MUST reject:

* unknown categories;
* aliases;
* free-form categories;
* compound invented categories;
* categories inferred from external vocabularies.

For example:

RequirementConstraint

is invalid unless explicitly added to the closed vocabulary by a future specification revision.

---

# 14. V5 — Semantic Attribute Integrity

The validator MUST validate every semantic attribute against its closed vocabulary.

## 14.1 modality

Allowed:

must
shall
should
may
cannot
prohibited
required
optional
none

## 14.2 structural_form

Allowed:

heading
paragraph
bullet-list
numbered-list
procedure-block
other

## 14.3 semantic_strength

Allowed:

strong
weak
descriptive
definitional
none

## 14.4 semantic_scope

Allowed:

global
system-wide
component-specific
local
unspecified

Any value outside the applicable closed vocabulary MUST cause rejection.

---

# 15. Semantic Attribute Non-Expansion

The validator MUST NOT infer missing attribute values.

The validator MUST NOT replace:

missing

with:

none

unless the applicable schema explicitly supplies that value.

The validator MUST reject missing required attributes according to the schema.

---

# 16. V6 — Unknown / Ambiguous Integrity

Unknown and Ambiguous are resolution states, not semantic kinds.

The validator MUST preserve the distinction:

```text
Unclassified
≠
Unknown
≠
Ambiguous
```

The validator MUST NOT silently convert one state into another.

When the applicable DM-2 semantic extraction record schema contains the explicit resolution representation, the validator MUST enforce its status, reason, and candidate classification constraints.

The following resolution states are valid:

* `resolved`
* `unknown`
* `ambiguous`

### Resolved

When `resolution.status = resolved`:

* `semantic_kind` MUST be a classified DM-2 semantic kind.
* `semantic_kind` MUST NOT be `Unclassified`.
* `resolution.reason` MUST be `null`.
* `candidate_kinds` MUST NOT be present.

### Unknown

When `resolution.status = unknown`:

* `semantic_kind` MUST be `Unclassified`.
* `candidate_kinds` MUST NOT be present.
* `resolution.reason` MUST be one of the permitted Unknown reasons defined by the applicable schema.

### Ambiguous

When `resolution.status = ambiguous`:

* `semantic_kind` MUST be `Unclassified`.
* `resolution.reason` MUST be `multiple_plausible_interpretations`.
* `candidate_kinds` MUST be present.
* `candidate_kinds` MUST contain at least two distinct classified semantic kinds.
* `Unclassified` MUST NOT appear in `candidate_kinds`.

The validator MUST reject internally contradictory resolution states.

The validator MUST NOT resolve contradictions automatically.

---

# 17. Candidate Classification Integrity

`candidate_kinds` represents plausible classified semantic kinds.

Therefore:

1. every candidate MUST belong to the classified portion of the DM-2 closed semantic vocabulary;
2. `Unclassified` MUST NOT appear as a candidate;
3. candidates MUST be unique;
4. candidates MUST NOT be treated as canonical `semantic_kind`;
5. invented categories MUST be rejected;
6. `candidate_kinds` MUST NOT be used for `unknown`;
7. `ambiguous` MUST contain at least two distinct candidate kinds.

A candidate list MUST NOT be silently collapsed into a single classification.

The presence of candidate kinds MUST NOT alter the canonical A-1a unit, its span, or its source text.

---

# 18. Resolved / Unresolved Consistency

The validator MUST enforce the following state semantics.

```text
resolved
  = one classified semantic kind has been accepted

unknown
  = no sufficiently supported classified semantic kind
    has been established

ambiguous
  = two or more plausible classified semantic kinds
    remain unresolved
```

The following combinations MUST be rejected:

* `resolution.status = resolved` with `semantic_kind = Unclassified`;
* `resolution.status = resolved` with a non-null `reason`;
* `resolution.status = resolved` with `candidate_kinds`;
* `resolution.status = unknown` with `semantic_kind != Unclassified`;
* `resolution.status = unknown` with `candidate_kinds`;
* `resolution.status = ambiguous` with `semantic_kind != Unclassified`;
* `resolution.status = ambiguous` with a reason other than `multiple_plausible_interpretations`;
* `resolution.status = ambiguous` without at least two distinct candidate kinds;
* `resolution.status = ambiguous` with `Unclassified` in `candidate_kinds`.

The validator MUST reject these states rather than normalize or repair them.

The validator MUST NOT:

* select one ambiguity candidate;
* convert `unknown` into `ambiguous`;
* convert `ambiguous` into `unknown`;
* promote a candidate into canonical `semantic_kind`;
* infer a missing resolution state;
* infer a missing candidate classification.

---

# 19. V7 — Boundary Integrity

DM-2-6 MUST enforce the A-1a boundary as immutable.

The validator MUST reject any record that:

* changes `line_start`;
* changes `line_end`;
* changes `source_text`;
* introduces a second unit;
* merges multiple units;
* splits one canonical unit.

DM-2 validation operates on exactly one canonical A-1a unit.

---

# 20. No Re-Segmentation

The validator MUST NOT inspect semantic content and conclude that the canonical unit should have been split or merged.

For example:

semantic record appears to contain two meanings

is not a DM-2-6 segmentation decision.

The validator MUST reject or accept the semantic record according to the existing unit boundary.

A-1a remains authoritative for segmentation.

---

# 21. V8 — Forbidden Content

The current DM-2 record MUST NOT contain causal or graph fields.

Examples of prohibited fields include:

claims
entities
actions
conditions
causes
effects
dependencies
triggers
mutations
transitions
causal_relations
causal_confidence
edges
graph

The list is illustrative of the causal boundary established by DM-2-3.

Because the record schema uses:

additionalProperties = false

such fields are rejected structurally.

DM-2-6 MUST NOT silently remove them.

---

# 22. Source Evidence vs Interpretation

The validator MUST preserve the distinction between:

SOURCE EVIDENCE

and:

LLM INTERPRETATION

Source evidence:

unit_id
line_start
line_end
source_text
semantic_evidence

must be validated against canonical input.

Interpretation:

semantic_kind
semantic_attributes

must be validated against closed vocabularies and semantic consistency rules.

The validator MUST NOT treat an interpretation as source evidence.

---

# 23. No Semantic Reinterpretation

DM-2-6 is a validator, not a semantic classifier.

It MUST NOT decide:

"This text is actually a Requirement."

It may only decide:

"The supplied semantic_kind is structurally and contractually valid."

provided all applicable validation rules pass.

---

# 24. No Repair

Invalid records MUST be rejected.

The validator MUST NOT:

* trim strings;
* fix line numbers;
* replace enum values;
* insert missing fields;
* remove forbidden fields;
* rewrite evidence;
* normalize source text;
* select an ambiguity candidate;
* reconstruct missing provenance.

The required behavior is:

invalid
  ↓
reject + diagnostic

not:

invalid
  ↓
repair
  ↓
accept

---

# 25. Diagnostic Requirements

A validation failure MUST identify the violated invariant sufficiently for deterministic debugging.

At minimum, a diagnostic SHOULD identify:

validation layer
rule
field/path
observed value
expected condition

Example conceptual diagnostic:

INVALID_RECORD:
layer=V3
rule=EVIDENCE_PHRASE_SUBSTRING
path=semantic_evidence.phrases[0]
reason=phrase is not an exact substring of source_text

Diagnostics MUST describe the failure.

Diagnostics MUST NOT mutate the candidate record.

---

# 26. Validation Result

Conceptually, DM-2-6 produces:

{
  "valid": true,
  "diagnostics": []
}

or:

{
  "valid": false,
  "diagnostics": [
    {
      "rule": "EVIDENCE_PHRASE_SUBSTRING",
      "path": "semantic_evidence.phrases[0]",
      "reason": "..."
    }
  ]
}

The exact validator result schema is an implementation contract and is separate from the semantic extraction record schema.

---

# 27. Validation Ordering

The validator SHOULD evaluate rules in dependency order:

V0 Transport
 ↓
V1 Schema
 ↓
V2 Canonical Identity / Span
 ↓
V3 Evidence / Provenance
 ↓
V4 Semantic Kind
 ↓
V5 Semantic Attributes
 ↓
V6 Unknown / Ambiguous
 ↓
V7 Boundary
 ↓
V8 Forbidden Content

A lower-level structural failure MUST NOT be concealed by a later semantic interpretation.

The validator MAY report multiple independent failures if doing so does not require speculative interpretation.

---

# 28. Canonical Input Authority

When a record disagrees with canonical input:

canonical_unit
    >
semantic_extraction_record

The canonical unit wins.

The validator MUST reject the semantic record.

It MUST NOT update the canonical unit from the semantic record.

---

# 29. Determinism Requirement

For identical:

canonical_unit
semantic_extraction_record
applicable_schema
validation_rules

the validator MUST produce the same validity result.

Validation MUST NOT depend on:

* model inference;
* random seeds;
* wall-clock time;
* external network state;
* corpus statistics;
* mutable hidden state.

---

# 30. DM-2-6 Non-Responsibilities

DM-2-6 MUST NOT:

* segment documents;
* regenerate canonical units;
* classify semantic meaning;
* infer causal relationships;
* repair invalid records;
* expand closed vocabularies;
* resolve semantic ambiguity;
* invent provenance;
* rewrite evidence;
* promote candidates to canonical classifications.

---

# 31. Validation Closure

The complete DM-2 validation dependency is:

A-1a-N canonical unit
        │
        ▼
DM-2-3 record structure
        │
        ├── identity/span
        │
        ├── semantic vocabulary
        │
        └── semantic attributes
        │
        ▼
DM-2-4 evidence/provenance
        │
        ├── exact phrase provenance
        └── line provenance
        │
        ▼
DM-2-5 resolution state
        │
        ├── resolved
        ├── unknown
        └── ambiguous
        │
        ▼
DM-2-6 deterministic validation
        │
        ├── ACCEPT
        └── REJECT

No validation stage may mutate canonical truth.

---

# 32. Normative Invariants

The following invariants are mandatory:

V-01:
The candidate MUST conform to the applicable JSON Schema.

V-02:
unit_id MUST equal the canonical unit_id.

V-03:
line_start MUST equal the canonical line_start.

V-04:
line_end MUST equal the canonical line_end.

V-05:
source_text MUST equal the canonical source_text exactly.

V-06:
Every evidence phrase MUST be an exact substring of source_text.

V-07:
Every evidence line MUST lie within line_start..line_end.

V-08:
Evidence lines MUST be unique.

V-09:
Phrase and line arrays MUST NOT be interpreted as positional pairs.

V-10:
semantic_kind MUST belong to the closed vocabulary.

V-11:
Every semantic attribute MUST belong to its closed vocabulary.

V-12:
Unknown, Ambiguous, and Unclassified MUST NOT be conflated.

V-13:
Candidate semantic kinds MUST NOT become canonical classification implicitly.

V-14:
A-1a boundaries MUST NOT be modified by DM-2.

V-15:
Causal fields MUST NOT enter the DM-2 record.

V-16:
Invalid records MUST be rejected, not repaired.

V-17:
The validator MUST NOT perform semantic reinterpretation.

V-18:
Validation MUST be deterministic.

V-19:
The validator MUST NOT silently expand the schema or vocabulary.

V-20:
The validator MUST NOT mutate canonical input.

---

# 33. Freeze Criteria

DM-2-6 is conformant only if:

1. schema validation is deterministic;
2. canonical identity is checked against A-1a-N;
3. canonical source text is immutable;
4. evidence phrases are exact substrings;
5. evidence lines remain inside the canonical span;
6. phrase/line positional correspondence is not assumed;
7. all semantic kinds use the closed vocabulary;
8. all semantic attributes use their closed vocabularies;
9. Unknown / Ambiguous semantics are validated explicitly;
10. causal content is rejected;
11. A-1a boundaries cannot be changed;
12. invalid records are rejected rather than repaired;
13. semantic interpretation is outside validator authority;
14. diagnostics identify violated rules;
15. identical inputs produce identical validation results;
16. no undocumented schema or vocabulary expansion occurs;
17. canonical input is never mutated.

---

# 34. Final DM-2 Validation Boundary

DM-2-6 establishes the following authority boundary:

A-1a-N
    =
canonical unit authority

DM-2
    =
semantic proposal / extraction

DM-2-6
    =
deterministic conformance validation

Validator
    ≠
semantic classifier

Validator
    ≠
repair engine

Validator
    ≠
boundary editor

Validator
    ≠
causal engine

The only canonical acceptance decision available to DM-2-6 is:

ACCEPT

or:

REJECT

A rejected record MUST NOT become canonical semantic output.
