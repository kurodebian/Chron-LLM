"""
t4_determinism_test_runner.py — T4: Determinism, Structural Immutability & Context Immutability Audit
"""

from step0_ssot import ParseStatus, ClaimType
from step2_production_parser import parse_production, ProductionParseResult
from step3_context_reducer import ContextReducer, ContextState


def run_t4_determinism_audit() -> bool:
    print("=" * 75)
    print("T4 AUDIT: DETERMINISM, IMMUTABILITY & REPEATED EVALUATION")
    print("=" * 75)

    all_passed = True

    # -------------------------------------------------------------------------
    # Sub-Test 1: Referential Determinism Across Multiple Runs
    # -------------------------------------------------------------------------
    print("\n[Sub-Test 1] Referential Determinism & Repeated Evaluation")
    test_cases = [
        ("App.Core", "requires: DB"),
        ("@EVIL", "requires: DB"),
        ("@EVIL", "# Comment"),
        ("App.Core", "requires:"),
    ]

    for unit, line in test_cases:
        base_res = parse_production(line, unit)
        for i in range(10):
            loop_res = parse_production(line, unit)
            if loop_res != base_res:
                print(f"  [FAIL] Non-deterministic behavior detected at iteration {i} for line: '{line}'")
                all_passed = False
                break
        else:
            print(f"  [PASS] 10x repeated execution identical for: '{line}' (Status: {base_res.status.name})")

    # -------------------------------------------------------------------------
    # Sub-Test 2: Trace & Result Structural Immutability Audit (3-Layer Lock)
    # -------------------------------------------------------------------------
    print("\n[Sub-Test 2] Trace & Result Structural Immutability Audit")
    
    res = parse_production("requires: DB", "@EVIL")
    
    # Layer 1: 型が tuple であること
    if isinstance(res.trace, tuple):
        print("  [PASS] [Layer 1] ProductionParseResult.trace is enforced as tuple.")
    else:
        print(f"  [FAIL] [Layer 1] ProductionParseResult.trace is not a tuple! Type: {type(res.trace)}")
        all_passed = False

    # Layer 2: tuple 内部要素の不変性 (append/clear 等の破壊操作の拒絶)
    try:
        res.trace.append("CORRUPTED_P6")  # type: ignore
        print("  [FAIL] [Layer 2] Mutation operation 'append' succeeded on trace tuple!")
        all_passed = False
    except AttributeError:
        print("  [PASS] [Layer 2] Internal element mutation on 'trace' tuple correctly blocked (AttributeError).")

    # Layer 3: ProductionParseResult インスタンスのフィールド再代入拒絶
    try:
        res.trace = ("CORRUPTED_P6",)  # type: ignore
        print("  [FAIL] [Layer 3] Result field re-assignment succeeded!")
        all_passed = False
    except AttributeError:
        print("  [PASS] [Layer 3] Field re-assignment on ProductionParseResult correctly blocked (AttributeError).")

    # -------------------------------------------------------------------------
    # Sub-Test 3: Order-Independence Audit (Stateless Internal Engine)
    # -------------------------------------------------------------------------
    print("\n[Sub-Test 3] Order-Independence & Stateless Engine Audit")
    
    sequence_A = [
        ("App.Core", "requires: DB"),
        ("@EVIL", "requires: DB"),
        ("App.Core", "unit: App.Core"),
    ]
    sequence_B = list(reversed(sequence_A))

    results_A = [parse_production(l, u) for u, l in sequence_A]
    results_B = [parse_production(l, u) for u, l in sequence_B]

    if results_A == list(reversed(results_B)):
        print("  [PASS] Execution sequence order does not cause internal state drift.")
    else:
        print("  [FAIL] Sequence order affected parsing outcomes!")
        all_passed = False

    # -------------------------------------------------------------------------
    # Sub-Test 4: ContextReducer Immutability Audit (Pure Reducer State Transition)
    # -------------------------------------------------------------------------
    print("\n[Sub-Test 4] ContextReducer Immutability Audit")
    
    initial_state = ContextState(current_unit="ModuleA")
    parse_result = parse_production("unit: ModuleB", "ModuleA")
    next_state = ContextReducer.reduce(initial_state, parse_result)

    cond_initial_unchanged = (initial_state.current_unit == "ModuleA")
    cond_next_updated = (next_state.current_unit == "ModuleB")
    cond_new_instance = (initial_state is not next_state)

    if cond_initial_unchanged and cond_next_updated and cond_new_instance:
        print("  [PASS] ContextReducer transition is pure: Context_t is unchanged, Context_t+1 is a new instance.")
    else:
        print("  [FAIL] ContextReducer mutated initial state or failed to yield new instance!")
        all_passed = False

    print("-" * 75)
    print(f"T4 Determinism & Immutability Audit: {'PASSED' if all_passed else 'FAILED'}")
    print("=" * 75)
    return all_passed


if __name__ == "__main__":
    run_t4_determinism_audit()