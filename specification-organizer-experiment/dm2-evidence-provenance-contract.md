# DM-2-4 Evidence / Provenance Contract

**Document:** `dm2-evidence-provenance-contract.md`
**Version:** 1.0
**Status:** Finalized
**Scope:** Chron-LLM Specification Organizer — DM-2 Semantic Extraction
**Layer:** DM-2-4 Evidence / Provenance

---

## 0. Purpose

DM-2-4 defines the normative semantics of:

* semantic evidence,
* evidence phrase provenance,
* evidence line provenance,
* canonical source provenance,
* separation between source evidence and LLM interpretation.

DM-2-4 constrains the semantic extraction record produced by DM-2-3.

DM-2-4 does not define:

* semantic classification vocabulary,
* semantic attributes,
* causal relations,
* causal inference,
* document segmentation,
* canonical unit generation.

Those responsibilities belong to other DM-2 layers or A-1a.

---

# 1. Normative Principle

The canonical A-1a-N unit is the sole source of semantic evidence consumed by DM-2.

The following fields are canonical and immutable:

```text
unit_id
line_start
line_end
source_text
```

DM-2 MUST treat these fields as source evidence.

DM-2 MUST NOT replace, reconstruct, normalize, paraphrase, translate, or otherwise modify the canonical source evidence.

---

# 2. Evidence / Interpretation Separation

DM-2 produces two fundamentally different classes of information.

## 2.1 Source Evidence

Source evidence is information directly inherited from the canonical A-1a-N unit.

Source evidence consists of:

```text
unit_id
line_start
line_end
source_text
semantic_evidence.phrases
semantic_evidence.lines
```

These values MUST be traceable to the canonical source unit.

## 2.2 LLM Interpretation

The following are interpretations produced by DM-2:

```text
semantic_kind
semantic_attributes.modality
semantic_attributes.structural_form
semantic_attributes.semantic_strength
semantic_attributes.semantic_scope
```

These values MUST NOT be treated as source quotations.

They are classification or interpretation results derived from the canonical source text.

---

# 3. Canonical Source Provenance

## 3.1 Canonical Source

For a DM-2 record, the canonical source is the exact A-1a-N canonical unit supplied as DM-2 input.

The canonical source is identified locally by:

```text
unit_id
line_start
line_end
source_text
```

The four fields MUST remain exactly identical between the DM-2 input and the corresponding DM-2 extraction record.

## 3.2 No Source Reconstruction

DM-2 MUST NOT reconstruct canonical source text from:

* Markdown structure,
* headings,
* list markers,
* inferred paragraphs,
* semantic interpretations,
* normalized whitespace,
* generated text,
* LLM output.

`source_text` MUST be carried forward exactly as supplied by A-1a-N.

## 3.3 Document-Level Provenance Boundary

The current DM-2 canonical-unit contract does not contain an explicit document identifier.

Therefore, DM-2-4 does NOT define or invent a new document-level provenance field.

In particular, DM-2 MUST NOT introduce fields such as:

```text
document_id
document_path
source_file
source_document
document_uri
```

unless such fields are explicitly introduced by a future upstream canonical-input specification.

Consequently, DM-2-4 defines **unit-local canonical provenance**, not a standalone document-identity mechanism.

---

# 4. Semantic Evidence Phrases

`semantic_evidence.phrases` contains textual excerpts selected from the canonical `source_text`.

Each phrase MUST:

1. be a string;
2. occur verbatim in `source_text`;
3. preserve the original character sequence;
4. preserve the original wording;
5. preserve the original language;
6. NOT be paraphrased;
7. NOT be translated;
8. NOT be normalized;
9. NOT be generated independently of `source_text`.

The following transformations are prohibited:

```text
source quotation
    ↓
paraphrase
    ↓
semantic_evidence.phrases
```

```text
source quotation
    ↓
translation
    ↓
semantic_evidence.phrases
```

```text
source quotation
    ↓
whitespace normalization
    ↓
semantic_evidence.phrases
```

Only the original textual excerpt is valid evidence.

---

# 5. Empty Evidence Phrase Set

An empty:

```json
"phrases": []
```

is structurally valid.

An empty phrase set MUST NOT be interpreted as permission to invent evidence.

If no suitable textual excerpt can be identified, the record MUST preserve the empty evidence state rather than fabricate a quotation.

Whether a particular semantic classification requires non-empty evidence is a separate DM-2 validation rule.

---

# 6. Evidence Lines

`semantic_evidence.lines` identifies source-document line numbers associated with the semantic evidence.

Each evidence line MUST satisfy:

```text
line_start <= evidence_line <= line_end
```

Evidence lines MUST therefore refer only to lines contained by the canonical A-1a unit.

An evidence line MUST NOT refer to a line outside the canonical unit.

Invalid:

```text
canonical unit:
line_start = 13
line_end   = 23

semantic_evidence.lines:
[12]
```

Valid:

```text
canonical unit:
line_start = 13
line_end   = 23

semantic_evidence.lines:
[13, 17, 21]
```

---

# 7. Phrase / Line Correspondence

The current DM-2-3 record represents evidence using two arrays:

```json
{
  "phrases": [],
  "lines": []
}
```

DM-2-4 therefore does NOT require a one-to-one positional mapping between the two arrays.

In particular:

```text
phrases[0] ↔ lines[0]
```

is NOT a normative relationship.

`phrases` identifies exact textual evidence.

`lines` identifies source-document lines containing or associated with that evidence.

The normative relationship is:

```text
phrases ⊆ source_text
```

and:

```text
lines ⊆ [line_start, line_end]
```

Exact phrase-to-line mapping is not represented by the current DM-2-3 record structure.

A future schema MAY introduce explicit evidence objects if exact phrase-to-line correspondence becomes a normative requirement. Such a change requires a separate specification revision.

---

# 8. Evidence Does Not Create Boundaries

Semantic evidence MUST NOT be used to alter A-1a boundaries.

DM-2 MUST NOT:

* split a canonical unit because multiple evidence phrases exist;
* merge canonical units because they share evidence;
* move an evidence line into another unit;
* redefine `line_start`;
* redefine `line_end`;
* create a new semantic unit.

The canonical unit boundary is authoritative.

Therefore:

```text
A-1a boundary
    ↓
immutable canonical unit
    ↓
DM-2 evidence selection
```

and never:

```text
A-1a boundary
    ↓
DM-2 evidence
    ↓
new boundary
```

---

# 9. Evidence vs Semantic Classification

The presence of a phrase in `semantic_evidence.phrases` does not itself establish the semantic classification.

For example:

```json
{
  "semantic_evidence": {
    "phrases": ["must remain immutable"],
    "lines": [42]
  },
  "semantic_kind": "Requirement"
}
```

contains:

```text
"must remain immutable"
```

as source evidence.

The value:

```text
"Requirement"
```

is an interpretation.

The interpretation MUST NOT be presented as though it were directly present in the source text.

---

# 10. No Synthetic Evidence

DM-2 MUST NOT generate evidence that does not occur in the canonical source.

The following are invalid:

```text
"the system must preserve state"
```

when that exact text does not occur in `source_text`.

Likewise invalid:

```text
"必須保持状態"
```

when the canonical source contains only the original-language expression.

Evidence is extraction, not generation.

---

# 11. Provenance Invariant

For every DM-2 record:

```text
record.unit_id
    == input.unit_id

record.line_start
    == input.line_start

record.line_end
    == input.line_end

record.source_text
    == input.source_text
```

These equality relationships are normative.

No semantic interpretation may modify canonical provenance.

---

# 12. Evidence Integrity Invariants

For every `phrase` in:

```text
semantic_evidence.phrases
```

the following MUST hold:

```text
phrase ∈ source_text
```

where membership means exact textual substring occurrence.

For every `line` in:

```text
semantic_evidence.lines
```

the following MUST hold:

```text
line_start <= line <= line_end
```

The validator MUST reject records violating these conditions.

The validator MUST NOT repair invalid evidence.

---

# 13. Evidence and LLM Output

The LLM is permitted to propose:

```text
semantic_evidence.phrases
semantic_evidence.lines
```

but the LLM output itself is not canonical evidence.

Canonical evidence is established only after deterministic validation against the canonical A-1a source unit.

Therefore:

```text
LLM output
    ↓
candidate evidence
    ↓
deterministic validation
    ↓
accepted evidence
```

An invalid candidate MUST be rejected.

The system MUST NOT silently:

* truncate an invalid phrase;
* replace a phrase with a nearby phrase;
* correct spelling;
* normalize whitespace;
* change line numbers;
* select a different source phrase.

---

# 14. Provenance Authority

The authority hierarchy is:

```text
A-1a-N canonical unit
        │
        │ authoritative source
        ▼
DM-2 semantic evidence
        │
        │ interpretation derived from source
        ▼
DM-2 semantic classification
```

Therefore:

```text
Canonical Source
    > Evidence Selection
    > Semantic Interpretation
```

Semantic interpretation MUST NOT override canonical source evidence.

---

# 15. Relationship to DM-2-3

DM-2-3 defines the record structure.

DM-2-4 defines the evidence and provenance semantics of that structure.

DM-2-4 does not introduce additional top-level record fields.

The DM-2-3 structure remains:

```text
unit_id
line_start
line_end
source_text
semantic_kind
semantic_evidence
semantic_attributes
```

The existing JSON Schema therefore remains structurally applicable to DM-2-4.

Cross-field and source-dependent constraints defined here belong to deterministic validation rather than JSON Schema syntax alone.

---

# 16. Explicit Non-Responsibilities

DM-2-4 MUST NOT perform or define:

* A-1a segmentation;
* unit splitting;
* unit merging;
* causal extraction;
* causal relation detection;
* dependency extraction;
* trigger/effect identification;
* state transition inference;
* graph construction;
* semantic taxonomy expansion;
* provenance field invention;
* source-text rewriting.

---

# 17. Freeze Criteria

DM-2-4 is considered conformant only if:

1. canonical A-1a fields are immutable;
2. `source_text` remains the authoritative source;
3. every evidence phrase is an exact substring of `source_text`;
4. every evidence line lies within the canonical unit span;
5. phrase-to-line positional correspondence is not falsely assumed;
6. no synthetic or translated evidence is accepted;
7. evidence cannot modify A-1a boundaries;
8. source evidence and LLM interpretation remain explicitly separated;
9. invalid evidence is rejected rather than repaired;
10. no undocumented provenance field is introduced.

---

# 18. DM-2-4 Boundary Decision

The current DM-2-4 contract establishes:

```text
CANONICAL PROVENANCE
    =
    immutable A-1a unit identity/span/source

EVIDENCE
    =
    exact excerpts + source line references

INTERPRETATION
    =
    semantic_kind + semantic_attributes

DOCUMENT IDENTITY
    =
    NOT YET REPRESENTED BY THE CURRENT DM-2 INPUT CONTRACT
```

The absence of an explicit document identifier is therefore a known specification boundary, not an invitation for DM-2 to invent one.
