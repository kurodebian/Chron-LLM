"""
t1_b_hypothesis_runner.py — T1-B: Property-based Differential Fuzzing
Requires 'hypothesis' and 'pytest' packages.
"""

from hypothesis import given, settings, strategies as st
from step1_reference_parser import parse_reference
from step2_production_parser import parse_production
from t1_differential_adapter import DifferentialAdapter


@settings(max_examples=10000, deadline=None)
@given(st.text(alphabet=st.characters(blacklist_categories=('Cs',)), min_size=0, max_size=80))
def test_t1_b_differential_equivalence(line_text: str):
    """
    Property-based test: For any arbitrary input string,
    Reference Parser and Production Parser must yield identical Canonical Outcomes.
    """
    ref_raw = parse_reference(line_text)
    prod_raw = parse_production(line_text)

    ref_out = DifferentialAdapter.adapt_reference(ref_raw)
    prod_out = DifferentialAdapter.adapt_production(prod_raw)

    assert ref_out == prod_out, (
        f"Differential Mismatch detected on input: {repr(line_text)}\n"
        f"  Reference:  {ref_out}\n"
        f"  Production: {prod_out}"
    )


def run_t1b_fuzzing() -> bool:
    """
    Final Freeze Audit 一元実行用エントリーポイント関数。
    Hypothesis による 10,000 サンプルのプロパティベースファジングを直接実行し、結果を bool で返却。
    """
    print("=" * 75)
    print("T1-B HYPOTHESIS PROPERTY-BASED FUZZING EXECUTION (10,000 Samples)")
    print("=" * 75)
    try:
        test_t1_b_differential_equivalence()
        print("  [PASS] Hypothesis differential fuzzing audit: Zero discrepancy detected.")
        return True
    except Exception as e:
        print(f"  [FAIL] Hypothesis differential fuzzing audit failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = run_t1b_fuzzing()
    sys.exit(0 if success else 1)