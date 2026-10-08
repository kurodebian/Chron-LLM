#!/usr/bin/env python3
# tools/a1_segment.py

import argparse
import json
from pathlib import Path
from tools.llm_backend import call_llm, LLMConfig


CONTRACT_PATH = Path("a1_boundary_observation_contract.json")


# ------------------------------------------------------------
# Source loading
# ------------------------------------------------------------

def load_source(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.readlines()


# ------------------------------------------------------------
# LLM boundary observation
# ------------------------------------------------------------

def detect_boundaries_llm(document_path: str, lines: list[str]) -> dict:
    """
    A-1a-O: LLM Boundary Observation.

    MUST:
      - return raw LLM observation as-is
      - do NOT repair, sort, drop, or modify spans
      - do NOT generate source_text
      - do NOT assign semantic taxonomy
      - do NOT generate causal relations
      - do NOT enforce DM-2 boundaries
    """

    source_text = "".join(lines)
    line_count = len(lines)

    numbered_source = "".join(
        f"{i+1:04d} | {line}"
        for i, line in enumerate(lines)
    )

    prompt = build_boundary_prompt(
        document_path=document_path,
        source_text=numbered_source,
        line_count=line_count,
    )

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
        n_predict=4096,
        single_turn=True,

        simple_io=True,
        display_prompt=False,
        show_timings=False,
        reasoning="off",

        grammar_path=(
            "/home/junu/Chron-LLM/"
            "specification-organizer-experiment/"
            "grammars/a1_boundary.gbnf"
        ),
        runtime_revision="b10709-9a9394a89",
    )

    observation = call_llm(prompt, config)

    json_text = extract_boundary_json(
        observation.raw_output
    )

    try:
        parsed = json.loads(json_text)
    except Exception as e:
        raise ValueError(
            f"INVALID_OBSERVATION: JSON parse failed: {e}"
        ) from e

    return parsed


# ------------------------------------------------------------

# Prompt

# ------------------------------------------------------------

def build_boundary_prompt(
    document_path: str,
    source_text: str,
    line_count: int,
) -> str:

    return f"""\

You are a boundary observation engine.

Your ONLY task is to identify semantic/document boundaries
in the supplied source document.

A semantic/document boundary is a contiguous span of source lines
that contains meaningful document content and forms one logically
coherent unit.

A boundary is defined by the content contained in the span,
not by whitespace, formatting gaps, or paragraph separation.

A boundary MUST:

* contain at least one non-blank line;
* contain meaningful document content;
* represent one logically coherent content unit.

A boundary MUST NOT:

* consist only of blank or whitespace-only lines;
* be a blank line;
* represent a spacing gap or formatting gap;
* represent a paragraph break by itself;
* merge unrelated content units;
* merge multiple top-level sections into one span;
* cover the entire document merely because it is contiguous.

Valid boundary units may include:

* a section heading (lines starting with '#', '##', '###');
* a paragraph consisting of one or more non-blank lines;
* a bullet list item;
* a numbered constraint or requirement;
* another contiguous group of non-blank lines that forms one
  logically coherent document unit.

Blank lines between content units are separators only.
They are not boundary units and MUST NOT be emitted as spans.

You MUST emit a boundary for each distinct logical content unit
that is present in the source document.

Do NOT classify semantic meaning.
Do NOT assign taxonomy.
Do NOT identify causal relations.
Do NOT generate graph structure.

Return JSON only.

Required output:

{{
    "boundaries": [
        {{
            "line_start": <integer>,
            "line_end": <integer>
        }}
    ]
}}

Rules:

* line numbers are 1-based and inclusive;
* boundaries must appear in document order;
* spans must not overlap;
* duplicate spans are forbidden;
* line_start must be >= 1;
* line_end must be >= line_start;
* line_end must not exceed the document line count;
* do not emit source_text;
* do not emit semantic_kind;
* do not emit node_type;
* do not emit causal_role;
* do not emit normative_role;
* do not emit state_role;
* do not emit transition_role;
* do not emit event_role;
* do not emit relation_kind;
* do not emit edges or graph structure.

Document path:
{document_path}

Document line count:
{line_count}

The number before "|" is the original 1-based source line number.
Use that number for line_start and line_end.
The number and "|" are presentation metadata and are not source content.

Source document:
<BEGIN_SOURCE>
{source_text}
<END_SOURCE>
"""


# ------------------------------------------------------------
# Raw observation validation
# ------------------------------------------------------------

def validate_raw_observation(
    observation: dict,
    lines: list[str],
) -> None:
    """
    Validate A-1a-O raw LLM observation.

    Invalid observations are rejected.
    Nothing is repaired or silently discarded.
    """

    if not isinstance(observation, dict):
        raise ValueError(
            "INVALID_OBSERVATION: root must be an object"
        )

    if set(observation.keys()) != {"boundaries"}:
        raise ValueError(
            "INVALID_OBSERVATION: unexpected root fields"
        )

    boundaries = observation["boundaries"]

    if not isinstance(boundaries, list):
        raise ValueError(
            "INVALID_OBSERVATION: boundaries must be an array"
        )

    line_count = len(lines)

    previous_start = 0
    previous_end = 0
    seen = set()

    for index, boundary in enumerate(boundaries):
        if not isinstance(boundary, dict):
            raise ValueError(
                f"INVALID_OBSERVATION: boundary[{index}] "
                "must be an object"
            )

        if set(boundary.keys()) != {
            "line_start",
            "line_end",
        }:
            raise ValueError(
                f"INVALID_OBSERVATION: boundary[{index}] "
                "contains forbidden fields"
            )

        start = boundary["line_start"]
        end = boundary["line_end"]

        if not isinstance(start, int) or isinstance(start, bool):
            raise ValueError(
                f"INVALID_OBSERVATION: boundary[{index}].line_start"
            )

        if not isinstance(end, int) or isinstance(end, bool):
            raise ValueError(
                f"INVALID_OBSERVATION: boundary[{index}].line_end"
            )

        if start < 1:
            raise ValueError(
                f"INVALID_OBSERVATION: boundary[{index}] "
                "line_start < 1"
            )

        if end < start:
            raise ValueError(
                f"INVALID_OBSERVATION: boundary[{index}] "
                "line_end < line_start"
            )

        if end > line_count:
            raise ValueError(
                f"INVALID_OBSERVATION: boundary[{index}] "
                "out of range"
            )

        source_text = "".join(
            lines[start - 1:end]
        )

        if source_text.strip() == "":
            raise ValueError(
                "INVALID_OBSERVATION: "
                f"whitespace-only span "
                f"{start}-{end}"
            )

        span = (start, end)

        if span in seen:
            raise ValueError(
                f"INVALID_OBSERVATION: duplicate span {span}"
            )

        seen.add(span)

        if index > 0 and start < previous_start:
            raise ValueError(
                "INVALID_OBSERVATION: boundaries are unsorted"
            )

        if index > 0 and start <= previous_end:
            raise ValueError(
                f"INVALID_OBSERVATION: overlapping span {span}"
            )

        previous_start = start
        previous_end = end


# ------------------------------------------------------------
# Deterministic normalization
# ------------------------------------------------------------

def normalize_boundaries(
    observation: dict,
    lines: list[str],
) -> list[dict]:
    """
    Convert VALID A-1a-O observations into canonical units.

    No semantic interpretation occurs here.
    """

    normalized_units = []

    for index, boundary in enumerate(
        observation["boundaries"],
        start=1,
    ):
        line_start = boundary["line_start"]
        line_end = boundary["line_end"]

        source_text = "".join(
            lines[line_start - 1:line_end]
        )

        normalized_units.append({
            "unit_id": f"u{index:04d}",
            "line_start": line_start,
            "line_end": line_end,
            "source_text": source_text,
        })

    return normalized_units


# ------------------------------------------------------------
# Output
# ------------------------------------------------------------

def write_units(
    document_path: str,
    units: list[dict],
) -> Path:

    output_path = (
        Path("semantic_units")
        / f"{document_path}.units.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "document_path": document_path,
        "units": units,
    }

    with open(
        output_path,
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )
        f.write("\n")

    return output_path

def extract_json_object(raw_output: str) -> str:
    """
    Extract the first syntactically complete JSON object from CLI output.

    This is transport-level extraction only.
    It does not interpret or repair the A-1a schema.
    """
    decoder = json.JSONDecoder()

    for index, char in enumerate(raw_output):
        if char != "{":
            continue

        try:
            _, end = decoder.raw_decode(raw_output, index)
        except json.JSONDecodeError:
            continue

        return raw_output[index:end]

    raise ValueError(
        "INVALID_OBSERVATION: "
        "no complete JSON object found in LLM output"
    )

def extract_boundary_json(raw_output: str) -> str:
    """
    Extract the A-1a JSON object from llama-cli transport output.

    This removes CLI/UI envelope only.
    It does not repair or normalize the observation.
    """
    marker = '"boundaries"'

    marker_positions = []
    start = 0

    while True:
        index = raw_output.find(marker, start)
        if index == -1:
            break
        marker_positions.append(index)
        start = index + 1

    decoder = json.JSONDecoder()

    for marker_index in marker_positions:
        object_start = raw_output.rfind("{", 0, marker_index)

        if object_start == -1:
            continue

        try:
            _, object_end = decoder.raw_decode(
                raw_output,
                object_start,
            )
        except json.JSONDecodeError:
            continue

        candidate = raw_output[object_start:object_end]

        try:
            candidate_object = json.loads(candidate)
        except json.JSONDecodeError:
            continue

        if (
            isinstance(candidate_object, dict)
            and set(candidate_object.keys()) == {"boundaries"}
        ):
            return candidate

    raise ValueError(
        "INVALID_OBSERVATION: "
        "A-1a boundary JSON object not found in LLM output"
    )