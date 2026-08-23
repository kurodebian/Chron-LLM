"""
t3_priority_domain_test_runner.py — T3: Trace-based Short-Circuit & Priority Audit
"""

from step0_ssot import ParseStatus
from step2_production_parser import parse_production


def run_t3_strict_trace_audit() -> bool:
    print("=" * 75)
    print("T3 AUDIT: STRICT EVALUATION TRACE & SHORT-CIRCUIT ASSERTIONS")
    print("=" * 75)

    # (current_unit, line, expected_status, expected_trace, description)
    # expected_trace MUST be a tuple in alignment with T4 Immutable Trace Contract
    test_matrix = [
        # 1. Valid Pipeline (P1 -> P2 -> P3 -> P4 -> P5)
        ("App.Core", "requires: DB", ParseStatus.VALID_CLAIM, ("P1", "P2", "P3", "P4", "P5"),
         "Valid claim executes full P1..P5 pipeline"),

        # 2. P3 Short-Circuit Assertions (P1 -> P2 -> P3 -> STOP; P4, P5 MUST NOT execute)
        (123, "requires: DB", ParseStatus.INVALID_CONTEXT, ("P1", "P2", "P3"),
         "Integer context -> Stopped at P3 (P4/P5 short-circuited)"),
        (object(), "requires: DB", ParseStatus.INVALID_CONTEXT, ("P1", "P2", "P3"),
         "Object context -> Stopped at P3"),
        ("", "requires: DB", ParseStatus.INVALID_CONTEXT, ("P1", "P2", "P3"),
         "Empty string context -> Stopped at P3"),
        ("@EVIL", "requires: DB", ParseStatus.INVALID_CONTEXT, ("P1", "P2", "P3"),
         "Invalid char context -> Stopped at P3"),
        (".", "requires: DB", ParseStatus.INVALID_CONTEXT, ("P1", "P2", "P3"),
         "Dot context -> Stopped at P3"),
        ("-", "requires: DB", ParseStatus.INVALID_CONTEXT, ("P1", "P2", "P3"),
         "Hyphen context -> Stopped at P3"),

        # 3. Priority Assertions: P1/P2 > P3
        ("@EVIL", "# Comment", ParseStatus.COMMENT_LINE, ("P1",),
         "Comment stopped at P1 (P2/P3 bypassed)"),
        ("@EVIL", "   \t", ParseStatus.BLANK_LINE, ("P1",),
         "Blank stopped at P1 (P2/P3 bypassed)"),
        ("@EVIL", "unknown: X", ParseStatus.NOT_A_CANDIDATE, ("P1", "P2"),
         "Non-candidate stopped at P2 (P3 bypassed)"),

        # 4. P4 Syntax Failure Assertion (P1 -> P2 -> P3 -> P4 -> STOP)
        ("App.Core", "requires:", ParseStatus.INVALID_GRAMMAR, ("P1", "P2", "P3", "P4"),
         "Malformed target stopped at P4 (P5 short-circuited)"),
    ]

    all_passed = True
    for idx, (unit, line, exp_status, exp_trace, desc) in enumerate(test_matrix, 1):
        res = parse_production(line, unit)

        status_passed = (res.status == exp_status)
        trace_passed = (res.trace == exp_trace)
        p4_not_executed = ("P4" not in res.trace) if exp_status == ParseStatus.INVALID_CONTEXT else True

        passed = status_passed and trace_passed and p4_not_executed
        if not passed:
            all_passed = False

        flag = "PASS" if passed else "FAIL"
        print(f"[{flag}] Case {idx:02d}: {desc}")
        if not passed:
            print(f"   ├─ Exp Status: {exp_status:<20} | Act Status: {res.status}")
            print(f"   └─ Exp Trace:  {str(exp_trace):<30} | Act Trace:  {res.trace}")

    print("-" * 75)
    print(f"T3 Priority & Short-Circuit Audit: {'PASSED' if all_passed else 'FAILED'}")
    print("=" * 75)
    return all_passed


if __name__ == "__main__":
    run_t3_strict_trace_audit()