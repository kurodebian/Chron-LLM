"""
t5_stateful_reducer_test_runner.py — T5: Stateful ContextReducer Trajectory Invariants Audit (Strictly Strengthened)
"""

from step0_ssot import ParseStatus, ClaimType
from step2_production_parser import parse_production, ProductionParseResult
from step3_context_reducer import ContextReducer, ContextState


def run_t5_stateful_audit() -> bool:
    print("=" * 75)
    print("T5 AUDIT: STATEFUL CONTEXT REDUCER TRAJECTORY INVARIANTS (STRICT)")
    print("=" * 75)

    all_passed = True

    # -------------------------------------------------------------------------
    # Sub-Test 1: Transition & Retention Invariants (Including INVALID_CONTEXT)
    # -------------------------------------------------------------------------
    print("\n[Sub-Test 1] Transition & Retention Invariants")
    
    s0 = ContextState(current_unit=None)
    
    r_unit_a = parse_production("unit: ModuleA", None)
    s1 = ContextReducer.reduce(s0, r_unit_a)
    
    r_req_x = parse_production("requires: LibX", s1.current_unit)
    s2 = ContextReducer.reduce(s1, r_req_x)

    r_inv_grammar = parse_production("unit: @EVIL", s2.current_unit)
    s3_a = ContextReducer.reduce(s2, r_inv_grammar)

    r_inv_context = parse_production("requires: DB", "@EVIL")
    s3_b = ContextReducer.reduce(s3_a, r_inv_context)

    r_unit_b = parse_production("unit: ModuleB", s3_b.current_unit)
    s4 = ContextReducer.reduce(s3_b, r_unit_b)

    inv_pass = (
        s1.current_unit == "ModuleA" and
        s2.current_unit == "ModuleA" and
        s3_a.current_unit == "ModuleA" and
        s3_b.current_unit == "ModuleA" and
        s4.current_unit == "ModuleB"
    )
    if inv_pass:
        print("  [PASS] Transition and all retention classes correctly maintained.")
    else:
        print("  [FAIL] Transition or retention invariant violated.")
        all_passed = False

    # -------------------------------------------------------------------------
    # Sub-Test 2: Historical State Immutability & Structural Identity Audit (A. Historical Identity)
    # -------------------------------------------------------------------------
    print("\n[Sub-Test 2] Historical State Immutability & Structural Identity (id() Uniqueness)")
    
    history = []
    curr_state = ContextState(current_unit=None)
    history.append(curr_state)

    lines_sequence = [
        "unit: App.Base",
        "requires: DB",
        "depends_on: Logger",
        "unit: App.Core",
        "requires: Auth",
        "unit: @BAD_UNIT",
        "# Just a comment",
        "requires: Config",
    ]

    for line in lines_sequence:
        prev_state = curr_state
        p_res = parse_production(line, curr_state.current_unit)
        curr_state = ContextReducer.reduce(curr_state, p_res)
        
        # 連続する状態間でのオブジェクト非同一性 (is not)
        if curr_state is prev_state:
            print(f"  [FAIL] State mutation in place detected at line: '{line}'")
            all_passed = False
        
        history.append(curr_state)

    # 履歴全体のすべてのオブジェクト ID が完全に一意であることの検証
    history_ids = [id(s) for s in history]
    if len(set(history_ids)) == len(history):
        print(f"  [PASS] All {len(history)} trajectory snapshots possess strictly unique object identities (no state recycling).")
    else:
        print("  [FAIL] State object identity collision detected across history.")
        all_passed = False

    # -------------------------------------------------------------------------
    # Sub-Test 3: Adversarial Boundary Isolation
    # -------------------------------------------------------------------------
    print("\n[Sub-Test 3] Adversarial Boundary Isolation")
    
    state = ContextState(current_unit="ModuleInitial")
    adversarial_inputs = [
        ("requires: Evil1", "ModuleInitial"),
        ("unit: @BAD1", "ModuleInitial"),
        ("unit: ValidAlpha", "ModuleInitial"),
        ("requires: Evil2", "ValidAlpha"),
        ("unit: @BAD2", "ValidAlpha"),
        ("unit: ValidBeta", "ValidAlpha"),
    ]

    expected_state_chain = [
        "ModuleInitial", "ModuleInitial", "ValidAlpha",
        "ValidAlpha", "ValidAlpha", "ValidBeta"
    ]

    adv_pass = True
    for (line, _), exp_unit in zip(adversarial_inputs, expected_state_chain):
        res = parse_production(line, state.current_unit)
        state = ContextReducer.reduce(state, res)
        if state.current_unit != exp_unit:
            print(f"  [FAIL] Adversarial drift at line '{line}': expected {exp_unit}, got {state.current_unit}")
            adv_pass = False
            all_passed = False

    if adv_pass:
        print("  [PASS] State boundaries remained fully isolated under adversarial sequences.")

    # -------------------------------------------------------------------------
    # Sub-Test 4: True Composition Audit (B. True Composition / Path-Consistency)
    # -------------------------------------------------------------------------
    print("\n[Sub-Test 4] True Composition Audit (Independent Path Convergence)")
    
    # 経路 A: S0 -> (unit: ModuleA) -> S1_A -> (requires: DB) -> S2_A
    s0 = ContextState(current_unit="Root")
    r1 = parse_production("unit: ModuleA", s0.current_unit)
    s1_a = ContextReducer.reduce(s0, r1)
    r2 = parse_production("requires: DB", s1_a.current_unit)
    s2_a = ContextReducer.reduce(s1_a, r2)

    # 経路 B: 独立に構築した同一の中間状態 S1_B から同一の還元処理を通す
    s1_b = ContextState(current_unit="ModuleA")  # 同値の中間状態を独立生成
    s2_b = ContextReducer.reduce(s1_b, r2)

    if s2_a == s2_b and s2_a is not s2_b:
        print("  [PASS] True path-consistency verified: independent paths yielding identical intermediate states converge to identical final states.")
    else:
        print("  [FAIL] Path convergence failed or state identity anomaly.")
        all_passed = False

    # -------------------------------------------------------------------------
    # Sub-Test 5: Parser-Reducer Separation Audit (C. Parser-Reducer Contract Isolation)
    # -------------------------------------------------------------------------
    print("\n[Sub-Test 5] Parser-Reducer Separation Audit (Typed IR Consumption)")
    
    # 偽装された複数の Typed IR（ProductionParseResult）を生成し、Reducer が
    # 「文字列の解析」を行わず、渡された IR のみを厳密に評価しているかを検証
    forged_units = ["TargetX", "TargetY", "TargetZ.Sub"]
    separation_passed = True

    for target in forged_units:
        forged_result = ProductionParseResult(
            status=ParseStatus.VALID_CLAIM,
            claim_type=ClaimType.UNIT,
            target=target,
            trace=("P1", "P2", "P3", "P4", "P5")
        )
        
        initial = ContextState(current_unit="BaseUnit")
        next_state = ContextReducer.reduce(initial, forged_result)
        
        if next_state.current_unit != target:
            print(f"  [FAIL] Reducer failed to strictly consume target '{target}', got '{next_state.current_unit}'")
            separation_passed = False
            all_passed = False

    # 無効なステータスを持つ偽装 IR が渡された場合、Reducer が状態を変更しないことの検証
    invalid_forged_result = ProductionParseResult(
        status=ParseStatus.INVALID_GRAMMAR,
        claim_type=ClaimType.UNIT,
        target="ShouldNotBeApplied",
        trace=()
    )
    safe_state = ContextState(current_unit="ImmutableBase")
    safe_next_state = ContextReducer.reduce(safe_state, invalid_forged_result)
    
    if safe_next_state.current_unit == "ImmutableBase":
        print("  [PASS] Reducer rejects non-VALID_CLAIM IR structures regardless of inner fields.")
    else:
        print("  [FAIL] Reducer incorrectly accepted invalid status IR.")
        separation_passed = False
        all_passed = False

    if separation_passed:
        print("  [PASS] Parser-Reducer contract separation strictly verified: Reducer is a pure Typed IR consumer.")

    print("-" * 75)
    print(f"T5 Stateful Trajectory Audit (Strict): {'PASSED' if all_passed else 'FAILED'}")
    print("=" * 75)
    return all_passed


if __name__ == "__main__":
    run_t5_stateful_audit()