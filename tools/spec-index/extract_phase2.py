#!/usr/bin/env python3
"""Phase 2: Qwen3.6 Semantic Fact Extractor for Chron-LLM.

改修仕様:
1. Qwenの生出力 (raw_semantic_facts) を不変のまま完全保存。
2. Python側での意味補完・分類推測・欠損埋め・null->[]変換を全廃。
3. 表記上の非破壊整形（trim等）のみを行う SemanticsPreservingNormalizer を実装。
4. Schema Validation エラーを SCHEMA_VIOLATION として独立分類・記録。
5. $.起点の JSON Pointer による変更差分 (changes) の機械的記録。
"""

import json
import argparse
import re
import copy
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
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


class AuditTracker:
    """監査カテゴリおよび変換差分を正確にトラッキングするクラス。"""

    def __init__(self):
        self.summary_counts = {
            "lossless_normalization_count": 0,
            "semantic_transformation_count": 0,
            "fabrication_count": 0,
            "schema_violation_count": 0,
            "normalization_error_count": 0,
        }
        self.changes: List[Dict[str, Any]] = []
        self.schema_violations: List[Dict[str, Any]] = []
        self.errors: List[str] = []

    def log_change(self, path: str, category: str, op: str, before: Any, after: Any):
        key_map = {
            "LOSSLESS_NORMALIZATION": "lossless_normalization_count",
            "SEMANTIC_TRANSFORMATION": "semantic_transformation_count",
            "FABRICATION": "fabrication_count",
        }
        if category in key_map:
            self.summary_counts[key_map[category]] += 1

        self.changes.append(
            {
                "path": path,
                "category": category,
                "op": op,
                "before": before,
                "after": after,
            }
        )

    def log_schema_violation(self, path: str, message: str):
        self.summary_counts["schema_violation_count"] += 1
        self.schema_violations.append({"path": path, "message": message})

    def log_error(self, message: str):
        self.summary_counts["normalization_error_count"] += 1
        self.errors.append(message)

    def to_dict(self) -> Dict[str, Any]:
        is_pure = (
            self.summary_counts["semantic_transformation_count"] == 0
            and self.summary_counts["fabrication_count"] == 0
            and self.summary_counts["schema_violation_count"] == 0
            and self.summary_counts["normalization_error_count"] == 0
        )
        return {
            "is_pure_semantics_preserved": is_pure,
            "summary_counts": self.summary_counts,
            "changes": self.changes,
            "schema_violations": self.schema_violations,
            "errors": self.errors,
        }


class SemanticsPreservingNormalizer:
    """意味を非破壊で保持しつつ、必要最小限の表記整形のみを行う正規化器。"""

    @classmethod
    def normalize(cls, raw_data: Any) -> Tuple[Any, AuditTracker]:
        tracker = AuditTracker()
        if raw_data is None:
            return None, tracker

        # ルート配下の再帰処理
        processed_data = copy.deepcopy(raw_data)

        # もしルートが {"semantic_facts": {...}} でラップされている場合は構造解除を記録
        if (
            isinstance(processed_data, dict)
            and "semantic_facts" in processed_data
            and len(processed_data) == 1
        ):
            unwrapped = processed_data["semantic_facts"]
            tracker.log_change(
                path="$",
                category="LOSSLESS_NORMALIZATION",
                op="unwrap_semantic_facts_root",
                before="<wrapped_dict>",
                after="<unwrapped_dict>",
            )
            processed_data = unwrapped

        normalized_result = cls._traverse_and_clean(
            processed_data, path="$", tracker=tracker
        )
        return normalized_result, tracker

    @classmethod
    def _traverse_and_clean(cls, data: Any, path: str, tracker: AuditTracker) -> Any:
        if data is None:
            return None

        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                clean_key = k.strip() if isinstance(k, str) else k
                key_path = f"{path}.{clean_key}"

                if clean_key != k:
                    tracker.log_change(
                        path=f"{path}.{k}",
                        category="LOSSLESS_NORMALIZATION",
                        op="trim_key",
                        before=k,
                        after=clean_key,
                    )

                new_dict[clean_key] = cls._traverse_and_clean(
                    v, path=key_path, tracker=tracker
                )
            return new_dict

        if isinstance(data, list):
            new_list = []
            for idx, item in enumerate(data):
                item_path = f"{path}[{idx}]"
                new_list.append(
                    cls._traverse_and_clean(item, path=item_path, tracker=tracker)
                )
            return new_list

        if isinstance(data, str):
            clean_str = data.strip()
            if clean_str != data:
                tracker.log_change(
                    path=path,
                    category="LOSSLESS_NORMALIZATION",
                    op="trim_string",
                    before=data,
                    after=clean_str,
                )
            return clean_str

        return data


def validate_schema_against_audit(
    data: Any, schema: Dict[str, Any], tracker: AuditTracker
):
    """JSON Schemaに照らし合わせ、不適合を SCHEMA_VIOLATION として独立記録する（データ補正は行わない）。"""
    if data is None:
        tracker.log_schema_violation("$", "Data is None (Extraction empty or failed)")
        return

    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

    for err in errors:
        # JSON Pointer 形式のパス構築
        json_path = "$." + ".".join(map(str, err.path)) if err.path else "$"
        tracker.log_schema_violation(json_path, err.message)


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

            # --- 空ファイルの観測処理 ---
            if (
                p1_record.get("content_state") == "EMPTY"
                or p1_record.get("is_empty") is True
            ):
                tracker = AuditTracker()
                record_phase2 = {
                    "spec_path": spec_path,
                    "sha256": p1_record.get("sha256"),
                    "physical": p1_record,
                    "raw_semantic_facts": None,  # ★ 未実行事実として None
                    "semantic_facts": None,  # ★ 人工生成せず None
                    "normalization_audit": tracker.to_dict(),
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
                    print(f"  └─ WARNING: Spec file not found at '{spec_path}'.")
            else:
                print(
                    f"  └─ WARNING: Record #{line_num} has no 'spec_path' or 'path' key."
                )

            user_payload = {"physical": p1_record, "raw_content": raw_content}

            print(f"[{line_num}] Extracting semantic facts: {spec_path}...")

            raw_semantic_facts = None
            semantic_facts = None
            tracker = AuditTracker()

            try:
                # 1. API呼び出しによる生レスポンス取得
                raw_qwen_output = call_qwen(
                    args.endpoint,
                    args.model,
                    system_prompt,
                    user_payload,
                    use_json_mode=use_json_mode,
                    max_tokens=args.max_tokens,
                )

                # ★ raw_semantic_facts の不変保存用にディープコピー
                raw_semantic_facts = copy.deepcopy(raw_qwen_output)

                if args.verbose:
                    print("\n--- [RAW LLM RESPONSE] ---")
                    print(json.dumps(raw_semantic_facts, ensure_ascii=False, indent=2))
                    print("--------------------------\n")

                # 2. 意味非破壊正規化 (Semantics-Preserving Normalization)
                semantic_facts, tracker = SemanticsPreservingNormalizer.normalize(
                    raw_semantic_facts
                )

                # 3. Schema Validation（非補正・観察型）
                validate_schema_against_audit(semantic_facts, schema, tracker)

            except Exception as e:
                print(f"  └─ WARNING: API or Extraction error on {spec_path}: {e}")
                tracker.log_error(str(e))

            # 4. レコード出力
            record_phase2 = {
                "spec_path": spec_path,
                "sha256": p1_record.get("sha256"),
                "physical": p1_record,
                "raw_semantic_facts": raw_semantic_facts,  # ★ 不変生出力
                "semantic_facts": semantic_facts,  # ★ 非破壊正規化出力
                "normalization_audit": tracker.to_dict(),  # ★ 監査ログ
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
