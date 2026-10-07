# DM-2-3 Extraction Record

**Status:** Draft for Formalization
**Scope:** Chron-LLM Specification Organizer
**Upstream:** A-1a-N / DM-2-0 / DM-2-1 / DM-2-2
**Downstream:** DM-2-4 Evidence / Provenance, DM-2-5 Unknown / Ambiguous Handling, DM-2-6 Validation

---

# 1. Purpose

DM-2-3 defines the canonical semantic extraction record produced from one A-1a canonical unit.

The record represents:

1. the immutable identity and span of the source unit;
2. the DM-2 semantic classification;
3. textual evidence supporting that classification;
4. semantic attributes permitted by the DM-2 contract.

DM-2-3 MUST NOT introduce causal relations or causal graph information.

---

# 2. One-to-One Unit Rule

One DM-2 extraction record corresponds to exactly one A-1a canonical unit.

```text
A-1a canonical unit
        │
        │ 1 : 1
        ▼
DM-2 extraction record
```

DM-2 MUST NOT:

* split one A-1a unit into multiple DM-2 units;
* merge multiple A-1a units into one DM-2 unit;
* change the unit span;
* change the canonical unit identifier;
* reorder units.

---

# 3. Canonical Identity Fields

The following fields are inherited from A-1a-N:

```text
unit_id
line_start
line_end
source_text
```

DM-2 MUST preserve these values exactly.

These fields are provenance-bearing canonical fields, not semantic predictions.

A DM-2 implementation MUST NOT regenerate a different `source_text`.

---

# 4. semantic_kind

`semantic_kind` is the primary semantic classification of the canonical unit.

Its value MUST belong to the DM-2-2 closed vocabulary:

```text
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
```

DM-2 MUST NOT emit a free-form semantic kind.

DM-2 MUST select `Unclassified` when the available evidence does not support an acceptable classification.

---

# 5. semantic_evidence

## 5.1 Definition

`semantic_evidence` identifies textual evidence within the canonical unit that supports the assigned `semantic_kind` and semantic attributes.

Evidence is observationally grounded.

DM-2 MUST NOT create evidence that does not occur in `source_text`.

## 5.2 Evidence Fields

The initial record contains:

```json
{
  "semantic_evidence": {
    "phrases": [],
    "lines": []
  }
}
```

### `phrases`

`phrases` contains exact textual excerpts selected from `source_text`.

Every phrase MUST occur verbatim within `source_text`.

DM-2 MUST NOT normalize, paraphrase, translate, or rewrite evidence phrases.

### `lines`

`lines` identifies source-document line numbers containing the cited evidence.

Every line MUST satisfy:

```text
line_start <= line <= line_end
```

The line numbers refer to the canonical A-1a span.

## 5.3 Evidence Sufficiency

A semantic classification MUST be supported by evidence.

An empty evidence set MUST NOT be used to conceal uncertainty.

If sufficient evidence cannot be identified, DM-2 MUST use the appropriate uncertainty handling defined by DM-2-5 rather than inventing evidence.

---

# 6. semantic_attributes

`semantic_attributes` contains semantic characteristics that supplement `semantic_kind` without introducing causal interpretation.

The initial permitted attributes are:

```text
modality
structural_form
semantic_strength
semantic_scope
```

No other semantic attribute is permitted by this version of the contract.

---

# 7. modality

`modality` describes explicit linguistic modality expressed by the unit.

The initial closed vocabulary is:

```text
must
shall
should
may
cannot
prohibited
required
optional
none
```

`none` indicates that no supported modality is explicitly evidenced.

DM-2 MUST NOT infer a modality merely from domain expectations.

For example, a descriptive statement MUST NOT be converted to `must` because the model considers the statement important.

---

# 8. structural_form

`structural_form` describes the textual/document form represented by the already-frozen A-1a unit.

The initial closed vocabulary is:

```text
heading
paragraph
bullet-list
numbered-list
procedure-block
other
```

`structural_form` is descriptive metadata.

It MUST NOT modify or challenge the A-1a boundary.

For example, if A-1a has classified an entire procedural chain as one canonical unit, DM-2 MAY classify its `structural_form` as `procedure-block`, but MUST NOT create separate units for individual steps.

---

# 9. semantic_strength

`semantic_strength` describes the strength or semantic character of the classification where such information is explicitly supported.

The initial closed vocabulary is:

```text
strong
weak
descriptive
definitional
none
```

`strong` and `weak` are relative semantic-strength classifications.

They MUST NOT be interpreted as causal strength.

They MUST NOT imply probability, confidence, causal force, or graph-edge weight.

`descriptive` and `definitional` identify semantic character rather than normative strength.

`none` indicates that no applicable strength characterization is supported.

---

# 10. semantic_scope

`semantic_scope` describes the explicitly supported scope of applicability represented by the unit.

The initial closed vocabulary is:

```text
global
system-wide
component-specific
local
unspecified
```

DM-2 MUST NOT infer scope solely from general domain knowledge.

`unspecified` MUST be used when the unit does not provide sufficient evidence for a supported scope.

Semantic scope MUST NOT be interpreted as a causal dependency scope.

---

# 11. Causal Boundary

DM-2-3 MUST NOT contain:

* causal edges;
* causes;
* effects;
* triggers;
* dependencies;
* mutations;
* transitions between states;
* causal confidence;
* graph nodes other than the inherited canonical unit identity;
* causal relation types.

The following concepts are explicitly outside this record:

```text
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
```

These MUST NOT be introduced into DM-2-3 merely because they may be useful to DM-3.

---

# 12. Evidence vs Interpretation

DM-2 MUST distinguish evidence from interpretation.

```text
source_text
    ↓
semantic_evidence
    ↓
semantic interpretation
```

`source_text` is canonical evidence inherited from A-1a.

`semantic_evidence` identifies portions of that evidence.

`semantic_kind` and `semantic_attributes` are interpretations derived from that evidence.

An interpretation MUST NOT be represented as if it were source evidence.

---

# 13. Record Invariants

For every valid DM-2-3 record:

1. `unit_id` is inherited unchanged from A-1a-N.
2. `line_start` is inherited unchanged from A-1a-N.
3. `line_end` is inherited unchanged from A-1a-N.
4. `source_text` is inherited unchanged from A-1a-N.
5. `semantic_kind` belongs to the closed vocabulary.
6. every evidence phrase occurs verbatim in `source_text`;
7. every evidence line lies within the canonical span;
8. every semantic attribute belongs to its defined closed vocabulary;
9. no causal field is present;
10. no new document boundary is introduced.

---

# 14. Non-Goals

DM-2-3 does not:

* determine document boundaries;
* normalize source text;
* rewrite specifications;
* infer causal relationships;
* construct graphs;
* determine state transitions;
* determine dependency relations;
* assign causal confidence;
* replace A-1a canonicalization.

---

# 15. Processing Model

```text
A-1a-N canonical unit
        │
        ├── unit_id
        ├── line_start
        ├── line_end
        └── source_text
                 │
                 ▼
          DM-2 semantic observation
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
 semantic_kind evidence attributes
        │        │        │
        └────────┴────────┘
                 │
                 ▼
        DM-2-3 Extraction Record
                 │
                 ▼
        DM-2-4 / DM-2-5 / DM-2-6
                 │
                 ▼
               DM-3
```

DM-2-3 is therefore a semantic observation record, not a causal representation.

## Resolution

Each DM-2 semantic extraction record MUST contain a `resolution` object.

The `resolution` object explicitly records whether the semantic classification is resolved, unknown, or ambiguous.

The resolution state MUST NOT alter the canonical A-1a unit identity, span, or source text.

### Resolution Status

`resolution.status` MUST be exactly one of:

* `resolved`
* `unknown`
* `ambiguous`

### Resolved

When `resolution.status` is `resolved`:

* `semantic_kind` MUST be one value from the closed DM-2 semantic vocabulary other than `Unclassified`.
* `resolution.reason` MUST be `null`.
* `resolution.candidate_kinds` MUST NOT be present.
* The classification is treated as the canonical semantic classification for the unit.

`resolved` MUST NOT be inferred merely from model confidence. It denotes that the extraction record contains a single accepted classified semantic kind under the DM-2 vocabulary.

`Unclassified` MUST NOT be used with `resolution.status = resolved`.

### Unknown

When `resolution.status` is `unknown`:

* `semantic_kind` MUST be `Unclassified`.
* `resolution.candidate_kinds` MUST NOT be present.
* `resolution.reason` MUST be exactly one of:

  * `insufficient_evidence`
  * `no_matching_category`
  * `context_required`
  * `unresolved`

`unknown` means that no sufficiently supported semantic classification can be established from the permitted DM-2 evidence.

`unknown` MUST NOT be converted into a guessed semantic category.

### Ambiguous

When `resolution.status` is `ambiguous`:

* `semantic_kind` MUST be `Unclassified`.
* `resolution.reason` MUST be `multiple_plausible_interpretations`.
* `resolution.candidate_kinds` MUST be present.
* `candidate_kinds` MUST contain at least two distinct values.
* Every candidate MUST belong to the classified portion of the closed DM-2 semantic vocabulary.
* `Unclassified` MUST NOT appear in `candidate_kinds`.
* Candidate kinds represent plausible interpretations only; they are not the canonical `semantic_kind`.

`ambiguous` MUST be used when two or more plausible classified semantic kinds remain unresolved after applying the DM-2 semantic classification rules.

### Unknown vs Ambiguous

`unknown` and `ambiguous` are distinct states.

`unknown` means:

```text
No sufficiently supported classification is established.
```

`ambiguous` means:

```text
Two or more plausible classified semantic kinds remain unresolved.
```

The absence of sufficient evidence MUST NOT automatically be represented as `ambiguous`.

The existence of multiple candidate interpretations MUST NOT be represented as `unknown` when those candidates can be explicitly enumerated.

### Candidate Kinds

`candidate_kinds` is an uncertainty representation only.

It MUST NOT:

* create a new semantic category;
* modify the closed vocabulary;
* contain `Unclassified`;
* create causal relations;
* create document boundaries;
* alter `source_text`;
* alter `line_start` or `line_end`;
* cause DM-2 to re-segment the A-1a unit.

`candidate_kinds` MUST contain only classified semantic kinds from the existing DM-2 closed semantic vocabulary.

`Unclassified` is a semantic classification state indicating that a classified semantic kind has not been established. It is not a candidate interpretation.

### Resolution and Canonical Evidence

Resolution is an interpretation of the immutable canonical A-1a unit.

The following precedence remains mandatory:

```text
A-1a-N canonical unit
        >
semantic evidence
        >
semantic classification
        >
resolution state
        >
candidate interpretations
```

No resolution state may modify or replace canonical evidence.

### Invalid Resolution States

The following states are invalid and MUST be rejected rather than repaired:

* `resolved` with a non-null reason;
* `resolved` with `candidate_kinds`;
* `resolved` with `semantic_kind = Unclassified`;
* `unknown` with `semantic_kind` other than `Unclassified`;
* `unknown` with `candidate_kinds`;
* `unknown` with `multiple_plausible_interpretations`;
* `ambiguous` with `semantic_kind` other than `Unclassified`;
* `ambiguous` with a reason other than `multiple_plausible_interpretations`;
* `ambiguous` without at least two distinct candidate kinds;
* `ambiguous` with `Unclassified` in `candidate_kinds`;
* candidate kinds outside the classified portion of the closed vocabulary.

The validator MUST reject these states without normalization or semantic repair.

