import os
import sys
import argparse
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "src"))

from causal_kernel.audit.independent_delta1_scanner import IndependentDelta1Scanner
from causal_kernel.kernel.reconciler.claim_extractor import TraceabilityClaimExtractor
from causal_kernel.kernel.reconciler.traceability_reconciler import TraceabilityReconciler

# 監査対象から除外するスコープ外ファイルのプレフィックス/パターン
EXCLUDED_FILE_PATTERNS = [
    "delta1_structural_summary",  # サマリー集計データ（ID空間不一致）
    "phase6_",                    # Phase 6 依存関係グラフ
    "phase7_",                    # Phase 7 グローバルグラフ
]

def is_valid_traceability_file(file_path: str) -> bool:
    file_name = os.path.basename(file_path)
    for pattern in EXCLUDED_FILE_PATTERNS:
        if pattern in file_name:
            return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Run Traceability Reconciliation Audit")
    parser.add_argument("--delta1-dir", default="data/delta1_normalized", help="Path to Delta-1 normalized JSON directory")
    parser.add_argument("--traceability-dir", default="data/audit", help="Path to Traceability JSON directory")
    args = parser.parse_args()

    print("==================================================")
    print("    RUNNING INDEPENDENT TRACEABILITY AUDIT")
    print("==================================================")

    # 1. Ground Truth Scan 
    print(f"[*] Scanning Ground Truth from: {args.delta1_dir}") 

    scanner = IndependentDelta1Scanner(args.delta1_dir) 
    gt, summary = scanner.scan() 

    print(f" - Physical Nodes : {gt.physical_node_count}") 
    print(f" - Canonical Nodes : {len(gt.canonical_nodes)}") 
    print(f" - Physical Edges : {gt.physical_edge_count}") 
    print(f" - Canonical Edges : {len(gt.canonical_edges)}") 
    print( f" - Rejected Nodes : " f"{gt.physical_node_count - len(gt.canonical_nodes)}" ) 
    print( f" - Rejected Edges : " f"{gt.physical_edge_count - len(gt.canonical_edges)}" )

    # 2. Extract Claims with Filtering
    all_trace_files = []
    filtered_trace_files = []
    
    if os.path.exists(args.traceability_dir):
        for root, _, files in os.walk(args.traceability_dir):
            for file in files:
                if file.endswith(".json"):
                    full_path = os.path.join(root, file)
                    all_trace_files.append(full_path)
                    if is_valid_traceability_file(full_path):
                        filtered_trace_files.append(full_path)

    print(f"\n[*] Extracting Claims from: {args.traceability_dir}")
    print(f"    - Total JSON Files Found : {len(all_trace_files)}")
    print(f"    - Target Audit Files     : {len(filtered_trace_files)} (Excluded: {len(all_trace_files) - len(filtered_trace_files)})")
    
    extractor = TraceabilityClaimExtractor(filtered_trace_files, delta1_dir=args.delta1_dir)
    claims = extractor.extract()
    print(f"    - Claimed Node Count     : {claims.claimed_node_count}")
    print(f"    - Claimed Edge Count     : {claims.claimed_edge_count}")

    # 3. Reconcile
    print("\n[*] Reconciling Ground Truth vs Claims...")
    reconciler = TraceabilityReconciler()
    report = reconciler.reconcile(gt, claims)

    # 4. Report Results
    print("\n==================================================")
    print("    AUDIT RECONCILIATION RESULTS")
    print("==================================================")
    print(f" Status Consistent : {'✅ YES (MATCH)' if report.is_consistent else '❌ NO (DISCREPANCY DETECTED)'}")
    print("--------------------------------------------------")
    print(f" [Nodes]")
    print(f"   - Ground Truth Unique : {report.gt_unique_node_count}")
    print(f"   - Traceability Claim  : {report.claimed_node_count}")
    print(f"   - Matched Nodes       : {report.node_match_count}")
    print(f"   - Discrepancies:")
    print(f"     * GT-Only (Untracked)   : {len(report.nodes_only_in_gt)}")
    print(f"     * Claim-Only (Phantom)  : {len(report.nodes_only_in_claim)}")

    print(f"\n [Edges]")
    print(f"   - Ground Truth Unique : {report.gt_unique_edge_count}")
    print(f"   - Traceability Claim  : {report.claimed_edge_count}")
    print(f"   - Matched Edges       : {report.edge_match_count}")
    print(f"   - Discrepancies:")
    print(f"     * GT-Only (Untracked)   : {len(report.edges_only_in_gt)}")
    print(f"     * Claim-Only (Phantom)  : {len(report.edges_only_in_claim)}")
    print("==================================================")

if __name__ == "__main__":
    main()