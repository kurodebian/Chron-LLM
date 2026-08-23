#!/usr/bin/env python3
"""
Traceability Validator for Chron-LLM Delta-1 -> Delta-2 Reduction (AUDIT_R2_REVISION)
Validates machine check invariants without modifying canonical files.
"""

import json
import sys

def validate_traceability(traceability_path: str) -> bool:
    with open(traceability_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    checks = data.get("machine_checks", {})
    
    # Required Invariant Checks
    assert checks.get("NODE_COUNT") == 340, f"NODE_COUNT mismatch: {checks.get('NODE_COUNT')}"
    assert checks.get("EDGE_COUNT") == 312, f"EDGE_COUNT mismatch: {checks.get('EDGE_COUNT')}"
    assert checks.get("NODE_CLASSIFIED") == 340, "NODE_CLASSIFIED != 340"
    assert checks.get("EDGE_CLASSIFIED") == 312, "EDGE_CLASSIFIED != 312"
    assert checks.get("NODE_UNMAPPED") == 0, "NODE_UNMAPPED > 0"
    assert checks.get("EDGE_UNMAPPED") == 0, "EDGE_UNMAPPED > 0"
    assert checks.get("NODE_DUPLICATE_MAPPING") == 0, "NODE_DUPLICATE_MAPPING > 0"
    assert checks.get("EDGE_DUPLICATE_MAPPING") == 0, "EDGE_DUPLICATE_MAPPING > 0"
    assert checks.get("DANGLING_SOURCE") == 0, "DANGLING_SOURCE > 0"
    assert checks.get("DANGLING_TARGET") == 0, "DANGLING_TARGET > 0"

    # Validate Claims Separation
    claims = data.get("claims", {})
    assert claims.get("STRUCTURAL_TRACEABILITY") == "PROVABLE"
    assert claims.get("SEMANTIC_PRESERVATION") == "NOT_CLAIMED_UNTIL_TRACEABILITY_VALIDATION_PASSES"

    # Validate Provenance Completeness
    for node_prov in data.get("delta2_nodes_provenance", []):
        assert node_prov.get("provenance_complete") is True, f"Node provenance incomplete: {node_prov}"

    for edge_prov in data.get("delta2_edges_provenance", []):
        assert edge_prov.get("provenance_complete") is True, f"Edge provenance incomplete: {edge_prov}"

    print("[SUCCESS] AUDIT_R2_REVISION Validation Passed. All 10 Machine Checks OK.")
    return True

if __name__ == "__main__":
    try:
        validate_traceability("delta1_delta2_traceability.json")
    except Exception as e:
        print(f"[FAIL] Validation Error: {e}")
        sys.exit(1)