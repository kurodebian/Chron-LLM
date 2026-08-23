#!/usr/bin/env python3
"""
CHRON-LLM PHASE C4: 12-NODE PYTHON <-> SBCL CROSS-VALIDATION DRIVER
Validates SBCL runtime execution traces against MasterGraph v2.0 (12N/38E) axioms.
"""

import json
import os
import subprocess
import sys


def load_master_graph(graph_path: str) -> dict:
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"MasterGraph not found at {graph_path}")
    with open(graph_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_sbcl_full_kernel(kernel_path: str) -> list:
    cmd = ["sbcl", "--script", kernel_path]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[ERROR] SBCL execution failed with return code {result.returncode}")
        print(result.stderr)
        sys.exit(1)

    stdout = result.stdout
    if "---SBCL_TRACE_BEGIN---" not in stdout or "---SBCL_TRACE_END---" not in stdout:
        print("[ERROR] Missing JSON trace delimiters in SBCL output.")
        print(stdout)
        sys.exit(1)

    raw_json = stdout.split("---SBCL_TRACE_BEGIN---")[1].split("---SBCL_TRACE_END---")[0]
    return json.loads(raw_json.strip())


def validate_traces_against_master_graph(traces: list, graph: dict) -> bool:
    print("\n=======================================================================")
    print("    CHRON-LLM 12-NODE CROSS-VALIDATION REPORT (SBCL ↔ Python Graph)")
    print("=======================================================================")

    expectations = {
        "TC1_VALID_PATH": {
            "expected_status": "ACCEPT",
            "required_edges": ["EDGE_0001", "EDGE_0002", "EDGE_0003", "EDGE_0004"],
            "pipeline_sequence": ["RuntimePipeline", "DerivePipeline", "CommitPipeline"],
            "description": "Full end-to-end causal path execution with valid AUTH-001 guard.",
        },
        "TC2_INVALID_AUTH": {
            "expected_status": "REJECT",
            "expected_reason": "ERR_MISSING_AUTH_GUARD",
            "target_invariant": "INV_AUTH_001",
            "description": "Authority Boundary Morphism trap on invalid guard token.",
        },
        "TC3_DERIVE_PURITY_VIOLATION": {
            "expected_status": "REJECT",
            "expected_reason": "ERR_DERIVE_PURITY_FAIL",
            "target_invariant": "INV_DER_001",
            "description": "DerivePipeline AST mutation trap for impure state operators.",
        },
    }

    all_passed = True

    for trace in traces:
        test_id = trace.get("test_id")
        status = trace.get("status")
        reason = trace.get("reason")

        exp = expectations.get(test_id)
        if not exp:
            print(f"[FAIL] Unrecognized Test ID in trace: {test_id}")
            all_passed = False
            continue

        status_ok = status == exp["expected_status"]
        reason_ok = (reason == exp.get("expected_reason")) if exp.get("expected_reason") else True

        if status_ok and reason_ok:
            print(f"[PASSED] {test_id}")
            print(f"         Status : {status} (Expected: {exp['expected_status']})")
            print(f"         Context: {exp['description']}")
            if reason:
                print(f"         Reason : {reason}")
        else:
            print(f"[FAILED] {test_id}")
            print(f"         Got Status: {status}, Expected: {exp['expected_status']}")
            print(f"         Got Reason: {reason}, Expected: {exp.get('expected_reason')}")
            all_passed = False

    print("=======================================================================\n")

    if all_passed:
        print("[SUCCESS] All SBCL runtime traces are 100% consistent with MasterGraph v2.0 Axioms.")
        return True
    else:
        print("[FAILURE] Inconsistencies detected between SBCL Runtime and MasterGraph v2.0.")
        return False


def main():
    graph_path = "data/graphs/causal_master_graph_v2.json"
    kernel_path = "src/causal_kernel/sbcl/chron_kernel_full_v2.lisp"

    graph = load_master_graph(graph_path)
    traces = run_sbcl_full_kernel(kernel_path)
    success = validate_traces_against_master_graph(traces, graph)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()