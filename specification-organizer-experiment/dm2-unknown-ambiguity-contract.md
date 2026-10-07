# DM-2-5 Unknown / Ambiguous Contract

**Document:** `dm2-unknown-ambiguity-contract.md`
**Version:** 1.0
**Status:** Finalized
**Scope:** Chron-LLM Specification Organizer — DM-2 Semantic Extraction
**Layer:** DM-2-5 Unknown / Ambiguous

---

# 0. Purpose

DM-2-5 defines the normative handling of semantic classification states that cannot be established with sufficient certainty from one immutable A-1a canonical unit.

DM-2-5 provides explicit representations for:

* unknown semantic classification;
* insufficient evidence;
* ambiguous semantic classification;
* unresolved interpretation;
* multiple plausible semantic classifications.

DM-2-5 prevents the LLM from converting uncertainty into an unsupported definitive classification.

DM-2-5 does not modify A-1a boundaries.

---

# 1. Fundamental Principle

Semantic uncertainty MUST be represented explicitly.

The system MUST prefer:

```text
explicit uncertainty
```

over:

```text
unsupported certainty
```

An uncertain semantic interpretation MUST NOT be converted into a definitive semantic classification merely to satisfy a closed vocabulary.

---

# 2. Relationship to `Unclassified`

`Unclassified` is a member of the DM-2 closed semantic-kind vocabulary.

```text
Unclassified
```

means that the canonical unit has been processed by DM-2 but no supported semantic kind has been established.

`Unclassified` does NOT by itself specify why classification was unsuccessful.

Possible reasons include:

* insufficient semantic evidence;
* insufficient context;
* genuinely non-classifiable content;
* unresolved ambiguity;
* absence of a suitable closed-vocabulary category.

Therefore:

```text
semantic_kind = Unclassified
```

MUST NOT be interpreted as equivalent to:

```text
ambiguous = true
```

and MUST NOT be interpreted as equivalent to:

```text
evidence_missing = true
```

---

# 3. Unknown State

An unknown state exists when the available canonical unit does not provide sufficient evidence to establish a semantic classification.

Examples include:

* a fragment whose meaning depends on unavailable external context;
* text that cannot be assigned to any closed-vocabulary category from the unit alone;
* content whose semantic function is genuinely indeterminate.

Unknown MUST be represented explicitly.

The system MUST NOT infer a semantic category solely from:

* formatting;
* filename;
* presumed document purpose;
* neighboring units;
* expected architecture;
* LLM prior knowledge;
* categories used elsewhere in the corpus.

---

# 4. Ambiguous State

An ambiguous state exists when two or more classified semantic interpretations remain plausible from the canonical unit and the available evidence does not establish one interpretation as authoritative.

Example:

```text id="kxzke8"
A unit may plausibly represent either:

Requirement

or

Constraint
```

if the source text alone does not provide sufficient evidence to distinguish them.

The system MUST preserve the ambiguity.

The system MUST NOT arbitrarily select one interpretation merely because one appears more probable.

---

# 5. Unknown vs Ambiguous

The two states are normatively distinct.

| State     | Meaning                                                           |
| --------- | ----------------------------------------------------------------- |
| Unknown   | No sufficiently supported classified semantic kind is established |
| Ambiguous | Two or more plausible classified semantic kinds remain unresolved |

Therefore:

```text id="s1mq6j"
Unknown ≠ Ambiguous
```

## Resolution-State Consistency

The following combinations are prohibited:

* `resolution.status = resolved` with `semantic_kind = Unclassified`
* `resolution.status = unknown` with `semantic_kind != Unclassified`
* `resolution.status = ambiguous` with `semantic_kind != Unclassified`

These constraints establish the relationship between the resolution state and the canonical `semantic_kind`.

## Candidate Classification Constraint

`candidate_kinds` represents plausible classified semantic kinds.

Therefore:

* `candidate_kinds` MUST contain only values from the classified DM-2 semantic vocabulary.
* `Unclassified` MUST NOT appear in `candidate_kinds`.
* `candidate_kinds` MUST contain at least two distinct values for `ambiguous`.
* `candidate_kinds` MUST NOT be used for `unknown`.

`Unclassified` is a semantic classification state indicating that a classified semantic kind has not been established. It is not itself a candidate interpretation.

## Distinction

The distinction MUST be preserved as follows:

```text id="y93xss"
Unknown
  = no established classified semantic kind

Ambiguous
  = multiple plausible classified semantic kinds
    remain unresolved
```

Insufficient evidence MUST NOT, by itself, cause a record to be classified as `ambiguous`.

Multiple candidate interpretations MUST NOT be represented as `unknown` when those candidates can be explicitly identified.

The resolution state MUST NOT alter the canonical A-1a unit, its span, or its source text.

---

# 6. Classification Authority

Only evidence supported by the canonical source may establish a definitive semantic classification.

The following are NOT classification authority:

* model confidence alone;
* frequency of a category in the corpus;
* category priors;
* external architectural assumptions;
* neighboring-unit interpretation;
* causal relationships inferred elsewhere;
* downstream graph structure.

The LLM MAY propose an interpretation.

The LLM MUST NOT establish canonical truth.

---

# 7. No Forced Classification

DM-2 MUST NOT force every unit into a definitive semantic kind.

The following behavior is prohibited:

```text
uncertain
    ↓
choose most likely category
    ↓
emit definitive classification
```

The required behavior is:

```text
uncertain
    ↓
represent uncertainty
    ↓
deterministic validation
```

This applies even when the LLM reports high internal confidence without sufficient source evidence.

---

# 8. Candidate Classifications

When ambiguity exists, candidate semantic kinds MAY be recorded as unresolved candidates.

Candidate classifications MUST come exclusively from the existing DM-2 closed vocabulary.

The system MUST NOT create a new semantic category to express uncertainty.

For example, the following is valid conceptually:

```text
candidate kinds:
    Requirement
    Constraint
```

The following is prohibited:

```text
candidate kind:
    "RequirementConstraint"
```

unless that category is separately introduced into the closed vocabulary by a future specification revision.

---

# 9. Candidate Classification Is Not Canonical Classification

A candidate semantic kind is not equivalent to `semantic_kind`.

The following distinction is normative:

```text
semantic_kind
    =
    accepted canonical classification
```

whereas:

```text
candidate_kind
    =
    unresolved possible classification
```

An unresolved candidate MUST NOT be consumed downstream as though it were a canonical semantic kind.

---

# 10. Evidence Requirement

Unknown or ambiguous status MUST NOT be used to weaken evidence requirements.

All evidence phrases remain subject to DM-2-4.

For every evidence phrase:

```text
phrase ∈ source_text
```

MUST remain true.

For every evidence line:

```text
line_start <= line <= line_end
```

MUST remain true.

Ambiguity does not permit synthetic evidence.

---

# 11. Insufficient Evidence

Insufficient evidence means that the canonical unit does not contain enough textual evidence to establish the intended semantic interpretation.

Insufficient evidence is a property of the available evidence.

It is NOT permission to obtain or invent additional information.

The system MUST NOT silently supplement the unit with:

* neighboring units;
* document-level assumptions;
* external specifications;
* generated explanations;
* causal graph information;
* LLM-generated context.

If additional context is introduced in a future specification, that context MUST be represented as a separate, explicitly defined input source.

---

# 12. Context Dependency

A unit MAY be context-dependent.

Context dependency MUST NOT be resolved implicitly.

If the semantic meaning of a unit cannot be determined from the canonical unit alone, the unit MAY remain Unknown or Ambiguous.

The system MUST NOT reconstruct missing context by assuming:

```text
previous heading
+
previous paragraph
+
neighboring bullet
```

constitutes part of the current canonical unit.

A-1a segmentation remains authoritative.

---

# 13. Boundary Immutability

Unknown or ambiguous semantic interpretation MUST NOT modify canonical boundaries.

The following operations remain prohibited:

```text
split unit
merge unit
extend span
shrink span
move line_start
move line_end
rewrite source_text
```

Therefore:

```text
Unknown
    ≠
segmentation failure
```

and:

```text
Ambiguous
    ≠
segmentation failure
```

A semantic uncertainty state belongs to DM-2, not A-1a.

---

# 14. No Causal Resolution

Causal information MUST NOT be used to force a semantic classification.

DM-2-5 MUST NOT resolve semantic ambiguity using:

* causes;
* effects;
* dependencies;
* triggers;
* state transitions;
* mutations;
* graph topology.

Those belong to DM-3 and downstream causal processing.

The semantic extraction layer MUST remain independent of causal inference.

---

# 15. Confidence Is Not Resolution

A numerical or qualitative confidence value produced by the LLM does not itself resolve ambiguity.

For example:

```text
candidate = Requirement
confidence = 0.92
```

does not establish:

```text
semantic_kind = Requirement
```

unless the classification satisfies the normative evidence and validation requirements.

Model confidence is therefore subordinate to deterministic validation and source evidence.

---

# 16. Explicit Uncertainty

Unknown and Ambiguous states MUST be machine-readable.

A future DM-2 record representation MUST be capable of expressing at minimum:

```text
classification status
reason for unresolved state
optional candidate semantic kinds
```

The representation MUST distinguish:

```text
resolved
unknown
ambiguous
```

without relying on free-form prose alone.

---

# 17. Required Uncertainty Reasons

The uncertainty reason vocabulary SHOULD remain closed.

Initial normative values:

```text
insufficient_evidence
multiple_plausible_interpretations
no_matching_category
context_required
unresolved
```

These values describe the state of the extraction.

They are not semantic kinds.

The system MUST NOT invent new reason values during extraction.

Any extension of this vocabulary requires a specification revision.

---

# 18. Candidate Set Constraints

If candidate semantic kinds are recorded:

1. every candidate MUST belong to the DM-2 closed vocabulary;
2. candidates MUST be unique;
3. candidates MUST represent genuinely unresolved alternatives;
4. candidates MUST NOT include arbitrary free-form categories;
5. candidates MUST NOT be interpreted as accepted classifications.

`Unclassified` MAY be used as the accepted semantic kind when no supported classification is established.

`Unclassified` MUST NOT be used as a synthetic candidate representing every possible semantic kind.

---

# 19. Resolved State

A semantic classification is resolved only when one semantic kind is accepted as the canonical interpretation for the unit.

Conceptually:

```text
status = resolved
semantic_kind = one closed-vocabulary kind
```

A resolved state MUST NOT simultaneously claim that the classification remains unresolved.

Therefore:

```text
resolved + unresolved ambiguity
```

is an invalid semantic state unless a future specification explicitly defines a separate primary/secondary classification model.

---

# 20. Unknown State

Conceptually:

```text
status = unknown
semantic_kind = Unclassified
```

may represent a unit for which no supported semantic classification is established.

The exact record encoding is defined by the DM-2-5 schema revision and MUST NOT be inferred by implementation.

---

# 21. Ambiguous State

Conceptually:

```text
status = ambiguous
candidate_kinds = [...]
```

represents unresolved competing interpretations.

The exact record encoding is defined by the DM-2-5 schema revision and MUST NOT be inferred by implementation.

---

# 22. Existing Record Schema Boundary

The current:

```text
dm2-semantic-extraction-record.schema.json
```

defines:

```text
semantic_kind
semantic_evidence
semantic_attributes
```

but does not currently define explicit uncertainty-state fields.

DM-2-5 therefore does NOT silently redefine that existing schema.

A subsequent schema revision MUST explicitly define the machine-readable representation required by this contract.

Until that revision is accepted:

```text
DM-2-5 semantic rules
```

are specification requirements, not permission to add undocumented fields to DM-2-3 records.

---

# 23. Validation Responsibilities

DM-2 validation MUST verify at least:

### Structural validation

* uncertainty status belongs to the closed vocabulary;
* uncertainty reason belongs to the closed vocabulary;
* candidate kinds belong to the semantic-kind vocabulary;
* candidate kinds are unique.

### Semantic consistency

* resolved state has an accepted semantic kind;
* ambiguous state has unresolved candidate interpretations where required;
* unknown state is not falsely represented as a definitive category;
* candidate kinds are not treated as canonical classification.

### Evidence consistency

* evidence remains valid under DM-2-4;
* uncertainty does not permit synthetic evidence;
* canonical source fields remain unchanged.

### Boundary consistency

* uncertainty does not alter A-1a unit identity or span.

Invalid records MUST be rejected.

The validator MUST NOT repair or silently coerce uncertainty states.

---

# 24. No Silent Fallback

The following fallback behavior is prohibited:

```text
invalid classification
    ↓
Unclassified
```

unless the extraction explicitly represents the reason that the unit is unresolved.

Likewise:

```text
ambiguous
    ↓
first candidate
```

is prohibited.

And:

```text
unknown
    ↓
most probable category
```

is prohibited.

Uncertainty MUST remain explicit.

---

# 25. Downstream Contract

Downstream processing MUST distinguish between:

```text
resolved
```

and:

```text
unknown / ambiguous
```

An unresolved semantic record MUST NOT be consumed as though it were a confirmed semantic fact.

Downstream systems MAY:

* preserve the record;
* report it;
* request review;
* perform separate resolution;
* use it as unresolved evidence.

Downstream systems MUST NOT silently promote an unresolved interpretation into canonical semantic truth.

---

# 26. Relationship to DM-2-6

DM-2-5 defines the semantic states.

DM-2-6 defines deterministic validation of those states.

Therefore:

```text
DM-2-5
    ↓
defines valid uncertainty semantics

DM-2-6
    ↓
verifies structural and semantic conformance
```

DM-2-6 MUST NOT invent a resolution for an Unknown or Ambiguous record.

---

# 27. Relationship to DM-3

Unknown or Ambiguous DM-2 results MUST NOT be resolved through causal extraction.

DM-3 MAY consume DM-2 results according to its own contract, but causal information MUST NOT retroactively modify DM-2 semantic classification.

The dependency direction remains:

```text
A-1a
  ↓
DM-2
  ↓
DM-3
```

not:

```text
A-1a
  ↓
DM-2
  ↕
DM-3
```

---

# 28. Normative Invariants

The following invariants are mandatory:

```text
I-1:
A-1a canonical fields are immutable.

I-2:
Unknown is not equivalent to Ambiguous.

I-3:
Unclassified is not itself an ambiguity reason.

I-4:
Candidate semantic kinds are not canonical semantic kinds.

I-5:
Candidates belong to the closed vocabulary.

I-6:
Uncertainty does not justify synthetic evidence.

I-7:
Uncertainty does not modify boundaries.

I-8:
Model confidence does not establish canonical classification.

I-9:
Causal information does not resolve DM-2 semantic classification.

I-10:
Invalid uncertainty states are rejected, not repaired.

I-11:
No undocumented fields are added to the existing DM-2-3 record schema.

I-12:
Unresolved semantic interpretation MUST NOT be promoted silently downstream.
```

---

# 29. Freeze Criteria

DM-2-5 is conformant only if:

1. Unknown and Ambiguous are explicitly distinguished;
2. `Unclassified` remains a semantic kind rather than an implicit ambiguity flag;
3. unresolved candidate classifications are separated from canonical classification;
4. candidate values use only the closed vocabulary;
5. evidence remains governed by DM-2-4;
6. canonical A-1a fields remain immutable;
7. semantic uncertainty cannot alter boundaries;
8. model confidence cannot force resolution;
9. causal information cannot force resolution;
10. invalid uncertainty states are rejected;
11. the existing DM-2-3 schema is not silently modified;
12. the machine-readable uncertainty representation is explicitly specified before implementation.

---

# 30. DM-2-5 Boundary Decision

DM-2-5 establishes the following normative distinction:

```text
RESOLVED
    one supported semantic classification

UNKNOWN
    no supported classification established

AMBIGUOUS
    multiple plausible classifications remain unresolved
```

and:

```text
Unclassified
    =
    semantic kind

Unknown / Ambiguous
    =
    extraction-resolution state
```

These concepts MUST NOT be conflated.

The exact JSON representation of the resolution state is intentionally deferred to an explicit DM-2-5 schema revision and MUST NOT be invented by implementation.
