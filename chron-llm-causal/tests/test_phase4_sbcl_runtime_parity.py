import subprocess
import json
import re
from pathlib import Path

SBCL_SCRIPT = "src/causal_kernel/sbcl/chron_kernel_full_v2.lisp"

TRACE_BEGIN = re.compile(r"---SBCL_TRACE_BEGIN---")
TRACE_END   = re.compile(r"---SBCL_TRACE_END---")

def extract_trace(output: str):
    lines = output.splitlines()
    begin = None
    end = None

    for i, line in enumerate(lines):
        if TRACE_BEGIN.search(line):
            begin = i + 1
        if TRACE_END.search(line):
            end = i
            break

    assert begin is not None, "SBCL_TRACE_BEGIN not found"
    assert end is not None, "SBCL_TRACE_END not found"

    trace_json = "\n".join(lines[begin:end]).strip()
    return json.loads(trace_json)

def test_phase4_sbcl_runtime_parity():
    assert Path(SBCL_SCRIPT).exists(), "SBCL script missing"

    proc = subprocess.Popen(
        ["sbcl", "--script", SBCL_SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate()

    assert proc.returncode == 0, f"SBCL exited with nonzero code: {proc.returncode}"
    assert stdout, "SBCL produced no stdout"

    trace = extract_trace(stdout)

    # Minimum required tests
    tc1 = next(t for t in trace if t["test_id"] == "TC1_VALID_PATH")
    tc2 = next(t for t in trace if t["test_id"] == "TC2_INVALID_AUTH")
    tc3 = next(t for t in trace if t["test_id"] == "TC3_DERIVE_PURITY_VIOLATION")

    # Assertions
    assert tc1["status"] == "ACCEPT"
    assert tc2["status"] == "REJECT"
    assert tc2.get("reason") == "ERR_MISSING_AUTH_GUARD"
    assert tc3["status"] == "REJECT"
    assert tc3.get("reason") == "ERR_DERIVE_PURITY_FAIL"

    # Evidence retention
    Path("data/audit/phase4_sbcl_runtime_trace.log").write_text(stdout)
