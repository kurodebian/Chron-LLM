# src/causal_kernel/kernel/reconciler/traceability_reconciler.py

from dataclasses import dataclass, field
from typing import Set, Tuple, List, Dict, Any

from causal_kernel.audit.independent_delta1_scanner import Delta1GroundTruth
from causal_kernel.kernel.reconciler.claim_extractor import TraceabilityClaims


@dataclass
class ReconciliationReport:
    """
    Report comparing Ground Truth vs Claims under Layer A/B Architecture.

    Node Physical Space (Layer A):
        Evaluates physical record counts (Physical, Canonical, Rejected).

    Node Semantic Space (Layer B):
        Evaluates Canonical Node IDs vs Claimed Node IDs.

    Edge Identity Space:
        Canonical Edge Records (4-tuple) projected into Semantic 3-tuples:
        pi_3(component_id, from_id, to_id, relation) = (from_id, to_id, relation)
    """

    is_consistent: bool = False

    # ------------------------------------------------------------------
    # Node Physical & Semantic Space
    # ------------------------------------------------------------------
    physical_node_count: int = 0
    canonical_node_count: int = 0
    rejected_node_count: int = 0
    claimed_node_count: int = 0

    unclaimed_canonical_nodes: Set[str] = field(default_factory=set)
    phantom_nodes: Set[str] = field(default_factory=set)

    # ------------------------------------------------------------------
    # Edge Identity Space
    # ------------------------------------------------------------------
    canonical_edge_records: int = 0
    gt_semantic_key_count: int = 0
    claimed_semantic_key_count: int = 0

    unclaimed_semantic_edges: Set[Tuple[str, str, str]] = field(
        default_factory=set
    )
    phantom_semantic_edges: Set[Tuple[str, str, str]] = field(
        default_factory=set
    )

    # ------------------------------------------------------------------
    # Errors / Malformed Claims
    # ------------------------------------------------------------------
    edge_mismatch_count: int = 0
    malformed_claim_count: int = 0
    malformed_claims: List[Dict[str, Any]] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Human-readable summary
    # ------------------------------------------------------------------
    def print_summary(self) -> None:
        print("=== RECONCILER AUDIT REPORT ===")

        print("Node:")
        print(f"  physical            = {self.physical_node_count}")
        print(f"  canonical           = {self.canonical_node_count}")
        print(f"  rejected            = {self.rejected_node_count}")
        print(f"  claimed             = {self.claimed_node_count}")
        print(f"  unclaimed_canonical = {len(self.unclaimed_canonical_nodes)}")
        print(f"  phantom             = {len(self.phantom_nodes)}")

        print()

        print("Edge:")
        print(f"  canonical_records   = {self.canonical_edge_records}")
        print(f"  semantic_keys       = {self.gt_semantic_key_count}")
        print(f"  claimed_keys        = {self.claimed_semantic_key_count}")
        print(f"  unclaimed           = {len(self.unclaimed_semantic_edges)}")
        print(f"  phantom             = {len(self.phantom_semantic_edges)}")

        print()

        print("Final:")
        print(f"  edge_mismatch_count = {self.edge_mismatch_count}")
        print(f"  malformed_claim_count = {self.malformed_claim_count}")
        print(f"  is_consistent       = {self.is_consistent}")


class TraceabilityReconciler:

    def reconcile(
        self,
        gt: Delta1GroundTruth,
        claims: TraceabilityClaims,
    ) -> ReconciliationReport:

        report = ReconciliationReport()

        # ==============================================================
        # 1. NODE SPACE RECONCILIATION
        #
        # Physical Record Level Metrics:
        #   physical = len(observed_nodes)
        #   canonical = len(canonical_nodes)
        #   rejected = physical - canonical
        #
        # Semantic Reconciliation:
        #   Canonical Node IDs vs Claimed Node IDs
        # ==============================================================

        report.physical_node_count = gt.physical_node_count
        gt_canonical_node_ids: Set[str] = {node.id for node in gt.canonical_nodes}
        report.canonical_node_count = len(gt_canonical_node_ids)
        report.rejected_node_count = (
            report.physical_node_count - report.canonical_node_count
        )

        claimed_node_ids: Set[str] = set(claims.claimed_node_ids)
        report.claimed_node_count = len(claimed_node_ids)

        report.unclaimed_canonical_nodes = (
            gt_canonical_node_ids - claimed_node_ids
        )
        report.phantom_nodes = claimed_node_ids - gt_canonical_node_ids

        # ==============================================================
        # 2. EDGE SPACE RECONCILIATION
        #
        # Projection pi_3(K_4) = (from_id, to_id, relation)
        # ==============================================================

        gt_semantic_edge_keys: Set[Tuple[str, str, str]] = {
            (
                edge.from_id,
                edge.to_id,
                edge.relation,
            )
            for edge in gt.canonical_edges
        }

        claimed_semantic_keys: Set[Tuple[str, str, str]] = {
            (
                str(src),
                str(dst),
                str(relation),
            )
            for src, dst, relation in claims.claimed_edge_keys
        }

        report.canonical_edge_records = len(gt.canonical_edges)
        report.gt_semantic_key_count = len(gt_semantic_edge_keys)
        report.claimed_semantic_key_count = len(claimed_semantic_keys)

        report.unclaimed_semantic_edges = (
            gt_semantic_edge_keys - claimed_semantic_keys
        )
        report.phantom_semantic_edges = (
            claimed_semantic_keys - gt_semantic_edge_keys
        )

        # ==============================================================
        # 3. CLAIM EXTRACTION ERRORS & VERDICT
        # ==============================================================

        report.malformed_claims = list(claims.malformed_entries)
        report.malformed_claim_count = len(report.malformed_claims)

        # Fallback property for compatibility
        report.edge_mismatch_count = getattr(claims, "edge_mismatch_count", 0)

        report.is_consistent = (
            len(report.unclaimed_canonical_nodes) == 0
            and len(report.phantom_nodes) == 0
            and len(report.unclaimed_semantic_edges) == 0
            and len(report.phantom_semantic_edges) == 0
            and report.edge_mismatch_count == 0
            and report.malformed_claim_count == 0
        )

        return report