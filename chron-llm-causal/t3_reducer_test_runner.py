"""
t3_reducer_test_runner.py — T3: ContextReducer Audit Verification
"""

from step0_ssot import ParseStatus, ClaimType
from step2_production_parser import parse_production
from step3_context_reducer import ContextState, ContextReducer


def run_t3_reducer_audit():
    print("=" * 75)
    print("T3 CONTEXT REDUCER STATE TRANSITION AUDIT")
    print("=" * 75)

    # テストストリーム（Parserを通過した行と状態維持の挙動検証）
    test_stream = [
        ("# Initial Comment", None, "Initial state retains None"),
        ("unit: ModuleA", "ModuleA", "UNIT Claim updates current_unit to 'ModuleA'"),
        ("requires: Dep1", "ModuleA", "REQUIRES Claim retains 'ModuleA'"),
        ("depends_on: ServiceB", "ModuleA", "DEPENDS_ON Claim retains 'ModuleA'"),
        ("   ", "ModuleA", "Blank line retains 'ModuleA'"),
        ("invalid syntax :", "ModuleA", "INVALID_GRAMMAR retains 'ModuleA'"),
        ("unit: ModuleB", "ModuleB", "New UNIT Claim updates current_unit to 'ModuleB'"),
        ("requires: Dep2", "ModuleB", "REQUIRES Claim retains 'ModuleB'"),
    ]

    state = ContextState()
    all_passed = True

    for idx, (line, expected_unit, desc) in enumerate(test_stream, 1):
        parse_res = parse_production(line)
        state = ContextReducer.reduce(state, parse_res)
        
        passed = (state.current_unit == expected_unit)
        if not passed:
            all_passed = False
            
        status_str = "[PASS]" if passed else "[FAIL]"
        print(f"Step {idx:02d} {status_str} Input: {repr(line):<22} | "
              f"Unit: {repr(state.current_unit):<10} | {desc}")

    print("-" * 75)
    if all_passed:
        print("T3 Context Transition Audit: PASSED (Context Retention & Transition Verified)")
    else:
        print("T3 Context Transition Audit: FAILED (State Mutation Discrepancy Detected)")
    print("=" * 75)


if __name__ == "__main__":
    run_t3_reducer_audit()