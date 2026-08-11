#!/usr/bin/env python3
"""Phase 2: Qwen3.6 Semantic Fact Extractor for Chron-LLM."""

import json
import argparse
import re
from pathlib import Path
from typing import Dict, Any, List
import urllib.request
import urllib.error
import jsonschema
from json_repair import repair_json


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract Phase 2 semantic facts using Qwen3.6."
    )
    parser.add_argument(
        "--input", default="spec-index/facts.jsonl", help="Phase 1 facts.jsonl path"
    )
    parser.add_argument(
        "--output",
        default="spec-index/facts_phase2.jsonl",
        help="Output path for Phase 2",
    )
    parser.add_argument(
        "--system-prompt",
        default="tools/spec-index/prompts/phase2_system.txt",
        help="System prompt path",
    )
    parser.add_argument(
        "--schema",
        default="tools/spec-index/schemas/phase2_schema.json",
        help="JSON Schema path",
    )
    parser.add_argument(
        "--endpoint",
        default="http://localhost:8080/v1/chat/completions",
        help="OpenAI-compatible API endpoint",
    )
    parser.add_argument("--model", default="qwen3.6-35b-moe", help="Model name")
    parser.add_argument(
        "--no-json-mode",
        action="store_true",
        help="Disable response_format=json_object if server fails",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=8192,
        help="Max output tokens for LLM response",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print raw LLM responses"
    )
    return parser.parse_args()


def clean_json_response(raw_text: str) -> str:
    """Strip thinking tags (<think>...</think>) and markdown code fences."""
    if not raw_text:
        return ""
    text = raw_text.strip()

    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"<thought>.*?</thought>", "", text, flags=re.DOTALL).strip()

    pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[-1].strip()
    return text


def _stringify_item(item: Any) -> str:
    """辞書や数値を文字列へ安全にフラット化するヘルパー関数"""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for val_key in [
            "target",
            "name",
            "dependency",
            "use",
            "claim",
            "text",
            "rule",
            "value",
            "description",
            "statement",
        ]:
            if val_key in item and item[val_key]:
                return str(item[val_key])
        return json.dumps(item, ensure_ascii=False)
    return str(item)


def normalize_semantic_facts(raw_facts: Dict[str, Any]) -> Dict[str, Any]:
    """Qwen3.6が出力するJSON構造の表記揺れや要素型をスキーマ要求に合わせて自動補正する。"""
    if "semantic_facts" in raw_facts and isinstance(raw_facts["semantic_facts"], dict):
        data = raw_facts["semantic_facts"]
    elif isinstance(raw_facts, dict):
        data = raw_facts
    else:
        data = {}

    key_aliases = {
        "concepts_and_definitions": [
            "concepts_and_definitions",
            "concepts",
            "definitions",
            "terms",
        ],
        "invariants_and_rules": [
            "invariants_and_rules",
            "invariants",
            "rules",
            "invariants_and_constraints",
        ],
        "boundary_claims": ["boundary_claims", "boundaries", "boundary_conditions"],
        "dependencies_and_uses": [
            "dependencies_and_uses",
            "dependencies",
            "uses",
            "imports",
        ],
        "unresolved_statements": [
            "unresolved_statements",
            "unresolved",
            "issues",
            "todos",
        ],
    }

    normalized = {}
    for target_key, aliases in key_aliases.items():
        extracted_val = None
        for alias in aliases:
            if alias in data and isinstance(data[alias], list):
                extracted_val = data[alias]
                break
        normalized[target_key] = extracted_val if extracted_val is not None else []

    # 1. concepts_and_definitions の構造補正 ({term, raw_text, section})
    fixed_concepts = []
    for item in normalized["concepts_and_definitions"]:
        if isinstance(item, dict):
            term = item.get("term") or item.get("id") or item.get("name") or "UNKNOWN"
            raw_text = (
                item.get("raw_text")
                or item.get("definition")
                or item.get("description")
                or ""
            )
            section = item.get("section") or ""
            fixed_concepts.append(
                {"term": str(term), "raw_text": str(raw_text), "section": str(section)}
            )
        elif isinstance(item, str):
            fixed_concepts.append({"term": item[:30], "raw_text": item, "section": ""})
    normalized["concepts_and_definitions"] = fixed_concepts

    # 2. invariants_and_rules の構造補正 ({type, rule, section})
    fixed_invariants = []
    for item in normalized["invariants_and_rules"]:
        if isinstance(item, dict):
            rule = (
                item.get("rule")
                or item.get("statement")
                or item.get("text")
                or item.get("description")
                or ""
            )
            inv_type = item.get("type") or "RULE"
            section = item.get("section") or ""
            fixed_invariants.append(
                {"type": str(inv_type), "rule": str(rule), "section": str(section)}
            )
        elif isinstance(item, str):
            inv_type = "INVARIANT" if ("INV_" in item or "不変" in item) else "RULE"
            fixed_invariants.append({"type": inv_type, "rule": item, "section": ""})
    normalized["invariants_and_rules"] = fixed_invariants

    # 3. boundary_claims の構造補正 ({claim_type, statement})
    fixed_boundaries = []
    for item in normalized["boundary_claims"]:
        if isinstance(item, dict):
            claim_type = item.get("claim_type") or item.get("type") or "BOUNDARY"
            statement = (
                item.get("statement")
                or item.get("claim")
                or item.get("text")
                or item.get("description")
                or ""
            )
            fixed_boundaries.append(
                {"claim_type": str(claim_type), "statement": str(statement)}
            )
        elif isinstance(item, str):
            fixed_boundaries.append({"claim_type": "BOUNDARY", "statement": item})
    normalized["boundary_claims"] = fixed_boundaries

    # 4. dependencies_and_uses (文字列配列に整形)
    normalized["dependencies_and_uses"] = [
        _stringify_item(x) for x in normalized["dependencies_and_uses"]
    ]

    # 5. unresolved_statements (文字列配列に整形)
    normalized["unresolved_statements"] = [
        _stringify_item(x) for x in normalized["unresolved_statements"]
    ]

    return normalized


def call_qwen(
    endpoint: str,
    model: str,
    system_prompt: str,
    user_payload: Dict[str, Any],
    use_json_mode: bool = True,
    max_tokens: int = 8192,
) -> Dict[str, Any]:
    headers = {"Content-Type": "application/json"}

    enforced_system_prompt = (
        system_prompt
        + "\n\nIMPORTANT: Return ONLY a valid JSON object matching the requested schema. Do NOT wrap in explanation text."
    )

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": enforced_system_prompt},
            {
                "role": "user",
                "content": json.dumps(user_payload, ensure_ascii=False, indent=2),
            },
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }

    if use_json_mode:
        body["response_format"] = {"type": "json_object"}

    req = urllib.request.Request(
        endpoint, data=json.dumps(body).encode("utf-8"), headers=headers
    )
    content = ""
    try:
        with urllib.request.urlopen(req) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            choice = res_data.get("choices", [{}])[0]
            message = choice.get("message", {})

            content = message.get("content") or message.get("reasoning_content") or ""
            cleaned_content = clean_json_response(content)

            if not cleaned_content.strip():
                finish_reason = choice.get("finish_reason", "unknown")
                raise ValueError(
                    f"API returned empty content (finish_reason: '{finish_reason}')"
                )

            try:
                parsed_obj = json.loads(cleaned_content)
            except json.JSONDecodeError:
                parsed_obj = repair_json(cleaned_content, return_objects=True)
                if not isinstance(parsed_obj, dict):
                    raise ValueError(
                        f"Repaired JSON is not a valid dict object (got {type(parsed_obj).__name__})"
                    )

            return parsed_obj

    except urllib.error.URLError as e:
        raise RuntimeError(f"API Connection Error: {e}")
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        if use_json_mode and (
            "empty content" in str(e) or "not a valid dict" in str(e)
        ):
            return call_qwen(
                endpoint,
                model,
                system_prompt,
                user_payload,
                use_json_mode=False,
                max_tokens=max_tokens,
            )
        raise RuntimeError(
            f"Invalid API response structure: {e}\nRaw Content Repr: {repr(content)}"
        )


def main():
    args = parse_args()

    system_prompt = Path(args.system_prompt).read_text(encoding="utf-8")
    with open(args.schema, "r", encoding="utf-8") as f:
        schema = json.load(f)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    records_processed = 0
    use_json_mode = not args.no_json_mode

    with (
        open(args.input, "r", encoding="utf-8") as infile,
        open(out_path, "w", encoding="utf-8") as outfile,
    ):
        for line_num, line in enumerate(infile, 1):
            if not line.strip():
                continue

            p1_record = json.loads(line)
            spec_path = p1_record.get("spec_path") or p1_record.get("path")

            if p1_record.get("content_state") == "EMPTY":
                record_phase2 = {
                    "spec_path": spec_path,
                    "sha256": p1_record.get("sha256"),
                    "physical": p1_record,
                    "semantic_facts": {
                        "concepts_and_definitions": [],
                        "invariants_and_rules": [],
                        "boundary_claims": [],
                        "dependencies_and_uses": [],
                        "unresolved_statements": ["EMPTY_FILE"],
                    },
                    "analysis": None,
                    "decision": None,
                }
                outfile.write(json.dumps(record_phase2, ensure_ascii=False) + "\n")
                records_processed += 1
                continue

            raw_content = ""
            if spec_path:
                target_file = Path(spec_path)
                if target_file.exists():
                    raw_content = target_file.read_text(
                        encoding="utf-8", errors="replace"
                    )
                else:
                    print(
                        f"  └─ WARNING: Spec file not found at '{spec_path}'. Passing empty content."
                    )
            else:
                print(
                    f"  └─ WARNING: Record #{line_num} has no 'spec_path' or 'path' key."
                )

            user_payload = {"physical": p1_record, "raw_content": raw_content}

            print(f"[{line_num}] Extracting semantic facts: {spec_path}...")

            try:
                raw_facts = call_qwen(
                    args.endpoint,
                    args.model,
                    system_prompt,
                    user_payload,
                    use_json_mode=use_json_mode,
                    max_tokens=args.max_tokens,
                )

                if args.verbose:
                    print("\n--- [RAW LLM RESPONSE] ---")
                    print(json.dumps(raw_facts, ensure_ascii=False, indent=2))
                    print("--------------------------\n")

                extracted_facts = normalize_semantic_facts(raw_facts)
                jsonschema.validate(instance=extracted_facts, schema=schema)

            except Exception as e:
                print(f"  └─ WARNING: Validation/API error on {spec_path}: {e}")
                extracted_facts = {
                    "concepts_and_definitions": [],
                    "invariants_and_rules": [],
                    "boundary_claims": [],
                    "dependencies_and_uses": [],
                    "unresolved_statements": [f"EXTRACTION_FAILED: {str(e)}"],
                }

            record_phase2 = {
                "spec_path": spec_path,
                "sha256": p1_record.get("sha256"),
                "physical": p1_record,
                "semantic_facts": extracted_facts,
                "analysis": None,
                "decision": None,
            }

            outfile.write(json.dumps(record_phase2, ensure_ascii=False) + "\n")
            records_processed += 1

    print(
        f"\nPhase 2 Complete. Total records written to {args.output}: {records_processed}"
    )


if __name__ == "__main__":
    main()
