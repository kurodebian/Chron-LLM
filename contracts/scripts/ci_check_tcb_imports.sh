#!/usr/bin/env bash
set -euo pipefail

# 非 TCB ソースコードディレクトリ配下で `import ChronLLM.Internal` の有無を全数捜索
FORBIDDEN_IMPORTS=$(git grep -E "import[[:space:]]+ChronLLM\.Internal" -- "user_space/" "user_code/" "tests/user/")

if [ -n "$FORBIDDEN_IMPORTS" ]; then
  echo "[ERROR] TCB Import Guard Failure: Direct import of ChronLLM.Internal detected in non-TCB modules!"
  echo "$FORBIDDEN_IMPORTS"
  exit 1
fi

echo "[SUCCESS] TCB Import Guard Passed: No illegal internal imports found."