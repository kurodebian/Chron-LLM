# src/causal_kernel/kernel/reconciler/traceability_reconciler.py

from dataclasses import dataclass, field
from typing import Set, Tuple, List, Dict

# 新しい Independent Ground Truth Scanner の型を唯一の正解として参照
from causal_kernel.audit.independent_delta1_scanner import Delta1GroundTruth
from causal_kernel.kernel.reconciler.claim_extractor import TraceabilityClaims


@dataclass
class ReconciliationReport:
    """
    Report comparing Ground Truth vs Claims under Layer A/B Architecture.
    """
    is_consistent: bool = False

    # Nodes
    gt_unique_node_count: int = 0
    claimed_node_count: int = 0
    node_match_count: int = 0
    nodes_only_in_gt: Set[str] = field(default_factory=set)
    nodes_only_in_claim: Set[str] = field(default_factory=set)
    gt_rejected_node_count: int = 0  # 旧 gt_duplicates / parse_errors を包摂

    # Edges
    gt_unique_edge_count: int = 0
    claimed_edge_count: int = 0
    edge_match_count: int = 0
    edges_only_in_gt: Set[Tuple[str, str, str]] = field(default_factory=set)
    edges_only_in_claim: Set[Tuple[str, str, str]] = field(default_factory=set)
    gt_rejected_edge_count: int = 0

    # Errors / Mismatches
    malformed_claims: List[Dict] = field(default_factory=list)


class TraceabilityReconciler:
    def reconcile(self, gt: Delta1GroundTruth, claims: TraceabilityClaims) -> ReconciliationReport:
        report = ReconciliationReport()

        # --- Node Reconciliation ---
        # Layer B Canonical Nodes から識別子集合を構成
        gt_nodes: Set[str] = {node.id for node in gt.canonical_nodes}
        claimed_nodes: Set[str] = claims.claimed_node_ids

        report.gt_unique_node_count = len(gt_nodes)
        report.claimed_node_count = len(claimed_nodes)

        report.node_match_count = len(gt_nodes & claimed_nodes)
        report.nodes_only_in_gt = gt_nodes - claimed_nodes
        report.nodes_only_in_claim = claimed_nodes - gt_nodes
        
        # 物理観測数 (Layer A) と Canonical 昇格数 (Layer B) の差分を無効・重複・拒絶件数とする
        report.gt_rejected_node_count = gt.physical_node_count - len(gt.canonical_nodes)

        # --- Edge Reconciliation ---
        # Layer B Canonical Edges から (from_id, to_id, relation) 集合を構成
        gt_edges: Set[Tuple[str, str, str]] = {
            (edge.from_id, edge.to_id, edge.relation) for edge in gt.canonical_edges
        }
        claimed_edges: Set[Tuple[str, str, str]] = claims.claimed_edge_keys

        report.gt_unique_edge_count = len(gt_edges)
        report.claimed_edge_count = len(claimed_edges)

        report.edge_match_count = len(gt_edges & claimed_edges)
        report.edges_only_in_gt = gt_edges - claimed_edges
        report.edges_only_in_claim = claimed_edges - gt_edges
        
        report.gt_rejected_edge_count = gt.physical_edge_count - len(gt.canonical_edges)

        # --- Consistency Check ---
        node_mismatch = len(report.nodes_only_in_gt) + len(report.nodes_only_in_claim)
        edge_mismatch = len(report.edges_only_in_gt) + len(report.edges_only_in_claim)
        
        # 整合性判定: Node/Edgeの不一致がなく、GT側での拒絶・破損がなく、Claim側にも不正形式がないこと
        report.is_consistent = (
            node_mismatch == 0
            and edge_mismatch == 0
            and report.gt_rejected_node_count == 0
            and report.gt_rejected_edge_count == 0
            and len(claims.malformed_entries) == 0
        )

        report.malformed_claims = claims.malformed_entries

        return report