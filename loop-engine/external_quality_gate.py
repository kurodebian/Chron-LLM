from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent
TARGET = REPO / "sandbox" / "repo_test"
BASELINE = REPO / "sandbox" / "repo_test_baseline"

PROTECTED_TESTS = [
    TARGET / "test_task.py",
    TARGET / "test_formatter.py",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_test_integrity() -> bool:
    ok = True

    for current in PROTECTED_TESTS:
        baseline = BASELINE / current.name

        if not current.exists():
            print(f"TEST_BASELINE_FAIL: missing {current}")
            ok = False
            continue

        if not baseline.exists():
            print(f"TEST_BASELINE_FAIL: missing baseline {baseline}")
            ok = False
            continue

        current_hash = sha256(current)
        baseline_hash = sha256(baseline)

        if current_hash != baseline_hash:
            print(f"TEST_BASELINE_FAIL: modified {current}")
            print(f"  baseline={baseline_hash}")
            print(f"  current ={current_hash}")
            ok = False

    if ok:
        print("TEST_BASELINE_PASS")

    return ok


def run_tests() -> bool:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(TARGET),
            "-q",
        ],
        cwd=REPO,
        env={
            **__import__("os").environ,
            "PYTHONPATH": str(TARGET),
        },
    )

    if result.returncode == 0:
        print("PYTEST_PASS")
        return True

    print("PYTEST_FAIL")
    return False


def main() -> int:
    integrity_ok = check_test_integrity()

    if not integrity_ok:
        print("EXTERNAL_QUALITY_GATE=FAIL")
        return 1

    tests_ok = run_tests()

    if not tests_ok:
        print("EXTERNAL_QUALITY_GATE=FAIL")
        return 1

    print("EXTERNAL_QUALITY_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
