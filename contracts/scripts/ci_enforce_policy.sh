#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================================="
echo " Chron-LLM v1.3.0 Layer 2 CI Enforcement Suite"
echo "=========================================================================="

# 1. ENFORCE: CI.GREP_INTERNAL_IMPORT
echo "[1/2] Executing ENFORCE: CI.GREP_INTERNAL_IMPORT..."
FORBIDDEN_IMPORTS=$(git grep -E "import[[:space:]]+ChronLLM\.Internal" -- "user_space/" "user_code/" "tests/user/" || true)

if [ -n "$FORBIDDEN_IMPORTS" ]; then
  echo "❌ [FAIL] Policy Violation (POLICY: TCB.ISOLATION.001): Direct import of ChronLLM.Internal detected!"
  echo "$FORBIDDEN_IMPORTS"
  exit 1
fi
echo "  [PASS] No illegal internal imports found in non-TCB modules."

# 2. ENFORCE: CI.ZERO_AXIOMS_CHECK
echo "[2/2] Executing ENFORCE: CI.ZERO_AXIOMS_CHECK..."
lake env lean --run Tests/AxiomCheck.lean

echo "=========================================================================="
echo "  All Layer 2 Enforcement Rules Passed Successfully."
echo "=========================================================================="