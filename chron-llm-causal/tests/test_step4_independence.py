import os
import json
import pytest
from pathlib import Path

from causal_kernel.audit.independent_delta1_scanner import (
    IndependentDelta1Scanner,
    Delta1GroundTruth,
)
from causal_kernel.kernel.reconciler.claim_extractor import TraceabilityClaimExtractor
from causal_kernel.kernel.reconciler.traceability_reconciler import TraceabilityReconciler


class TestStep4Independence:
    @pytest.fixture(autouse=True)
    def setup_dirs(self, tmp_path: Path):
        self.tmpdir = str(tmp_path)
        self.delta1_dir = tmp_path / "delta1"
        self.traceability_dir = tmp_path / "traceability"
        self.delta1_dir.mkdir()
        self.traceability_dir.mkdir()

        # Dummy Delta1 Data (1 component, 4 nodes total with 1 duplicate)
        self.delta1_file1 = self.delta1_dir / "file1.json"
        self.delta1_file1.write_text(json.dumps({
            "component_id": "comp1",
            "nodes": [
                {"id": "NODE_A", "origin": "EXPLICIT_NODE"},
                {"id": "NODE_B", "origin": "EXPLICIT_NODE"}
            ],
            "edges": [
                {"id": "E1", "from": "NODE_A", "to": "NODE_B", "relation": "CAUSES"}
            ],
            "proposals": []
        }), encoding="utf-8")

        self.delta1_file2 = self.delta1_dir / "file2.json"
        self.delta1_file2.write_text(json.dumps({
            "component_id": "comp2",
            "nodes": [
                {"id": "NODE_A", "origin": "EXPLICIT_NODE"},  # Duplicate ID
                {"id": "NODE_C", "origin": "EXPLICIT_NODE"}
            ],
            "edges": [],
            "proposals": []
        }), encoding="utf-8")

        # Dummy Traceability Data
        self.traceability_file = self.traceability_dir / "traceability_v1.json"
        self.traceability_file.write_text(json.dumps({
            "nodes": [{"id": "NODE_A"}, {"id": "NODE_B"}, {"id": "NODE_C"}],
            "edges": [{"from": "NODE_A", "to": "NODE_B", "relation": "CAUSES"}]
        }), encoding="utf-8")

    def test_scanner_independence_and_accuracy(self):
        """
        1. Scanner must produce GT from Delta1 only.
        2. GT must correctly identify duplicates.
        """
        scanner = IndependentDelta1Scanner(self.delta1_dir)
        gt, summary = scanner.scan()

        # Check Raw Physical Counts
        assert gt.physical_node_count == 4  # NODE_A, NODE_B, NODE_A, NODE_C

        # Check Canonical Counts and Identification
        canonical_ids = {node.id for node in gt.canonical_nodes}
        assert len(gt.canonical_nodes) == 3
        assert canonical_ids == {"NODE_A", "NODE_B", "NODE_C"}
        assert summary.identity["duplicate_node_ids"] == 1

    def test_extractor_accuracy(self):
        extractor = TraceabilityClaimExtractor([str(self.traceability_file)])
        claims = extractor.extract()
        assert claims.claimed_node_ids == {"NODE_A", "NODE_B", "NODE_C"}
        assert ("NODE_A", "NODE_B", "CAUSES") in claims.claimed_edge_keys

    def test_reconciler_consistency(self):
        scanner = IndependentDelta1Scanner(self.delta1_dir)
        gt, summary = scanner.scan()

        extractor = TraceabilityClaimExtractor([str(self.traceability_file)])
        claims = extractor.extract()

        reconciler = TraceabilityReconciler()
        report = reconciler.reconcile(gt, claims)

        assert report.is_consistent

    def test_reconciler_discrepancy_hallucination(self):
        bad_trace_file = os.path.join(self.tmpdir, "bad_trace.json")
        bad_data = {
            "nodes": [{"id": "NODE_A"}, {"id": "NODE_B"}, {"id": "NODE_C"}, {"id": "GHOST_NODE"}],
            "edges": []
        }
        with open(bad_trace_file, "w") as f:
            json.dump(bad_data, f)

        scanner = IndependentDelta1Scanner(self.delta1_dir)
        gt, summary = scanner.scan()

        extractor = TraceabilityClaimExtractor([bad_trace_file])
        claims = extractor.extract()

        reconciler = TraceabilityReconciler()
        report = reconciler.reconcile(gt, claims)

        assert not report.is_consistent
        assert "GHOST_NODE" in report.unreconciled_claimed_nodes

    def test_scanner_ignores_traceability_directory(self):
        trap_file = os.path.join(self.traceability_dir, "fake_delta1.json")
        with open(trap_file, "w") as f:
            json.dump({"nodes": [{"id": "TRAP_NODE"}], "edges": []}, f)

        scanner = IndependentDelta1Scanner(self.delta1_dir)
        gt, summary = scanner.scan()

        canonical_ids = {node.id for node in gt.canonical_nodes}
        assert "TRAP_NODE" not in canonical_ids