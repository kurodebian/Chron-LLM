#!/usr/bin/env python3
# tools/run_a1a_corpus.py

import argparse
import json
import os
import sys
from pathlib import Path

# Allow direct execution:
#   python tools/run_a1a_corpus.py
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.a1_segment import (
    detect_boundaries_llm,
    load_source,
    normalize_boundaries,
    validate_raw_observation,
    write_units,
)
from tools.validate_a1_artifact import validate_units_json


DEFAULT_MANIFEST = Path("corpus_manifest.json")
EXPECTED_MANIFEST_VERSION = "A-0d.1"
EXPECTED_STATUS = "FROZEN"
EXPECTED_COUNT = 49


def load_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    if not isinstance(manifest, dict):
        raise ValueError("INVALID_MANIFEST: root must be an object")

    if manifest.get("manifest_version") != EXPECTED_MANIFEST_VERSION:
        raise ValueError(
            "INVALID_MANIFEST: "
            f"manifest_version must be {EXPECTED_MANIFEST_VERSION!r}"
        )

    if manifest.get("status") != EXPECTED_STATUS:
        raise ValueError("INVALID_MANIFEST: status must be FROZEN")

    observation_corpus = manifest.get("observation_corpus")
    if not isinstance(observation_corpus, dict):
        raise ValueError("INVALID_MANIFEST: observation_corpus missing")

    if observation_corpus.get("canonical_spec_input_forbidden") is not True:
        raise ValueError(
            "INVALID_MANIFEST: canonical_spec_input_forbidden must be true"
        )

    files = manifest.get("files")
    if not isinstance(files, list):
        raise ValueError("INVALID_MANIFEST: files must be a list")

    if len(files) != EXPECTED_COUNT:
        raise ValueError(
            "INVALID_MANIFEST: "
            f"expected {EXPECTED_COUNT} observation files, got {len(files)}"
        )

    return manifest


def resolve_source(repository_root: Path, document_path: str) -> Path:
    relative = Path(document_path)

    if relative.is_absolute():
        raise ValueError(
            f"INVALID_MANIFEST_PATH: absolute path is forbidden: {document_path}"
        )

    root = repository_root.resolve()
    source = (root / relative).resolve()

    try:
        source.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"INVALID_MANIFEST_PATH: path escapes repository_root: {document_path}"
        ) from exc

    if not source.is_file():
        raise FileNotFoundError(
            f"SOURCE_NOT_FOUND: {document_path} -> {source}"
        )

    return source


def run_document(repository_root: Path, document_path: str) -> Path:
    source_path = resolve_source(repository_root, document_path)
    lines = load_source(str(source_path))

    observation = detect_boundaries_llm(
        document_path=document_path,
        lines=lines,
    )

    validate_raw_observation(observation, lines)

    units = normalize_boundaries(
        observation,
        lines,
    )

    output_path = write_units(
        document_path,
        units,
    )

    # validate_units_json() resolves document_path from cwd.
    # Keep artifact document_path logical and validate from repository root.
    absolute_output = Path(output_path).resolve()
    original_cwd = Path.cwd()

    try:
        os.chdir(repository_root)
        validate_units_json(str(absolute_output))
    finally:
        os.chdir(original_cwd)

    return absolute_output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run frozen A-1a boundary observation over the manifest corpus."
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N manifest entries.",
    )

    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Zero-based manifest index at which to start.",
    )

    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be >= 1")

    if args.start < 0:
        parser.error("--start must be >= 0")

    manifest_path = args.manifest.resolve()
    manifest = load_manifest(manifest_path)

    repository_root = Path(
        manifest["repository_root"]
    ).resolve()

    if not repository_root.is_dir():
        raise FileNotFoundError(
            f"REPOSITORY_ROOT_NOT_FOUND: {repository_root}"
        )

    entries = manifest["files"]

    selected = entries[args.start:]

    if args.limit is not None:
        selected = selected[:args.limit]

    if not selected:
        raise ValueError("NO_INPUT: selected manifest range is empty")

    print(
        f"A-1a corpus run: {len(selected)} document(s) "
        f"from manifest {manifest_path}"
    )

    for offset, entry in enumerate(
        selected,
        start=args.start + 1,
    ):
        if not isinstance(entry, dict):
            raise ValueError(
                f"INVALID_MANIFEST_ENTRY: index={offset}"
            )

        document_path = entry.get("path")

        if not isinstance(document_path, str) or not document_path:
            raise ValueError(
                f"INVALID_MANIFEST_ENTRY: missing path at index={offset}"
            )

        print(f"[{offset}/{len(entries)}] {document_path}")

        output_path = run_document(
            repository_root,
            document_path,
        )

        print(f"  PASS: {output_path}")

    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
