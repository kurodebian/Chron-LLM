# tests/test_step4_independence.py

import pytest
import tempfile
import json
import os
import sys

# Ensure the root package is importable
# Adjust this path if your project structure differs (e.g., if 'src' is the root)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from causal_kernel.kernel.scanner.delta1_scanner import IndependentDelta1Scanner
from causal_kernel.kernel.reconciler.claim_extractor import TraceabilityClaimExtractor
from causal_kernel.kernel.reconciler.traceability_reconciler import TraceabilityReconciler

class TestStep4Independence:
    
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        
        # Create mock Delta1 normalized files
        self.delta1_dir = os.path.join(self.tmpdir, "delta1_normalized")
        os.makedirs(self.delta1_dir)
        
        # File 1: Node A, Edge A->B
        file1 = {
            "nodes": [{"id": "NODE_A"}, {"id": "NODE_B"}],
            "edges": [{"source": "NODE_A", "target": "NODE_B", "type": "CAUSES"}]
        }
        
        # File 2: Node A (Duplicate), Node C
        file2 = {
            "nodes": [{"id": "NODE_A"}, {"id": "NODE_C"}],
            "edges": []
        }
        
        with open(os.path.join(self.delta1_dir, "file1.json"), "w") as f:
            json.dump(file1, f)
        with open(os.path.join(self.delta1_dir, "file2.json"), "w") as f:
            json.dump(file2, f)
            
        # Create mock Traceability file (Claims)
        self.traceability_dir = os.path.join(self.tmpdir, "audit")
        os.makedirs(self.traceability_dir)
        
        # Claim: Matches GT exactly for now
        traceability_data = {
            "nodes": [{"id": "NODE_A"}, {"id": "NODE_B"}, {"id": "NODE_C"}],
            "edges": [{"source": "NODE_A", "target": "NODE_B", "type": "CAUSES"}]
        }
        self.traceability_file = os.path.join(self.traceability_dir, "traceability_v1.json")
        with open(self.traceability_file, "w") as f:
            json.dump(traceability_data, f)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_scanner_independence_and_accuracy(self):
        """
        1. Scanner must produce GT from Delta1 only.
        2. GT must correctly identify duplicates.
        """
        scanner = IndependentDelta1Scanner(self.delta1_dir)
        gt = scanner.scan()
        
        # Check Raw Counts
        assert gt.raw_node_occurrences == 4  # A, B, A, C
        assert gt.raw_edge_occurrences == 1  # A->B
        
        # Check Unique Counts
        assert gt.unique_node_count == 3     # A, B, C
        assert gt.unique_edge_count == 1     # A->B
        
        # Check Duplicates
        assert "NODE_A" in gt.duplicate_node_ids
        assert len(gt.duplicate_node_ids) == 1
        
        # Check Independence (Implicit: it didn't crash or look for traceability)
        assert len(gt.files_scanned) == 2

    def test_extractor_accuracy(self):
        """
        Extractor must pull claims from Traceability.
        """
        extractor = TraceabilityClaimExtractor([self.traceability_file])
        claims = extractor.extract()
        
        assert "NODE_A" in claims.claimed_node_ids
        assert "NODE_B" in claims.claimed_node_ids
        assert "NODE_C" in claims.claimed_node_ids
        assert ("NODE_A", "NODE_B", "CAUSES") in claims.claimed_edge_keys
        
        assert claims.claimed_node_count == 3
        assert claims.claimed_edge_count == 1

    def test_reconciler_consistency(self):
        """
        If GT == Claims, Reconciler should report consistent.
        """
        scanner = IndependentDelta1Scanner(self.delta1_dir)
        gt = scanner.scan()
        
        extractor = TraceabilityClaimExtractor([self.traceability_file])
        claims = extractor.extract()
        
        reconciler = TraceabilityReconciler()
        report = reconciler.reconcile(gt, claims)
        
        assert report.is_consistent is True
        assert report.node_match_count == 3
        assert report.edge_match_count == 1
        assert len(report.nodes_only_in_gt) == 0
        assert len(report.nodes_only_in_claim) == 0

    def test_reconciler_discrepancy_hallucination(self):
        """
        If Claims contain a node that GT does not have (Hallucination).
        """
        # Create a "Bad" Traceability
        bad_trace_file = os.path.join(self.tmpdir, "bad_trace.json")
        bad_data = {
            "nodes": [{"id": "NODE_A"}, {"id": "NODE_B"}, {"id": "NODE_C"}, {"id": "GHOST_NODE"}],
            "edges": []
        }
        with open(bad_trace_file, "w") as f:
            json.dump(bad_data, f)
            
        scanner = IndependentDelta1Scanner(self.delta1_dir)
        gt = scanner.scan()
        
        extractor = TraceabilityClaimExtractor([bad_trace_file])
        claims = extractor.extract()
        
        reconciler = TraceabilityReconciler()
        report = reconciler.reconcile(gt, claims)
        
        assert report.is_consistent is False
        assert "GHOST_NODE" in report.nodes_only_in_claim
        assert "GHOST_NODE" not in report.nodes_only_in_gt
        assert report.claimed_node_count == 4
        assert report.gt_unique_node_count == 3

    def test_scanner_ignores_traceability_directory(self):
        """
        Explicitly verify that Scanner does NOT scan the traceability directory.
        We place a "Trap" file in the traceability dir and ensure GT count doesn't change.
        """
        # Place a file in traceability dir that looks like a delta1 file
        trap_file = os.path.join(self.traceability_dir, "fake_delta1.json")
        with open(trap_file, "w") as f:
            json.dump({"nodes": [{"id": "TRAP_NODE"}], "edges": []}, f)
            
        scanner = IndependentDelta1Scanner(self.delta1_dir) # Scanning ONLY delta1_dir
        gt = scanner.scan()
        
        # GT should NOT contain TRAP_NODE
        assert "TRAP_NODE" not in gt.unique_node_ids
        assert gt.unique_node_count == 3 # Still A, B, C
