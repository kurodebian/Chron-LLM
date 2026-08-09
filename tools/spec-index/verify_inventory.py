#!/usr/bin/env python3
"""
GATE-1: Physical Provenance Integrity Verifier
Freeze Version

Responsibility
--------------

1. .spec files

   - Physical Source of Truth (SSOT)

2. facts.jsonl

   - Phase 1 physical observation evidence
   - STRICT SCHEMA
   - No aliases
   - No fallback
   - No inferred values
   - No additional fields

3. spec-map.json

   - Processing / inventory map
   - NOT an evidence source
   - Required physical metadata must nevertheless match
     the actual files

GATE-1 MUST PASS CONDITIONS
---------------------------

1. ACTUAL_SPEC_PATHS == SPEC_MAP_PATHS == PHASE1_FACT_PATHS

2. No duplicate spec_path exists in:
   - spec-map.json
   - facts.jsonl

3. facts.jsonl conforms EXACTLY to:

   {
       "spec_path": str,
       "bytes": int >= 0,
       "lines": int >= 0,
       "is_empty": bool,
       "sha256": lowercase hexadecimal 64 chars
   }

   No additional fields.
   No aliases.
   No fallback.
   No inferred values.

4. spec-map.json item contains the required structure:

   {
       "path": str,
       "physical": {
           "bytes": int >= 0,
           "lines": int >= 0,
           "is_empty": bool
       }
   }

   Additional inventory metadata at item/root level is permitted because
   spec-map.json is an index/map rather than a strict evidence record.

5. Actual file == Phase 1 evidence:
   - bytes
   - lines
   - is_empty
   - sha256

6. Actual file == spec-map:
   - bytes
   - lines
   - is_empty

7. is_empty is explicit and is NEVER obtained by fallback
   from another field.

8. is_empty must be physically coherent:

       is_empty == (bytes == 0)

9. JSON structural / syntax / decoding errors are explicit
   GATE failures.

10. One or more violations => GATE-1 FAIL.

11. Only GATE-1 PASS permits transition to Phase 2.

Line-count definition
---------------------

`lines` is defined as the number of newline-terminated records
(`b"\\n"` occurrences) in the physical file.

This definition MUST be identical to the Phase 1 producer.
No alternative line-count interpretation is permitted.
"""

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set


# ============================================================================
# Paths
# ============================================================================

SPECS_DIR = Path("specs")
MAP_PATH = Path("spec-index/.inventory/spec-map.json")
FACTS_PATH = Path("spec-index/facts.jsonl")


# ============================================================================
# Constants / Strict Schemas
# ============================================================================

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

FACT_REQUIRED_FIELDS = {
    "spec_path",
    "bytes",
    "lines",
    "is_empty",
    "sha256",
}

FACT_ALLOWED_FIELDS = FACT_REQUIRED_FIELDS

MAP_REQUIRED_ITEM_FIELDS = {
    "path",
    "physical",
}

MAP_REQUIRED_PHYSICAL_FIELDS = {
    "bytes",
    "lines",
    "is_empty",
}


# ============================================================================
# Validation helpers
# ============================================================================

def validate_non_negative_int(value: Any) -> bool:
    """
    Strict non-negative integer validation.

    bool is intentionally rejected because bool is a subclass of int
    in Python.
    """
    return type(value) is int and value >= 0


def validate_bool(value: Any) -> bool:
    """Strict boolean validation."""
    return type(value) is bool


def validate_non_empty_string(value: Any) -> bool:
    """Strict non-empty string validation."""
    return isinstance(value, str) and bool(value.strip())


def validate_sha256(value: Any) -> bool:
    """
    Strict SHA-256 representation:

    exactly 64 lowercase hexadecimal characters.
    """
    return (
        isinstance(value, str)
        and SHA256_PATTERN.fullmatch(value) is not None
    )


# ============================================================================
# Physical observation
# ============================================================================

def compute_sha256(path: Path) -> str:
    """Compute SHA-256 of the physical file."""
    digest = hashlib.sha256()

    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def count_lines(path: Path) -> int:
    """
    Count physical newline-terminated lines.

    Definition:
        number of b"\\n" occurrences.

    This intentionally avoids Python text iteration so that the
    physical measurement definition is explicit and deterministic.
    """
    count = 0

    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            count += chunk.count(b"\n")

    return count


def collect_actual_spec_paths() -> Set[str]:
    """
    Collect all .spec files physically present under the repository root.

    Paths are represented using POSIX separators.
    """
    root_dir = Path(".")
    exclude_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__"}

    return {
        p.as_posix()
        for p in root_dir.glob("**/*.spec")
        if p.is_file() and not any(part in exclude_dirs for part in p.parts)
    }

# ============================================================================
# JSON loading
# ============================================================================

def load_json_file(
    path: Path,
    errors: List[str],
) -> Any:
    """
    Load a JSON file while converting syntax, decoding, and I/O failures
    into explicit GATE errors.
    """
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError as exc:
        errors.append(
            f"JSON_SYNTAX_ERROR: {path}: "
            f"line={exc.lineno}, column={exc.colno}: {exc.msg}"
        )

    except UnicodeDecodeError as exc:
        errors.append(
            f"JSON_ENCODING_ERROR: {path}: {exc}"
        )

    except OSError as exc:
        errors.append(
            f"FILE_READ_ERROR: {path}: {exc}"
        )

    return None


# ============================================================================
# spec-map.json validation
# ============================================================================

def load_and_validate_spec_map(
    errors: List[str],
) -> tuple[Set[str], Dict[str, Dict[str, Any]]]:
    """
    Validate spec-map.json structure and return:

        map_paths
        map_by_path

    The required item fields are:

        path
        physical

    The physical object must contain:

        bytes
        lines
        is_empty

    Additional inventory metadata is permitted because spec-map.json
    is an index/map rather than a strict evidence record.
    """

    map_paths: Set[str] = set()
    map_seen: Set[str] = set()
    map_by_path: Dict[str, Dict[str, Any]] = {}

    data = load_json_file(MAP_PATH, errors)

    if data is None:
        return map_paths, map_by_path

    if not isinstance(data, dict):
        errors.append(
            "SPEC_MAP_SCHEMA_ERROR: root must be a JSON object."
        )
        return map_paths, map_by_path

    if "items" not in data:
        errors.append(
            "SPEC_MAP_SCHEMA_ERROR: "
            "missing required root field 'items'."
        )
        return map_paths, map_by_path

    items = data["items"]

    if not isinstance(items, list):
        errors.append(
            "SPEC_MAP_SCHEMA_ERROR: "
            "'items' must be an array."
        )
        return map_paths, map_by_path

    for index, item in enumerate(items):

        if not isinstance(item, dict):
            errors.append(
                f"SPEC_MAP_SCHEMA_ERROR: "
                f"item[{index}] must be an object."
            )
            continue

        # ------------------------------------------------------------------
        # Required item fields
        # ------------------------------------------------------------------

        missing_item_fields = (
            MAP_REQUIRED_ITEM_FIELDS - set(item.keys())
        )

        if missing_item_fields:
            errors.append(
                f"spec-map.json item[{index}]: "
                f"missing required fields "
                f"{sorted(missing_item_fields)}."
            )

        # ------------------------------------------------------------------
        # path
        # ------------------------------------------------------------------

        if "path" not in item:
            continue

        path_key = item["path"]

        if not validate_non_empty_string(path_key):
            errors.append(
                f"spec-map.json item[{index}]: "
                f"'path' must be a non-empty string."
            )
            continue

        # ------------------------------------------------------------------
        # Duplicate path
        # ------------------------------------------------------------------

        if path_key in map_seen:
            errors.append(
                "DUPLICATE_SPEC_PATH in spec-map.json: "
                f"'{path_key}' appears multiple times."
            )

        map_seen.add(path_key)
        map_paths.add(path_key)
        map_by_path[path_key] = item

        # ------------------------------------------------------------------
        # physical
        # ------------------------------------------------------------------

        if "physical" not in item:
            errors.append(
                f"[{path_key}] SPEC_MAP_SCHEMA_ERROR: "
                f"missing required object 'physical'."
            )
            continue

        physical = item["physical"]

        if not isinstance(physical, dict):
            errors.append(
                f"[{path_key}] SPEC_MAP_SCHEMA_ERROR: "
                f"'physical' must be an object."
            )
            continue

        # ------------------------------------------------------------------
        # Required physical fields
        # ------------------------------------------------------------------

        missing_physical_fields = (
            MAP_REQUIRED_PHYSICAL_FIELDS - set(physical.keys())
        )

        if missing_physical_fields:
            errors.append(
                f"[{path_key}] SPEC_MAP_SCHEMA_ERROR: "
                f"missing required physical fields "
                f"{sorted(missing_physical_fields)}."
            )

        # ------------------------------------------------------------------
        # physical.bytes
        # ------------------------------------------------------------------

        if "bytes" in physical:
            if not validate_non_negative_int(physical["bytes"]):
                errors.append(
                    f"[{path_key}] INVALID_PHYSICAL_FIELD: "
                    f"'physical.bytes' must be a non-negative integer, "
                    f"got {physical['bytes']!r}."
                )

        # ------------------------------------------------------------------
        # physical.lines
        # ------------------------------------------------------------------

        if "lines" in physical:
            if not validate_non_negative_int(physical["lines"]):
                errors.append(
                    f"[{path_key}] INVALID_PHYSICAL_FIELD: "
                    f"'physical.lines' must be a non-negative integer, "
                    f"got {physical['lines']!r}."
                )

        # ------------------------------------------------------------------
        # physical.is_empty
        # ------------------------------------------------------------------

        if "is_empty" in physical:
            if not validate_bool(physical["is_empty"]):
                errors.append(
                    f"[{path_key}] INVALID_PHYSICAL_FIELD: "
                    f"'physical.is_empty' must be boolean, "
                    f"got {physical['is_empty']!r}."
                )

        # ------------------------------------------------------------------
        # Internal physical coherence
        #
        # This is NOT inference.
        # It is a validity constraint on explicitly supplied fields.
        # ------------------------------------------------------------------

        if (
            validate_non_negative_int(physical.get("bytes"))
            and validate_bool(physical.get("is_empty"))
        ):
            expected_empty = physical["bytes"] == 0

            if physical["is_empty"] != expected_empty:
                errors.append(
                    f"[{path_key}] INVALID_PHYSICAL_RELATION: "
                    f"'physical.is_empty'="
                    f"{physical['is_empty']!r} "
                    f"contradicts 'physical.bytes'="
                    f"{physical['bytes']!r}."
                )

    return map_paths, map_by_path


# ============================================================================
# facts.jsonl validation
# ============================================================================

def load_and_validate_phase1_facts(
    errors: List[str],
) -> tuple[Set[str], Dict[str, Dict[str, Any]]]:
    """
    Validate Phase 1 facts.jsonl against the EXACT strict schema.

    Exactly these fields are permitted:

        spec_path
        bytes
        lines
        is_empty
        sha256

    No aliases.
    No fallback.
    No inferred values.
    No additional fields.
    """

    p1_paths: Set[str] = set()
    p1_seen: Set[str] = set()
    p1_facts: Dict[str, Dict[str, Any]] = {}

    try:
        with FACTS_PATH.open(
            "r",
            encoding="utf-8",
        ) as f:

            for line_num, line in enumerate(f, 1):

                # Blank physical lines are not JSONL records.
                if not line.strip():
                    continue

                try:
                    record = json.loads(line)

                except json.JSONDecodeError as exc:
                    errors.append(
                        f"JSONL_SYNTAX_ERROR: {FACTS_PATH}: "
                        f"line={line_num}, column={exc.colno}: "
                        f"{exc.msg}"
                    )
                    continue

                if not isinstance(record, dict):
                    errors.append(
                        f"FACT_SCHEMA_ERROR: {FACTS_PATH}: "
                        f"line={line_num}: "
                        f"record must be a JSON object."
                    )
                    continue

                # ==========================================================
                # EXACT schema
                # ==========================================================

                actual_fields = set(record.keys())

                missing_fields = (
                    FACT_REQUIRED_FIELDS - actual_fields
                )

                extra_fields = (
                    actual_fields - FACT_ALLOWED_FIELDS
                )

                if missing_fields:
                    errors.append(
                        f"FACT_SCHEMA_ERROR: {FACTS_PATH}: "
                        f"line={line_num}: "
                        f"missing required fields "
                        f"{sorted(missing_fields)}."
                    )

                if extra_fields:
                    errors.append(
                        f"FACT_SCHEMA_ERROR: {FACTS_PATH}: "
                        f"line={line_num}: "
                        f"unexpected fields "
                        f"{sorted(extra_fields)}."
                    )

                # ==========================================================
                # spec_path
                # ==========================================================

                if "spec_path" not in record:
                    continue

                path_key = record["spec_path"]

                if not validate_non_empty_string(path_key):
                    errors.append(
                        f"FACT_SCHEMA_ERROR: {FACTS_PATH}: "
                        f"line={line_num}: "
                        f"'spec_path' must be a non-empty string."
                    )
                    continue

                # ==========================================================
                # Duplicate detection
                # ==========================================================

                if path_key in p1_seen:
                    errors.append(
                        "DUPLICATE_SPEC_PATH in facts.jsonl: "
                        f"'{path_key}' appears multiple times."
                    )

                p1_seen.add(path_key)
                p1_paths.add(path_key)

                # ==========================================================
                # bytes
                # ==========================================================

                if "bytes" in record:
                    if not validate_non_negative_int(
                        record["bytes"]
                    ):
                        errors.append(
                            f"[{path_key}] FACT_SCHEMA_ERROR: "
                            f"'bytes' must be a non-negative integer, "
                            f"got {record['bytes']!r}."
                        )

                # ==========================================================
                # lines
                # ==========================================================

                if "lines" in record:
                    if not validate_non_negative_int(
                        record["lines"]
                    ):
                        errors.append(
                            f"[{path_key}] FACT_SCHEMA_ERROR: "
                            f"'lines' must be a non-negative integer, "
                            f"got {record['lines']!r}."
                        )

                # ==========================================================
                # is_empty
                # ==========================================================

                if "is_empty" in record:
                    if not validate_bool(
                        record["is_empty"]
                    ):
                        errors.append(
                            f"[{path_key}] FACT_SCHEMA_ERROR: "
                            f"'is_empty' must be boolean, "
                            f"got {record['is_empty']!r}."
                        )

                # ==========================================================
                # sha256
                # ==========================================================

                if "sha256" in record:
                    if not validate_sha256(
                        record["sha256"]
                    ):
                        errors.append(
                            f"[{path_key}] FACT_SCHEMA_ERROR: "
                            f"'sha256' must be exactly 64 lowercase "
                            f"hexadecimal characters, "
                            f"got {record['sha256']!r}."
                        )

                # ==========================================================
                # Internal physical coherence
                #
                # Explicit validation only.
                # No fallback or inference is performed.
                # ==========================================================

                if (
                    validate_non_negative_int(
                        record.get("bytes")
                    )
                    and validate_bool(
                        record.get("is_empty")
                    )
                ):
                    expected_empty = record["bytes"] == 0

                    if record["is_empty"] != expected_empty:
                        errors.append(
                            f"[{path_key}] "
                            f"INVALID_PHYSICAL_RELATION: "
                            f"'is_empty'="
                            f"{record['is_empty']!r} "
                            f"contradicts 'bytes'="
                            f"{record['bytes']!r}."
                        )

                p1_facts[path_key] = record

    except UnicodeDecodeError as exc:
        errors.append(
            f"FACT_ENCODING_ERROR: {FACTS_PATH}: {exc}"
        )

    except OSError as exc:
        errors.append(
            f"FILE_READ_ERROR: {FACTS_PATH}: {exc}"
        )

    return p1_paths, p1_facts


# ============================================================================
# Main Gate
# ============================================================================

def main() -> int:

    errors: List[str] = []

    # ------------------------------------------------------------------------
    # 0. Required input files
    # ------------------------------------------------------------------------

    if not MAP_PATH.is_file():
        errors.append(
            f"REQUIRED_FILE_MISSING: {MAP_PATH}"
        )

    if not FACTS_PATH.is_file():
        errors.append(
            f"REQUIRED_FILE_MISSING: {FACTS_PATH}"
        )

    if errors:
        print_gate_result(errors, 0)
        return 1

    # ------------------------------------------------------------------------
    # 1. Actual .spec files
    # ------------------------------------------------------------------------

    actual_spec_paths = collect_actual_spec_paths()

    # ------------------------------------------------------------------------
    # 2. spec-map.json
    # ------------------------------------------------------------------------

    map_paths, map_by_path = (
        load_and_validate_spec_map(errors)
    )

    # ------------------------------------------------------------------------
    # 3. Phase 1 facts.jsonl
    # ------------------------------------------------------------------------

    p1_paths, p1_facts = (
        load_and_validate_phase1_facts(errors)
    )

    # ------------------------------------------------------------------------
    # 4. Three-way path-set equality
    # ------------------------------------------------------------------------

    if not (
        actual_spec_paths == map_paths
        and map_paths == p1_paths
    ):
        errors.append(
            "SET_MISMATCH: "
            "ACTUAL_SPEC_PATHS != "
            "SPEC_MAP_PATHS != "
            "PHASE1_FACT_PATHS."
        )

        errors.append(
            "  Actual-only: "
            f"{sorted(actual_spec_paths - map_paths)}"
        )

        errors.append(
            "  Map-only: "
            f"{sorted(map_paths - actual_spec_paths)}"
        )

        errors.append(
            "  Phase1-only: "
            f"{sorted(p1_paths - actual_spec_paths)}"
        )

    # ------------------------------------------------------------------------
    # 5. Physical identity verification
    # ------------------------------------------------------------------------

    all_target_paths = (
        actual_spec_paths
        | map_paths
        | p1_paths
    )

    for path_str in sorted(all_target_paths):

        path_obj = Path(path_str)

        # ====================================================================
        # Actual file existence
        # ====================================================================

        if not path_obj.is_file():
            errors.append(
                f"[{path_str}] ACTUAL_FILE_MISSING: "
                f"listed path does not resolve to a regular file."
            )
            continue

        # ====================================================================
        # Actual physical facts
        # ====================================================================

        try:
            actual_bytes = path_obj.stat().st_size
            actual_lines = count_lines(path_obj)
            actual_is_empty = actual_bytes == 0
            actual_sha256 = compute_sha256(path_obj)

        except OSError as exc:
            errors.append(
                f"[{path_str}] ACTUAL_FILE_READ_ERROR: {exc}"
            )
            continue

        # ====================================================================
        # Map facts
        # ====================================================================

        map_item = map_by_path.get(path_str)

        if map_item is None:
            errors.append(
                f"[{path_str}] SPEC_MAP_ENTRY_MISSING."
            )
            continue

        map_physical = map_item.get("physical")

        if not isinstance(map_physical, dict):
            continue

        map_bytes = map_physical.get("bytes")
        map_lines = map_physical.get("lines")
        map_is_empty = map_physical.get("is_empty")

        # ====================================================================
        # Phase 1 facts
        # ====================================================================

        p1_record = p1_facts.get(path_str)

        if p1_record is None:
            errors.append(
                f"[{path_str}] PHASE1_FACT_MISSING."
            )
            continue

        p1_bytes = p1_record.get("bytes")
        p1_lines = p1_record.get("lines")
        p1_is_empty = p1_record.get("is_empty")
        p1_sha256 = p1_record.get("sha256")

        # ====================================================================
        # Bytes
        # ====================================================================

        if (
            validate_non_negative_int(map_bytes)
            and validate_non_negative_int(p1_bytes)
        ):
            if not (
                actual_bytes
                == map_bytes
                == p1_bytes
            ):
                errors.append(
                    f"[{path_str}] MISMATCH_BYTES: "
                    f"actual={actual_bytes}, "
                    f"map={map_bytes}, "
                    f"phase1={p1_bytes}."
                )

        # ====================================================================
        # Lines
        # ====================================================================

        if (
            validate_non_negative_int(map_lines)
            and validate_non_negative_int(p1_lines)
        ):
            if not (
                actual_lines
                == map_lines
                == p1_lines
            ):
                errors.append(
                    f"[{path_str}] MISMATCH_LINES: "
                    f"actual={actual_lines}, "
                    f"map={map_lines}, "
                    f"phase1={p1_lines}."
                )

        # ====================================================================
        # is_empty
        #
        # IMPORTANT:
        # No inference or fallback is performed.
        #
        # The field must exist and be explicitly boolean in both
        # sources. Its value must agree with:
        #
        #     actual_bytes == 0
        #
        # ====================================================================

        if (
            validate_bool(map_is_empty)
            and validate_bool(p1_is_empty)
        ):
            if not (
                actual_is_empty
                == map_is_empty
                == p1_is_empty
            ):
                errors.append(
                    f"[{path_str}] MISMATCH_IS_EMPTY: "
                    f"actual={actual_is_empty}, "
                    f"map={map_is_empty}, "
                    f"phase1={p1_is_empty}."
                )

        # ====================================================================
        # SHA-256
        # ====================================================================

        if validate_sha256(p1_sha256):

            if actual_sha256 != p1_sha256:
                errors.append(
                    f"[{path_str}] MISMATCH_SHA256: "
                    f"actual='{actual_sha256}', "
                    f"phase1='{p1_sha256}'."
                )

    # ------------------------------------------------------------------------
    # 6. Gate result
    # ------------------------------------------------------------------------

    print_gate_result(
        errors,
        len(all_target_paths),
    )

    return 1 if errors else 0

# ============================================================================
# Output
# ============================================================================

def print_gate_result(
    errors: List[str],
    target_count: int,
) -> None:

    print("=" * 72)
    print(" GATE-1: Physical Provenance Integrity Check")
    print("=" * 72)

    if errors:

        print(
            f"FAILED: Found {len(errors)} integrity violation(s):"
        )
        print()

        for error in errors:
            print(f"  [ERROR] {error}")

        print()
        print(
            "GATE-1 RESULT: FAIL "
            "(Phase 2 is BLOCKED)"
        )

    else:

        print(
            f"PASS: Verified {target_count} spec file(s)."
        )
        print()
        print(
            "  - Path Sets:"
            " ACTUAL == MAP == PHASE1"
        )
        print(
            "  - Duplicate spec_path:"
            " NONE"
        )
        print(
            "  - Phase 1 Schema:"
            " EXACT / STRICT"
        )
        print(
            "  - spec-map Schema:"
            " STRICT"
        )
        print(
            "  - Bytes:"
            " 100% CONSISTENT"
        )
        print(
            "  - Lines:"
            " 100% CONSISTENT"
        )
        print(
            "  - is_empty:"
            " EXPLICIT / COHERENT / NON-INFERRED / CONSISTENT"
        )
        print(
            "  - SHA-256:"
            " VALID FORMAT / 100% MATCH"
        )

        print()
        print(
            "GATE-1 RESULT: PASS "
            "(Phase 2 is CLEARED)"
        )

# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    sys.exit(main())