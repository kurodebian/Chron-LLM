#!/usr/bin/env python3
"""
tools/spec_linter.py - Static Invariant & Type Safety Linter for Chron-LLM IR Specifications

Verifies:
1. Core Type Registry Alignment (Type aliases & undefined types)
2. Exclusion Matrix Violations (Strict isolation boundary with negation recognition)
3. Mandatory Invariant Presence (Determinism, Authority, Immutability)
4. Pipeline Flow Continuity
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set


class Color:
    HEADER = "\033[95m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


class ChronSpecLinter:
    def __init__(self, core_spec_path: Path, phase_specs_dir: Path):
        self.core_spec_path = core_spec_path
        self.phase_specs_dir = phase_specs_dir

        self.declared_types: Set[str] = set()
        self.type_aliases: Dict[str, str] = {}
        self.exclusions_matrix: Dict[str, Set[str]] = {}
        self.phase_specs: Dict[str, dict] = {}
        self.violations: List[str] = []
        self.warnings: List[str] = []

    def parse_core_types(self):
        """Parse core/types.spec to build master types, aliases, and exclusion rules."""
        if not self.core_spec_path.exists():
            self.violations.append(f"Core spec not found at {self.core_spec_path}")
            return

        content = self.core_spec_path.read_text()

        # Extract TYPES & Aliases
        types_match = re.search(
            r"TYPES:\s*\n(.*?)(?=\n\n|\n#[A-Z]|\n[A-Z]+:)", content, re.DOTALL
        )
        if types_match:
            raw_types = types_match.group(1)
            for line in raw_types.split("\n"):
                line = re.sub(r"//.*", "", line).strip()
                if not line:
                    continue
                if "=" in line:
                    alias, target = [t.strip() for t in line.split("=", 1)]
                    self.type_aliases[alias] = target
                    self.declared_types.add(alias)
                else:
                    type_name = line.split()[0]
                    self.declared_types.add(type_name)

        # Extract EXCLUSIONS Matrix
        excl_match = re.search(
            r"EXCLUSIONS:\s*\n(.*?)(?=\n\n|\n#[A-Z]|\Z)", content, re.DOTALL
        )
        if excl_match:
            for line in excl_match.group(1).split("\n"):
                line = line.strip()
                if line and ":" in line:
                    phase_key, excluded_list = line.split(":", 1)
                    phase_key = phase_key.strip().lower()
                    terms = [
                        t.strip()
                        for t in re.sub(r"[\[\]]", "", excluded_list).split(",")
                    ]
                    self.exclusions_matrix[phase_key] = set(filter(None, terms))

    def parse_phase_spec(self, filepath: Path) -> dict:
        """Parse an individual phase charter file."""
        content = filepath.read_text()
        phase_id = filepath.stem.replace("-charter", "").lower()

        # Extract Types from STATE (Variable : Type) or TYPES (Type1, Type2)
        extracted_types = set()
        state_match = re.search(r"(?:STATE|TYPES):\s*(.*)", content)
        if state_match:
            raw_state = state_match.group(1)
            # Find Types after colons (e.g., "H : History" -> "History")
            types_after_colon = re.findall(r":\s*([A-Z][a-zA-Z0-9_]*)", raw_state)
            extracted_types.update(types_after_colon)

            # Find comma-separated list of types if no colons present
            if not types_after_colon:
                tokens = re.findall(r"\b[A-Z][a-zA-Z0-9_]*\b", raw_state)
                extracted_types.update(tokens)

        # Extract EXCLUDE
        excludes = set()
        excl_match = re.search(r"EXCLUDE:\s*(.*)", content)
        if excl_match:
            terms = [t.strip() for t in excl_match.group(1).split(",")]
            excludes.update(filter(None, terms))

        # Extract Invariants (allowing optional whitespace before colon)
        invs = re.findall(r"INV[-\w]*\s*:\s*(.*)", content)

        return {
            "phase_id": phase_id,
            "filename": filepath.name,
            "content": content,
            "types": extracted_types,
            "excludes": excludes,
            "invariants": invs,
        }

    def run_checks(self):
        """Execute static analysis on IR specifications."""
        self.parse_core_types()

        for spec_file in sorted(self.phase_specs_dir.glob("phase-*-charter.spec")):
            spec_data = self.parse_phase_spec(spec_file)
            self.phase_specs[spec_data["phase_id"]] = spec_data

        if not self.phase_specs:
            self.violations.append(
                f"No phase charter files found in {self.phase_specs_dir}"
            )
            return

        # ---------------------------------------------------------------------
        # CHECK 1: Type Safety & Registry Consistency
        # ---------------------------------------------------------------------
        for phase_id, spec in self.phase_specs.items():
            for type_symbol in spec["types"]:
                if type_symbol in {"StructuralGraph"}:  # Recognized structural alias
                    continue
                if (
                    type_symbol not in self.declared_types
                    and type_symbol not in self.type_aliases
                ):
                    self.warnings.append(
                        f"[{spec['filename']}] Type '{type_symbol}' is not declared in core/types.spec"
                    )

        # ---------------------------------------------------------------------
        # CHECK 2: Exclusion Isolation Boundary (Recognizing Negation Invariants)
        # ---------------------------------------------------------------------
        for phase_id, spec in self.phase_specs.items():
            excludes_to_check = set(spec["excludes"])
            core_key = phase_id.replace("-", "")
            if core_key in self.exclusions_matrix:
                excludes_to_check.update(self.exclusions_matrix[core_key])

            for prohibited_term in excludes_to_check:
                pattern = r"\b" + re.escape(prohibited_term) + r"\b"
                lines = spec["content"].split("\n")
                for line_num, line in enumerate(lines, 1):
                    # Ignore EXCLUDE definition line itself
                    if "EXCLUDE" in line:
                        continue
                    # Ignore negation expressions (e.g., "!in", "NOT IN")
                    if re.search(pattern, line):
                        if "!in" in line or "NOT IN" in line or "not in" in line:
                            continue  # Valid assertion of non-presence
                        self.violations.append(
                            f"[{spec['filename']}:{line_num}] EXCLUSION VIOLATION: "
                            f"Prohibited term '{prohibited_term}' referenced in logic: '{line.strip()}'"
                        )

        # ---------------------------------------------------------------------
        # CHECK 3: Authority Invariant Guarantees
        # ---------------------------------------------------------------------
        if "phase-a" in self.phase_specs:
            pa = self.phase_specs["phase-a"]
            if not any("authoritative" in inv for inv in pa["invariants"]):
                self.violations.append(
                    f"[{pa['filename']}] Missing Authority Invariant (H.authoritative_causal_record)"
                )

        for pid in ["phase-c", "phase-d"]:
            if pid in self.phase_specs:
                ps = self.phase_specs[pid]
                if not any("non_authoritative" in inv for inv in ps["invariants"]):
                    self.violations.append(
                        f"[{ps['filename']}] Missing Invariant: Must declare 'non_authoritative'"
                    )

        # ---------------------------------------------------------------------
        # CHECK 4: Determinism Guarantee Chain
        # ---------------------------------------------------------------------
        for pid in ["phase-b", "phase-c", "phase-d", "phase-e"]:
            if pid in self.phase_specs:
                ps = self.phase_specs[pid]
                if not any("deterministic" in inv.lower() for inv in ps["invariants"]):
                    self.violations.append(
                        f"[{ps['filename']}] Missing Determinism Guarantee in INVs"
                    )

    def print_report(self):
        print(
            f"\n{Color.HEADER}{Color.BOLD}===================================================={Color.ENDC}"
        )
        print(
            f"{Color.HEADER}{Color.BOLD} Chron-LLM IR Spec Linter Verification Report {Color.ENDC}"
        )
        print(
            f"{Color.HEADER}{Color.BOLD}===================================================={Color.ENDC}\n"
        )

        print(f"Loaded Core Types: {len(self.declared_types)} definitions")
        print(f"Loaded Phase Charters: {len(self.phase_specs)} files\n")

        if self.warnings:
            print(
                f"{Color.WARNING}{Color.BOLD}[ WARNINGS / TYPE MISMATCHES ]{Color.ENDC}"
            )
            for w in self.warnings:
                print(f"  {Color.WARNING}⚠ {w}{Color.ENDC}")
            print()

        if self.violations:
            print(
                f"{Color.FAIL}{Color.BOLD}[ CRITICAL VIOLATIONS FOUND: {len(self.violations)} ]{Color.ENDC}"
            )
            for v in self.violations:
                print(f"  {Color.FAIL}✘ {v}{Color.ENDC}")
            print(
                f"\n{Color.FAIL}{Color.BOLD}FAILED: Specifications contain invariant or type safety violations.{Color.ENDC}\n"
            )
            sys.exit(1)
        else:
            print(
                f"{Color.OKGREEN}{Color.BOLD}✔ SUCCESS: All Phase specifications (A-F) pass structural invariant & exclusion checks!{Color.ENDC}\n"
            )


if __name__ == "__main__":
    root_dir = Path(".")
    core_spec = root_dir / "core" / "types.spec"
    phase_dir = root_dir / "docs" / "ir"

    linter = ChronSpecLinter(core_spec, phase_dir)
    linter.run_checks()
    linter.print_report()
