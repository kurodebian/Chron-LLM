# ~/Chron-LLM/loop-engine/quality_gate.py
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_DIR = Path(__file__).parent / "sandbox" / "repo_test"

# ベースライン凍結時の SHA-256
BASELINE_HASHES = {
    "test_task.py": "fa8e36510aa7c0ef84f38e9f17c21d1e99aef65d50fecb290148ad06ab279630",
    "test_formatter.py": "29c1e8c519704db5118eef2c8234ff0318d64891005916bd56326f771e04df9c",
}

def verify_test_integrity() -> bool:
    """1 & 2. テストファイルの改変検知"""
    for filename, expected_hash in BASELINE_HASHES.items():
        file_path = TARGET_DIR / filename
        if not file_path.exists():
            print(f"[GATE FAIL] Test file missing: {filename}")
            return False
        
        current_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if current_hash != expected_hash:
            print(f"[GATE FAIL] Test tamper detected: {filename}")
            print(f"  Expected: {expected_hash}")
            print(f"  Actual:   {current_hash}")
            return False
    return True

def run_pytest_gate() -> bool:
    """3 & 5. pytest 実行および失敗判定"""
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(TARGET_DIR)
    
    cmd = [sys.executable, "-m", "pytest", str(TARGET_DIR), "-q"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    
    if res.returncode != 0:
        print("[GATE FAIL] pytest execution failed.")
        print(res.stdout)
        return False
    return True

def main():
    print("=== External Quality Gate ===")
    
    # 改変チェック
    if not verify_test_integrity():
        print(">>> OVERALL RESULT: FAIL (Integrity Breach)")
        sys.exit(1)
        
    # pytest 判定
    if not run_pytest_gate():
        print(">>> OVERALL RESULT: FAIL (Assertion Failure)")
        sys.exit(1)
        
    print(">>> OVERALL RESULT: PASS")
    sys.exit(0)

if __name__ == "__main__":
    main()