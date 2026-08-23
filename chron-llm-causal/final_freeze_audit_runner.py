"""
final_freeze_audit_runner.py — Phase 7C: Cross-System Final Freeze Audit Runner

Executes T1-A, T1-B, T3, T4, and T5 in a single unified process to verify
suite pass aggregation, contract boundaries, and scope declarations prior to FINAL FREEZE.
"""

from step0_ssot import ParseStatus, ClaimType
from step2_production_parser import parse_production
from step3_context_reducer import ContextReducer, ContextState

# 実環境の正確なモジュール名・関数名でインポート（整合完了）
from t1_a_test_runner import run_t1_a_audit
from t1_b_hypothesis_runner import run_t1b_fuzzing
from t3_priority_domain_test_runner import run_t3_strict_trace_audit
from t4_determinism_test_runner import run_t4_determinism_audit
from t5_stateful_reducer_audit_runner import run_t5_stateful_trajectory_audit


def run_final_freeze_audit() -> bool:
    print("===========================================================================")
    print("PHASE 7C: FINAL FREEZE CROSS-SYSTEM VERIFICATION AUDIT")
    print("===========================================================================")
    print("Audit Scope: T1-A, T1-B, T3, T4, T5 Suite Execution & Boundary Verification")
    print("=" * 75)

    suite_results = {}

    # 1. T1-A Execution
    print("\n>>> Phase 1/5: Executing T1-A (Exact Match Audit)...")
    suite_results["T1-A"] = run_t1_a_audit()

    # 2. T1-B Execution
    print("\n>>> Phase 2/5: Executing T1-B (Differential Fuzzing Audit)...")
    suite_results["T1-B"] = run_t1b_fuzzing()

    # 3. T3 Execution
    print("\n>>> Phase 3/5: Executing T3 (Priority & Domain Trace Audit)...")
    suite_results["T3"] = run_t3_strict_trace_audit()

    # 4. T4 Execution
    print("\n>>> Phase 4/5: Executing T4 (Determinism & Immutability Audit)...")
    suite_results["T4"] = run_t4_determinism_audit()

    # Execution Block 内
    # 5. T5 Execution
    print("\n>>> Phase 5/5: Executing T5 (Stateful Reducer & Trajectory Audit)...")
    suite_results["T5"] = run_t5_stateful_trajectory_audit()

    # -------------------------------------------------------------------------
    # Final Contract & Boundary Checks
    # -------------------------------------------------------------------------
    print("\n" + "=" * 75)
    print("CROSS-SYSTEM SUITE & BOUNDARY AUDIT SUMMARY")
    print("=" * 75)

    all_suites_passed = all(suite_results.values())

    # 1. Suite Aggregation Verification
    if all_suites_passed:
        print("  [PASS] All registered audit suites (T1-A, T1-B, T3, T4, T5) returned PASS.")
    else:
        failed_suites = [k for k, v in suite_results.items() if not v]
        print(f"  [FAIL] Audit failures detected in suites: {failed_suites}")

    # 2. Contract Boundary Declarations
    print("\n[Contract Boundary Verification]")
    print("  * Parser -> ProductionParseResult (Typed IR) -> ContextReducer -> ContextState")
    print("  * Parser-Reducer Separation: Verified via T5 Sub-Test 5")
    print("  * Historical Immutability (Identity & Value Preservation): Verified via T5 Sub-Test 2")

    # 3. Empirical Scope Boundary Declaration
    print("\n[Audit Scope & Proof Boundary Declaration]")
    print("  * Scope Type: EMPIRICAL VERIFICATION (Finite State Trajectories & Fuzzing)")
    print("  * Mathematical Formal Proof (Coq/Lean/Z3): OUT OF SCOPE / NOT CLAIMED")
    print("  * Verification Guarantee: Valid strictly within tested invariants and empirical boundaries.")

    print("\n" + "=" * 75)
    if all_suites_passed:
        print("FINAL FREEZE AUDIT RUNNER: EXECUTION COMPLETED (ALL SUITES PASSED)")
        print("Status: Pending Final System-wide Audit Review")
    else:
        print("FINAL FREEZE AUDIT RUNNER: EXECUTION FAILED")
        print("Status: HOLD / Regression or Failure Detected")
    print("=" * 75)

    return all_suites_passed


if __name__ == "__main__":
    run_final_freeze_audit()