#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


EXPECTED_COUNT = 49

EXPECTED_SOURCE_ROLES = {
    "FORMAL_CONSTITUTION",
    "FORMAL_SPECIFICATION",
    "ARCHITECTURAL_SPECIFICATION",
    "EXPERIMENTAL_SPECIFICATION",
    "DESIGN_DOCUMENT",
}

EXPECTED_LEGACY = {
    "chron-llm-causal/CAUSAL_SPECIFICATION_MATRIX.md",
    "chron-llm-causal/docs/specs/component-001.md",
    "chron-llm-causal/tests/fixtures/spec_component_001.md",
}

FORBIDDEN_SEMANTIC_KEYS = {
    "semantic_kind",
    "node_type",
    "causal_role",
    "normative_role",
    "lifecycle_kind",
    "state_role",
    "transition_role",
    "event_role",
    "relation_kind",
    "candidate_roles",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def line_count(path: Path) -> int:
    # Equivalent to counting newline characters, i.e. wc -l semantics.
    with path.open("rb") as f:
        return f.read().count(b"\n")


def input_set_digest(files: list[dict]) -> str:
    records = []
    for entry in sorted(files, key=lambda x: x["path"]):
        records.append(f'{entry["path"]}\t{entry["sha256"]}')

    payload = ("\n".join(records) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def find_forbidden_keys(obj, path="$"):
    found = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in FORBIDDEN_SEMANTIC_KEYS:
                found.append(f"{path}.{key}")
            found.extend(find_forbidden_keys(value, f"{path}.{key}"))

    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            found.extend(find_forbidden_keys(value, f"{path}[{i}]"))

    return found


def check_path(path_str: str, repository_root: Path) -> Path:
    p = Path(path_str)

    if p.is_absolute():
        fail(f"repository-relative violation: absolute path: {path_str}")

    if path_str.startswith("./"):
        fail(f"non-canonical relative path: {path_str}")

    if "\\" in path_str:
        fail(f"non-canonical path separator: {path_str}")

    normalized = Path(path_str)
    if ".." in normalized.parts:
        fail(f"path traversal is forbidden: {path_str}")

    # Require canonical POSIX-style relative spelling.
    if normalized.as_posix() != path_str:
        fail(f"non-canonical repository-relative path: {path_str}")

    resolved = (repository_root / normalized).resolve()

    try:
        resolved.relative_to(repository_root.resolve())
    except ValueError:
        fail(f"path escapes repository root: {path_str}")

    return resolved


def check_manifest(manifest_path: Path, require_digest: bool) -> int:
    print("A-0d.1 FREEZE VALIDATOR")
    print("=" * 72)

    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    errors: list[str] = []

    def check(label: str, condition: bool, detail: str = ""):
        status = "PASS" if condition else "FAIL"
        suffix = f" — {detail}" if detail else ""
        print(f"{label:<28} {status}{suffix}")
        if not condition:
            errors.append(f"{label}: {detail or 'condition failed'}")

    # ------------------------------------------------------------------
    # STRUCTURE
    # ------------------------------------------------------------------

    check(
        "manifest_version",
        manifest.get("manifest_version") == "A-0d.1",
        f"got {manifest.get('manifest_version')!r}",
    )

    status = manifest.get("status")
    check(
        "status",
        status in {"CANDIDATE", "FROZEN"},
        f"got {status!r}",
    )

    corpus = manifest.get("observation_corpus", {})
    files = manifest.get("files", [])
    excluded = manifest.get("excluded", [])

    check(
        "observation_count",
        corpus.get("count") == EXPECTED_COUNT,
        f"got {corpus.get('count')!r}",
    )

    check(
        "files_array_count",
        len(files) == EXPECTED_COUNT,
        f"got {len(files)}",
    )

    check(
        "canonical_spec_input_forbidden",
        corpus.get("canonical_spec_input_forbidden") is True,
        f"got {corpus.get('canonical_spec_input_forbidden')!r}",
    )

    # ------------------------------------------------------------------
    # REPOSITORY ROOT
    # ------------------------------------------------------------------

    repository_root_raw = manifest.get("repository_root")

    if not repository_root_raw:
        errors.append("repository_root: missing")
        print(f"{'repository_root':<28} FAIL — missing")
        repository_root = None
    else:
        repository_root = Path(repository_root_raw)

        check(
            "repository_root",
            repository_root.is_absolute() and repository_root.exists(),
            f"{repository_root}",
        )

    # ------------------------------------------------------------------
    # PATH UNIQUENESS
    # ------------------------------------------------------------------

    paths = [entry.get("path") for entry in files]
    duplicate_paths = sorted(
        {p for p in paths if paths.count(p) > 1}
    )

    check(
        "path_uniqueness",
        len(paths) == len(set(paths)),
        f"duplicates={duplicate_paths}",
    )

    # ------------------------------------------------------------------
    # FILE-BY-FILE VALIDATION
    # ------------------------------------------------------------------

    existence_pass = 0
    size_pass = 0
    line_pass = 0
    sha_pass = 0
    relative_pass = 0
    role_pass = 0
    eligible_pass = 0

    for i, entry in enumerate(files, start=1):
        path_str = entry.get("path")

        if not isinstance(path_str, str):
            errors.append(f"file[{i}]: path missing/non-string")
            print(f"file[{i:02d}]                  FAIL — invalid path")
            continue

        try:
            if repository_root is None:
                raise AssertionError("repository_root unavailable")

            actual_path = check_path(path_str, repository_root)
            relative_pass += 1
        except AssertionError as e:
            errors.append(f"{path_str}: {e}")
            print(f"file[{i:02d}] relative          FAIL — {e}")
            continue

        if actual_path.exists() and actual_path.is_file():
            existence_pass += 1
        else:
            errors.append(f"{path_str}: file does not exist")
            print(f"file[{i:02d}] existence         FAIL — missing")
            continue

        expected_size = entry.get("size_bytes")
        actual_size = actual_path.stat().st_size

        if actual_size == expected_size:
            size_pass += 1
        else:
            errors.append(
                f"{path_str}: size_bytes "
                f"manifest={expected_size} actual={actual_size}"
            )

        expected_lines = entry.get("line_count")
        actual_lines = line_count(actual_path)

        if actual_lines == expected_lines:
            line_pass += 1
        else:
            errors.append(
                f"{path_str}: line_count "
                f"manifest={expected_lines} actual={actual_lines}"
            )

        expected_sha = entry.get("sha256")
        actual_sha = sha256_file(actual_path)

        if actual_sha == expected_sha:
            sha_pass += 1
        else:
            errors.append(
                f"{path_str}: sha256 "
                f"manifest={expected_sha} actual={actual_sha}"
            )

        role = entry.get("source_role")

        if role in EXPECTED_SOURCE_ROLES:
            role_pass += 1
        else:
            errors.append(
                f"{path_str}: invalid source_role={role!r}"
            )

        if entry.get("observation_eligible") is True:
            eligible_pass += 1
        else:
            errors.append(
                f"{path_str}: observation_eligible is not true"
            )

    check(
        "repository_relative",
        relative_pass == len(files),
        f"{relative_pass}/{len(files)}",
    )

    check(
        "file_existence",
        existence_pass == len(files),
        f"{existence_pass}/{len(files)}",
    )

    check(
        "size_bytes",
        size_pass == len(files),
        f"{size_pass}/{len(files)}",
    )

    check(
        "line_count",
        line_pass == len(files),
        f"{line_pass}/{len(files)}",
    )

    check(
        "sha256",
        sha_pass == len(files),
        f"{sha_pass}/{len(files)}",
    )

    check(
        "source_role_vocabulary",
        role_pass == len(files),
        f"{role_pass}/{len(files)}",
    )

    check(
        "observation_eligible",
        eligible_pass == len(files),
        f"{eligible_pass}/{len(files)}",
    )

    # ------------------------------------------------------------------
    # .spec EXCLUSION
    # ------------------------------------------------------------------

    spec_entries = [
        entry["path"]
        for entry in files
        if entry.get("path", "").endswith(".spec")
    ]

    check(
        ".spec_exclusion",
        len(spec_entries) == 0,
        f"found={spec_entries}",
    )

    # ------------------------------------------------------------------
    # LEGACY EXCLUSION
    # ------------------------------------------------------------------

    excluded_paths = [entry.get("path") for entry in excluded]

    check(
        "excluded_count",
        len(excluded) == 3,
        f"got {len(excluded)}",
    )

    check(
        "legacy_exclusion_paths",
        set(excluded_paths) == EXPECTED_LEGACY,
        f"got={sorted(excluded_paths)}",
    )

    legacy_reasons_ok = all(
        entry.get("reason") == "LEGACY_CAUSAL_ARTIFACT"
        for entry in excluded
    )

    check(
        "legacy_exclusion_reasons",
        legacy_reasons_ok,
    )

    overlap = sorted(set(paths) & EXPECTED_LEGACY)

    check(
        "legacy_not_observation_input",
        len(overlap) == 0,
        f"overlap={overlap}",
    )

    # ------------------------------------------------------------------
    # SEMANTIC TAXONOMY ABSENCE
    # ------------------------------------------------------------------

    forbidden_keys = find_forbidden_keys(manifest)

    check(
        "semantic_taxonomy_absent",
        len(forbidden_keys) == 0,
        f"found={forbidden_keys}",
    )

    # ------------------------------------------------------------------
    # INPUT SET DIGEST
    # ------------------------------------------------------------------

    computed_digest = None

    if (
        len(files) == EXPECTED_COUNT
        and all(
            isinstance(e.get("path"), str)
            and isinstance(e.get("sha256"), str)
            for e in files
        )
    ):
        computed_digest = input_set_digest(files)

        print()
        print(f"computed_input_set_digest  {computed_digest}")

        freeze = manifest.get("freeze", {})
        recorded_digest = freeze.get("input_set_digest")

        if recorded_digest is None:
            print(
                "recorded_input_set_digest NOT PRESENT "
                "(acceptable before Step 2)"
            )
            if require_digest:
                errors.append(
                    "input_set_digest: required but not present"
                )
                print("input_set_digest          FAIL — missing")
            else:
                print("input_set_digest          DEFERRED — Step 2")
        else:
            check(
                "input_set_digest",
                recorded_digest == computed_digest,
                f"recorded={recorded_digest}",
            )

        check(
            "hash_algorithm",
            freeze.get("hash_algorithm") == "sha256",
            f"got {freeze.get('hash_algorithm')!r}",
        )

    # ------------------------------------------------------------------
    # FINAL RESULT
    # ------------------------------------------------------------------

    print()
    print("-" * 72)

    if errors:
        print("RESULT                     FAIL")
        print()
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("RESULT                     PASS")
    print()

    if status == "FROZEN":
        print(
            "WARNING: manifest is already marked FROZEN. "
            "This validator does not modify status."
        )
    else:
        print(
            "PRE-FREEZE VALIDATION PASS. "
            "Manifest remains CANDIDATE."
        )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="A-0d.1 observation corpus Freeze Validator"
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        default="corpus_manifest.json",
    )
    parser.add_argument(
        "--require-digest",
        action="store_true",
        help="Require recorded input_set_digest to match computed digest",
    )

    args = parser.parse_args()

    return check_manifest(
        Path(args.manifest),
        require_digest=args.require_digest,
    )


if __name__ == "__main__":
    sys.exit(main())
