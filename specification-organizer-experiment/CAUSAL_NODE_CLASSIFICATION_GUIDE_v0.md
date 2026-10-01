# CAUSAL_NODE_CLASSIFICATION_GUIDE v0 (Freeze-candidate)

## 1. Purpose
This guide defines the minimal semantic rules for Δ1 causal-node extraction.
It fixes only the classification boundaries and evidence model.
Canonical taxonomy, JSON schema, and deterministic ID rules are NOT frozen here.

## 2. Definitions

### 2.1 CAUSAL_NODE
A CAUSAL_NODE is a specification text unit that:
- expresses an independently identifiable semantic entity, claim, state, action,
  constraint, authority, event, or transition, AND
- can participate in a causal, normative, dependency, or state-transition
  relationship with another semantic unit.

### 2.2 NOT_CAUSAL_NODE
A NOT_CAUSAL_NODE is text that:
- lacks independently identifiable semantic role, OR
- cannot meaningfully participate in causal/normative/dependency/state relations.

Examples:
- headings, structural text, introductory paragraphs,
- pure commentary, formatting artifacts,
- invented concepts not grounded in source text.

## 3. Semantic Segmentation
- Markdown structure (paragraphs, bullets, headings, tables, code blocks)
  MUST NOT be treated as semantic units.
- The classifier MUST perform semantic segmentation:
  identify minimal meaningful units before node eligibility testing.

## 4. Node Eligibility Test (LLM MUST follow this exact order)

1. **Semantic Independence**
   - Does the fragment express an independently meaningful semantic unit?
   - NO → NON_NODE
   - YES → proceed

2. **Relational Capability**
   - Can this unit participate in causal/normative/dependency/state relations?
   - NO → NON_NODE
   - YES → proceed

3. **Semantic Role Identification**
   - Assign a provisional semantic role (node type candidate).
   - This is NOT canonical taxonomy.

4. **Claim Evidence**
   - Determine whether the semantic claim itself is:
     - explicit (directly stated)
     - inferred (implied but not stated)

5. **Classification Evidence**
   - Determine whether the classification decision is:
     - explicit (source text directly indicates the role)
     - inferred (classifier deduces the role)

6. **Ambiguity Check**
   - If multiple plausible roles exist → status = ambiguous
   - If no stable role can be assigned → status = unclassified

7. **Source Span Preservation**
   - MUST preserve exact source span (line_start, line_end).

## 5. Provisional Node Categories (NOT frozen)
These categories are provisional and will be refined after Pilot Corpus analysis.

- Invariant
- Authority
- Component
- Fact
- State
- Transition
- Event
- Action / Operation
- Concept / Cluster
- Unclassified

## 6. Evidence Model (explicitly separated)

### 6.1 claim_evidence
Indicates whether the semantic claim is:
- explicit
- inferred

### 6.2 classification_evidence
Indicates whether the classification decision is:
- explicit
- inferred

## 7. Ambiguous / Unclassified / Unresolved

### ambiguous
- Multiple plausible classifications.
- Node is valid but classification is not stable.

### unclassified
- Node is valid but classification cannot be determined.

### unresolved
- Node validity OR classification cannot be determined due to:
  - missing context,
  - unclear semantics,
  - contradictory text,
  - extraction errors.

`resolution_status` MUST be one of:
- resolved
- ambiguous
- unclassified
- unresolved

## 8. Multi-node Extraction
- A single semantic unit MAY yield multiple nodes.
- Classifier MUST NOT collapse distinct semantic roles into one node.

## 9. Prohibited
- causal edge generation
- CAE relation vocabulary (mutates, triggers, etc.)
- old Δ1 vocabulary (State/Operation/Invariant as fixed types)
- invented nodes
- invented relations

## 10. Required Output Fields (NOT a schema; classification contract)

Each semantic unit MUST produce:

source_text
source_span: [line_start, line_end]
is_node: true | false

classification:
primary: string | null
alternatives: [string]
status: classified | ambiguous | unclassified

claim_evidence: explicit | inferred
classification_evidence: explicit | inferred

reason: string
confidence: 0.0–1.0

resolution_status: resolved | ambiguous | unclassified | unresolved