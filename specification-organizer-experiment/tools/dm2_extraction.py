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

Do not perform causal extraction.
Do not generate causal relations.
Do not generate graph structure.

Return JSON only.

Canonical unit:
{json.dumps(canonical_unit, ensure_ascii=False, indent=2)}
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
