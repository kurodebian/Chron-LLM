"""
t1_a_test_runner.py — T1-A Differential Test Runner (Extended Boundary Matrix)
"""

from step1_reference_parser import parse_reference
from step2_production_parser import parse_production
from t1_differential_adapter import DifferentialAdapter


EXTENDED_TEST_MATRIX = [
    # 1. Valid Claims (All 3 types)
    ("unit: App.Core", "Unit claim valid"),
    ("requires: DB-V2", "Requires claim valid"),
    ("depends_on: Service_A", "DependsOn claim valid"),
    ("  requires  :   A.B-C_1  ", "Whitespace variations"),

    # 2. Invalid ID Boundaries
    ("unit: .A", "Leading dot"),
    ("requires: A.", "Trailing dot"),
    ("depends_on: A..B", "Consecutive dots"),
    ("unit: A.-B", "Dot-hyphen sequence"),

    # 3. Non-Candidate & Case Sensitivity
    ("UNIT: App", "Uppercase keyword -> NOT_A_CANDIDATE"),
    ("Requires: DB", "Capitalized keyword -> NOT_A_CANDIDATE"),
    ("unknown: X", "Unknown keyword -> NOT_A_CANDIDATE"),

    # 4. Invalid Syntax / Malformed Prefix
    ("unit:", "Missing target -> INVALID_GRAMMAR"),
    ("requires: A B", "Space inside ID -> INVALID_GRAMMAR"),

    # 5. Comment & Blank Lines (Valid - No Newline)
    ("# test comment", "Comment line"),
    ("   \t  ", "Blank line"),

    # 6. PhysicalLine Boundary Violations (Newlines / Terminators)
    ("unit: App\n", "Claim with trailing LF -> INVALID_GRAMMAR"),
    ("unit: App\r\n", "Claim with trailing CRLF -> INVALID_GRAMMAR"),
    ("# comment\n", "Comment with trailing LF -> INVALID_GRAMMAR"),
    ("   \n", "Blank with trailing LF -> INVALID_GRAMMAR"),
    ("\t\n", "Tab-blank with trailing LF -> INVALID_GRAMMAR"),
    ("\n", "Pure LF line -> INVALID_GRAMMAR"),
    ("\r\n", "Pure CRLF line -> INVALID_GRAMMAR"),
]


def run_t1_a_audit() -> bool:
    print("=" * 75)
    print("T1-A DIFFERENTIAL TEST EXECUTION (Re-run with Boundary Guard)")
    print("=" * 75)

    all_passed = True
    pass_count = 0

    for line, description in EXTENDED_TEST_MATRIX:
        ref_raw = parse_reference(line)
        prod_raw = parse_production(line)

        ref_out = DifferentialAdapter.adapt_reference(ref_raw)
        prod_out = DifferentialAdapter.adapt_production(prod_raw)

        match = (ref_out == prod_out)
        if match:
            pass_count += 1
        else:
            all_passed = False

        status_flag = "PASS" if match else "FAIL"
        print(f"[{status_flag}] Input: {repr(line)} ({description})")
        if not match:
            print(f"   ├─ Reference:  {ref_out}")
            print(f"   └─ Production: {prod_out}")

    print("-" * 75)
    print(f"Summary: {pass_count}/{len(EXTENDED_TEST_MATRIX)} Cases Matched.")
    print(f"T1-A Differential Status: {'PASSED (Zero Discrepancy)' if all_passed else 'FAILED'}")
    print("=" * 75)
    return all_passed


if __name__ == "__main__":
    run_t1_a_audit()