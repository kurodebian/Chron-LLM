# src/causal_kernel/kernel/reconciler/traceability_reconciler.py

from dataclasses import dataclass, field
from typing import Set, Tuple, List, Dict  # <-- Dict を追加

# Absolute imports to ensure correctness regardless of entry point
from causal_kernel.kernel.scanner.delta1_scanner import Delta1GroundTruth
from causal_kernel.kernel.reconciler.claim_extractor import TraceabilityClaims

@dataclass
class ReconciliationReport:
    """
    Report comparing Ground Truth vs Claims.
    """
    is_consistent: bool = False
    
    # Nodes
    gt_unique_node_count: int = 0
    claimed_node_count: int = 0
    node_match_count: int = 0
    nodes_only_in_gt: Set[str] = field(default_factory=set)
    nodes_only_in_claim: Set[str] = field(default_factory=set)
    gt_duplicates: int = 0
    
    # Edges
    gt_unique_edge_count: int = 0
    claimed_edge_count: int = 0
    edge_match_count: int = 0
    edges_only_in_gt: Set[Tuple[str, str, str]] = field(default_factory=set)
    edges_only_in_claim: Set[Tuple[str, str, str]] = field(default_factory=set)
    
    # Errors
    parse_errors_from_gt: List[Dict] = field(default_factory=list)
    malformed_claims: List[Dict] = field(default_factory=list)

class TraceabilityReconciler:
    def reconcile(self, gt: Delta1GroundTruth, claims: TraceabilityClaims) -> ReconciliationReport:
        report = ReconciliationReport()
        
        # --- Node Reconciliation ---
        gt_nodes = gt.unique_node_ids
        claimed_nodes = claims.claimed_node_ids
        
        report.gt_unique_node_count = len(gt_nodes)
        report.claimed_node_count = len(claimed_nodes)
        
        report.node_match_count = len(gt_nodes & claimed_nodes)
        report.nodes_only_in_gt = gt_nodes - claimed_nodes
        report.nodes_only_in_claim = claimed_nodes - gt_nodes
        report.gt_duplicates = len(gt.duplicate_node_ids)
        
        # --- Edge Reconciliation ---
        gt_edges = gt.unique_edge_keys
        claimed_edges = claims.claimed_edge_keys
        
        report.gt_unique_edge_count = len(gt_edges)
        report.claimed_edge_count = len(claimed_edges)
        
        report.edge_match_count = len(gt_edges & claimed_edges)
        report.edges_only_in_gt = gt_edges - claimed_edges
        report.edges_only_in_claim = claimed_edges - gt_edges
        
        # --- Consistency Check ---
        node_mismatch = len(report.nodes_only_in_gt) + len(report.nodes_only_in_claim)
        edge_mismatch = len(report.edges_only_in_gt) + len(report.edges_only_in_claim)
        
        report.is_consistent = (node_mismatch == 0 and edge_mismatch == 0 and 
                                len(gt.parse_errors) == 0 and len(claims.malformed_entries) == 0)
        
        report.parse_errors_from_gt = gt.parse_errors
        report.malformed_claims = claims.malformed_entries
        
        return report