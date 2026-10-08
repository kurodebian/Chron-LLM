import json
from typing import Callable

from tools.validate_dm2 import validate_semantic_extraction_json

from tools.llm_backend import call_llm, LLMConfig

def build_dm2_prompt(canonical_unit: dict) -> str:
    return f"""
You are a DM-2 semantic extraction engine.

Your ONLY task is to classify and extract semantic information
from ONE canonical A-1a unit.

The canonical unit is immutable.

MUST NOT split the unit.
MUST NOT merge the unit.
MUST NOT reorder units.
MUST NOT modify unit_id.
MUST NOT modify line_start.
MUST NOT modify line_end.
MUST NOT modify source_text.
MUST NOT perform causal extraction.
MUST NOT generate causal relations.
MUST NOT generate graph structure.

You MUST return exactly ONE JSON object.
Return JSON only.
Do not output Markdown.
Do not output code fences.
Do not output explanations.
Do not output any text before or after the JSON object.

## Required output structure

The JSON object MUST contain exactly these top-level fields:

- unit_id
- line_start
- line_end
- source_text
- semantic_kind
- semantic_evidence
- semantic_attributes
- resolution

No other top-level fields are permitted.

## Canonical identity fields

Copy these fields from the canonical unit EXACTLY:

- unit_id
- line_start
- line_end
- source_text

Never infer, rewrite, normalize, truncate, or otherwise modify them.

## semantic_kind

semantic_kind MUST be exactly one of:

- Heading
- Requirement
- Constraint
- Definition
- Description
- Procedure
- State
- Event
- Exception
- Unclassified

Do not invent categories.
Do not use lowercase or aliases.

## semantic_evidence

semantic_evidence MUST have exactly these fields:

{{
  "phrases": ["..."],
  "lines": [1]
}}

- phrases: exact phrases from source_text that support the semantic classification.
- lines: source line numbers supporting the classification.
- Do not invent evidence that is not present in the canonical unit.

## semantic_attributes

semantic_attributes MUST have exactly these fields:

{{
  "modality": "...",
  "structural_form": "...",
  "semantic_strength": "...",
  "semantic_scope": "..."
}}

modality MUST be one of:

- must
- shall
- should
- may
- cannot
- prohibited
- required
- optional
- none

structural_form MUST be one of:

- heading
- paragraph
- bullet-list
- numbered-list
- procedure-block
- other

semantic_strength MUST be one of:

- strong
- weak
- descriptive
- definitional
- none

semantic_scope MUST be one of:

- global
- system-wide
- component-specific
- local
- unspecified

## resolution

resolution MUST have:

{{
  "status": "...",
  "reason": null
}}

status MUST be exactly one of:

- resolved
- unknown
- ambiguous

### If status is "resolved"

- semantic_kind MUST NOT be "Unclassified".
- reason MUST be null.
- candidate_kinds MUST NOT be present.

Example:

{{
  "status": "resolved",
  "reason": null
}}

### If status is "unknown"

- semantic_kind MUST be "Unclassified".
- reason MUST be one of:
  - insufficient_evidence
  - no_matching_category
  - context_required
  - unresolved
- candidate_kinds MUST NOT be present.

Example:

{{
  "status": "unknown",
  "reason": "insufficient_evidence"
}}

### If status is "ambiguous"

- semantic_kind MUST be "Unclassified".
- reason MUST be exactly:
  "multiple_plausible_interpretations"
- candidate_kinds MUST be present.
- candidate_kinds MUST contain at least two distinct valid semantic kinds.
- candidate_kinds MUST NOT contain "Unclassified".

Example:

{{
  "status": "ambiguous",
  "reason": "multiple_plausible_interpretations",
  "candidate_kinds": [
    "Requirement",
    "Constraint"
  ]
}}

## Forbidden legacy output format

Do NOT use the old semantic extraction format.

NEVER emit these fields:

- semantic_type
- subject
- predicate
- object
- polarity

These fields are NOT part of DM-2 V2.

## Forbidden causal/graph fields

NEVER emit:

- claims
- entities
- actions
- conditions
- causes
- effects
- dependencies
- triggers
- mutations
- transitions
- causal_relations
- causal_confidence
- edges
- graph

## Example

For the canonical unit:

{{
  "unit_id": "u0001",
  "line_start": 13,
  "line_end": 15,
  "source_text": "The system SHALL preserve canonical evidence."
}}

a valid resolved output is:

{{
  "unit_id": "u0001",
  "line_start": 13,
  "line_end": 15,
  "source_text": "The system SHALL preserve canonical evidence.",
  "semantic_kind": "Requirement",
  "semantic_evidence": {{
    "phrases": ["SHALL preserve canonical evidence"],
    "lines": [13]
  }},
  "semantic_attributes": {{
    "modality": "shall",
    "structural_form": "paragraph",
    "semantic_strength": "strong",
    "semantic_scope": "system-wide"
  }},
  "resolution": {{
    "status": "resolved",
    "reason": null
  }}
}}

Do not copy this example blindly.
Classify the supplied canonical unit according to its actual content.

## Canonical unit

{json.dumps(canonical_unit, ensure_ascii=False, indent=2)}

Return exactly one DM-2 V2 JSON object and nothing else.
""".strip()


def extract_dm2_record(
    canonical_unit: dict,
    llm_call: Callable[[str], str],
) -> dict:
    prompt = build_dm2_prompt(canonical_unit)

    raw_output = llm_call(prompt)

    if not isinstance(raw_output, str) or not raw_output.strip():
        raise ValueError("INVALID_DM2_OUTPUT: empty LLM output")

    validate_semantic_extraction_json(
        canonical_unit,
        raw_output,
    )

    return json.loads(raw_output)


def extract_dm2_records(
    canonical_units: list[dict],
    llm_call: Callable[[str], str],
) -> list[dict]:
    if not isinstance(canonical_units, list):
        raise ValueError("INVALID_DM2_INPUT: canonical_units must be a list")

    records = []

    for canonical_unit in canonical_units:
        records.append(
            extract_dm2_record(
                canonical_unit=canonical_unit,
                llm_call=llm_call,
            )
        )

    return records

def extract_dm2_record_llm(
    canonical_unit: dict,
) -> dict:
    prompt = build_dm2_prompt(canonical_unit)

    config = LLMConfig(
        command=(
            "/home/junu/llama.cpp-prism/build/bin/llama-cli",
        ),
        model_path=(
            "/home/junu/models/"
            "Ternary-Bonsai-2-27B-PTQ1_0.gguf"
        ),
        temperature=0.0,
        top_k=40,
        top_p=1.0,
        seed=0,
        n_predict=2048,
        single_turn=True,
        machine_output=True,
        simple_io=True,
        display_prompt=False,
        show_timings=False,
        reasoning="off",
        runtime_revision="b10709-9a9394a89",
    )

    observation = call_llm(prompt, config)

    return extract_dm2_record(
        canonical_unit=canonical_unit,
        llm_call=lambda _prompt: observation.raw_output,
    )
