# Common Specification IR - Canonical Baseline Artifact
# VERSION 0.1 | STATUS DRAFT | MODE SPECIFICATION_FIRST | GOVERNANCE STRICT
# This artifact is a normative specification document (SOURCE_SPECIFICATION
# tier). It is not a parser, not a checker, and not an implementation.

version: "0.1"
status: "DRAFT"
mode: "SPECIFICATION_FIRST"
governance: "STRICT"
implementation: "LOCKED"
source_of_truth: "SOURCE_SPECIFICATION"
title: "Common Specification IR v0.1 Baseline"
root: "SPEC"

purpose: >-
  Unify heterogeneous specification syntax into an evidence-preserving
  Common Specification IR suitable for the pipeline:
  SOURCE_SPECIFICATION -> COMMON_SPECIFICATION_IR -> SPECIFICATION_GRAPH ->
  CAUSAL/INVARIANT/AUTHORITY_VALIDATION.

non_goals:
  - source rewriting
  - source replacement
  - unstated semantic inference
  - semantic repair
  - implementation generation
  - runtime state generation
  - causal inference not explicitly supported by source evidence

authority_order:
  - "SOURCE_SPECIFICATION"
  - "SOURCE_EVIDENCE"
  - "COMMON_SPEC_IR"
  - "SPECIFICATION_GRAPH"
  - "DERIVED_ANALYSIS"
  note: >-
    Strict descending order of authority. No IR node, derived field, graph
    node, or format syntax outranks the source specification or the source
    evidence that supports it.

axioms:
  - id: "IR-001"
    name: "SOURCE_TEXT_IS_CANONICAL_EVIDENCE"
  - id: "IR-002"
    name: "IR_IS_EVIDENCE_PRESERVING_DERIVATION"
  - id: "IR-003"
    name: "UNSTATED_SOURCE_SEMANTICS_MUST_NOT_BE_CREATED"
  - id: "IR-004"
    name: "AMBIGUITY_MUST_BE_REPRESENTED_NOT_RESOLVED_BY_ASSUMPTION"
  - id: "IR-005"
    name: "NORMALIZATION_MUST_NOT_DELETE_SOURCE_INFORMATION"
  - id: "IR-006"
    name: "EVERY_SEMANTIC_IR_NODE_MUST_HAVE_SOURCE_TRACEABILITY"
  - id: "IR-007"
    name: "FORMAT_SYNTAX_IS_NOT_SEMANTIC_IDENTITY"
  - id: "IR-008"
    name: "IDENTICAL_SEMANTIC_CATEGORY_MAY_HAVE_MULTIPLE_SOURCE_SYNTAXES"
  - id: "IR-009"
    name: "SOURCE_SYNTAX_MUST_REMAIN_RECONSTRUCTABLE"
  - id: "IR-010"
    name: "UNKNOWN_IS_NOT_FALSE"
  - id: "IR-011"
    name: "ABSENT_IS_NOT_UNKNOWN"
  - id: "IR-012"
    name: "INFERRED_IS_NOT_EXPLICIT"

root_node: "SPEC"

required_node_types:
  - "SPEC"
  - "CLAIM"
  - "ENTITY"
  - "TYPE"
  - "ENUM"
  - "OPERATION"
  - "INVARIANT"
  - "THEOREM"
  - "POLICY"
  - "TEST"
  - "RELATION"
  - "AUTHORITY"
  - "EVIDENCE"
  - "UNKNOWN"

source_reference_contract:
  every_semantic_ir_node: "MUST carry source traceability"
  required_attributes:
    - "source document identity"
    - "source region identity"
    - "path"
    - "line/region information"
    - "raw source representation where available"

semantic_assertion_status:
  values:
    - "EXPLICIT"
    - "AMBIGUOUS"
    - "UNKNOWN"

provenance:
  values:
    - "EXPLICIT"
    - "DERIVED"

assertion_status_provenance_rule:
  statement: >-
    ASSERTION_STATUS and PROVENANCE are independent dimensions. They must be
    carried separately on every semantic IR node and must never be collapsed
    into one field or one value.

identity:
  statement: >-
    Semantic identity MUST NOT depend solely on source syntax. Identity MUST
    support the four fields: SOURCE_ID, SOURCE_VERSION, LOCAL_ID, NODE_TYPE.

unknown:
  status: "FIRST_CLASS"
  distinctions:
    - "UNKNOWN != FALSE"
    - "ABSENT != UNKNOWN"
    - "INFERRED != EXPLICIT"
  meaning: >-
    UNKNOWN is a first-class status for values that cannot be established
    from source evidence. It is never treated as FALSE, as ABSENT, or as
    EXPLICIT.

transformation_rule:
  allowed_normalization_changes:
    - "syntax representation"
    - "category representation"
    - "identifiers"
    - "nesting representation"
    - "format metadata"
  forbidden_invention: >-
    Normalization MUST NOT invent authority, causality, dependency, invariant,
    type, policy, requirement, or prohibition unless explicitly supported by
    source evidence.

loss_contract:
  information_loss: "PROHIBITED except when explicitly represented as UNKNOWN, AMBIGUOUS, or UNSUPPORTED"
  parser_failure: "MUST NOT be interpreted as source absence"

conflict_handling:
  statement: >-
    When sources conflict:
      1. Preserve both source assertions.
      2. Preserve both source references.
      3. Represent the conflict explicitly.
      4. Do not silently resolve the conflict.

traceability:
  statement: >-
    Every semantic IR node MUST be traceable to its source (IR-006).
    Derived fields MUST be marked DERIVED.
    Unresolved fields MUST be represented as UNKNOWN/AMBIGUOUS as applicable.

source_reconstruction:
  requirement: >-
    Source syntax MUST remain reconstructable (IR-009): every IR representation
    MUST be accompanied by source references sufficient to recover the original
    source syntax for the covered regions.
  p10_contract:
    capabilities:
      - "SOURCE_DOCUMENT_RAW_CONTENT"
      - "COMPLETE_SOURCE_REGION_PARTITION"
      - "SOURCE_REGION_ORDERING"
      - "STRUCTURAL_ORDERING"
      - "PRESERVATION_OF_ALL_UNCOVERED_SOURCE_SPANS"
    closure_rule: >-
      P10_SOURCE_RECONSTRUCTION remains OPEN in v0.1. The capabilities above
      are defined here as the normative v0.1 contract, but contract
      definition alone is not closure: closure requires implementation
      evidence, which is locked out of scope in v0.1.
    p10_status_in_v0_1: "OPEN"
    closure_claim: "FORBIDDEN in v0.1 without implementation evidence"

format_independence:
  statement: >-
    The IR MUST be independent of Common Lisp syntax, type-theoretic
    specification DSL, test-format syntax, and parser-specific syntax.
    (IR-007) The container syntax of this file carries no semantics beyond
    what is explicitly normative above.

legacy_parser_classification:
  target: "organizer.py"
  classification: "LEGACY_EXTRACTOR"
  rule: >-
    organizer.py MUST NOT be treated as the canonical IR definition. It is
    a legacy extraction tool only.

validation_phases:
  - "SOURCE_COVERAGE"
  - "TRACEABILITY"
  - "STRUCTURAL"
  - "REFERENCE"
  - "SEMANTIC_CONSISTENCY"
  - "GRAPH_CONSTRUCTION"

freeze_boundary:
  frozen_in_v0_1:
    - "schema"
    - "semantic categories"
    - "authority ordering"
    - "traceability requirements"
    - "loss contract"
    - "UNKNOWN/AMBIGUITY handling"
    - "format independence"
  out_of_scope:
    - "implementation"
    - "organizer rewrite"
    - "model selection"
    - "prompt optimization"
    - "code generation"
    - "runtime integration"

change_policy:
  - "Do not add speculative primitives merely because a future checker might need them."
  - "Do not mix lexical parser rules into the semantic IR."
  - "Do not create closure claims that require implementation evidence."
  - "Do not solve P10 inside v0.1 by assertion."
