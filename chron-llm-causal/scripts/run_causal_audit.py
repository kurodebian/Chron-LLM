#!/usr/bin/env python3
import json
import os
import sys
import logging
from datetime import datetime
from jsonschema import validate, ValidationError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DELTA1 = os.path.join(BASE_DIR, 'data', 'delta1_normalized')
DATA_GRAPH = os.path.join(BASE_DIR, 'data', 'graphs')
SCHEMAS = os.path.join(BASE_DIR, 'schemas')
AUDIT_OUT = os.path.join(BASE_DIR, 'data', 'audit')

# Ensure audit output dir exists
if not os.path.exists(AUDIT_OUT):
    os.makedirs(AUDIT_OUT)

audit_results = {
    "audit_id": f"AUDIT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
    "status": "PENDING",
    "checks": {},
    "evidence": []
}

def check_schema_validation():
    """
    Check if Delta-1 and Delta-2 data conform to their respective schemas.
    """
    logging.info("Running Schema Validation...")
    checks = {}
    
    # 1. Delta-1 Extraction Schema
    schema_path = os.path.join(SCHEMAS, 'delta1-extraction.schema.json')
    with open(schema_path) as f:
        delta1_schema = json.load(f)
    
    delta1_files = [f for f in os.listdir(DATA_DELTA1) if f.endswith('.json')]
    delta1_status = "PASS"
    errors = []
    for file in delta1_files:
        with open(os.path.join(DATA_DELTA1, file)) as f:
            try:
                data = json.load(f)
                validate(instance=data, schema=delta1_schema)
            except (ValidationError, json.JSONDecodeError) as e:
                delta1_status = "FAIL"
                errors.append(f"File: {file}, Error: {str(e)}")
    
    checks["delta1_schema"] = {
        "status": delta1_status,
        "details": errors
    }
    
    # 2. Delta-2 MasterGraph Schema
    schema_path = os.path.join(SCHEMAS, 'delta2-mastergraph.schema.json')
    with open(schema_path) as f:
        delta2_schema = json.load(f)
    
    master_graph_file = "causal_master_graph_v2.json"
    if os.path.exists(os.path.join(DATA_GRAPH, master_graph_file)):
        with open(os.path.join(DATA_GRAPH, master_graph_file)) as f:
            try:
                data = json.load(f)
                validate(instance=data, schema=delta2_schema)
                delta2_status = "PASS"
                errors = []
            except (ValidationError, json.JSONDecodeError) as e:
                delta2_status = "FAIL"
                errors.append(f"Error: {str(e)}")
    else:
        delta2_status = "FAIL"
        errors = ["Master Graph file not found"]
        
    checks["delta2_schema"] = {
        "status": delta2_status,
        "details": errors
    }
    
    audit_results["checks"].update(checks)
    if any(v["status"] == "FAIL" for v in checks.values()):
        audit_results["status"] = "FAIL"

def check_independent_recomputation():
    """
    Run the Independent Delta-1 Scanner to validate the physical integrity
    and canonical promotion of the Delta-1 data.
    """
    logging.info("Running Independent Delta-1 Audit (Scanner)...")
    
    try:
        # 1. Import the Scanner Class
        sys.path.append(os.path.join(BASE_DIR, 'src', 'causal_kernel', 'audit'))
        from independent_delta1_scanner import IndependentDelta1Scanner, Path

        # 2. Initialize Scanner with the target directory
        # We are auditing the 'normalized' data which serves as the current ground truth
        target_dir = Path(DATA_DELTA1)
        
        if not target_dir.exists():
            raise FileNotFoundError(f"Target directory {target_dir} does not exist")

        scanner = IndependentDelta1Scanner(target_dir)
        
        # 3. Execute Scan
        # This returns a GroundTruth object and a Summary
        gt_snapshot, scan_summary = scanner.scan()

        # 4. Evaluate Status
        status = scan_summary.status
        
        # 5. Extract Key Metrics for Reporting
        details = {
            "physical_population": scan_summary.physical_population,
            "canonical_population": scan_summary.canonical_population,
            "identity_metrics": scan_summary.identity,
            "error_count": len(scan_summary.errors)
        }
        
        # If there are errors, include a few samples for debugging
        if scan_summary.errors:
            details["error_samples"] = [
                {
                    "type": err.get("type"),
                    "file": err.get("file"),
                    "message": err.get("message")
                }
                for err in list(scan_summary.errors)[:5] # Limit to 5 for log size
            ]

        audit_results["checks"]["recomputation"] = {
            "status": status,
            "details": details
        }

        if status == "FAIL":
            audit_results["status"] = "FAIL"
            logging.warning(f"Scanner found {len(scan_summary.errors)} issues.")
        
    except Exception as e:
        logging.exception("Scanner execution failed")
        audit_results["checks"]["recomputation"] = {
            "status": "FAIL",
            "message": f"Scanner execution failed: {str(e)}"
        }
        audit_results["status"] = "FAIL"


def main():
    logging.info("Starting Causal Audit...")
    
    # 1. Schema Check
    check_schema_validation()
    
    # 2. Recomputation Check (The most critical part)
    check_independent_recomputation()
    
    # 3. Write Report
    report_path = os.path.join(AUDIT_OUT, f"audit_report_{audit_results['audit_id']}.json")
    with open(report_path, 'w') as f:
        json.dump(audit_results, f, indent=2)
        
    logging.info(f"Audit complete. Report saved to {report_path}")
    logging.info(f"Status: {audit_results['status']}")
    
    return 0 if audit_results["status"] == "PASS" else 1

if __name__ == "__main__":
    exit(main())
