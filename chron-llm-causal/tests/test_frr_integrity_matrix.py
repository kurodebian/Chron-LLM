"""
30-Case Comprehensive Test Suite for FRR Global Integrity Invariants
Covers All Invariants (FR-INV-01 .. FR-INV-10), Fail-Closed Conditions,
5-Table Cross-Consistency, Pattern Overlaps, and Cryptographic Strictness.
"""

import unittest
import hashlib
import base64
import rfc8785
from cryptography.hazmat.primitives.asymmetric import ed25519

from frr_integrity_validator import (
    FRRIntegrityValidator, CanonicalTargetUniverse, IntegritySeverity
)


class TestFRRIntegrityMatrix(unittest.TestCase):
    def setUp(self):
        self.priv_key = ed25519.Ed25519PrivateKey.generate()
        self.pub_key = self.priv_key.public_key()
        self.universe = CanonicalTargetUniverse(
            node_ids={"NODE_A", "NODE_B", "NODE_C"},
            edge_ids={"EDGE_X", "EDGE_Y"},
            spec_ids={"SPEC_1"},
            authority_ids={"AUTH_1"}
        )
        self.evidence_store = {"EV_01", "EV_02"}
        self.validator = FRRIntegrityValidator(
            target_universe=self.universe,
            verification_key=self.pub_key,
            known_evidence_ids=self.evidence_store
        )

    def _build_signed_package(self, rules: list, custom_key=None) -> dict:
        key = custom_key or self.priv_key
        pkg = {"rules": rules}
        canonical_bytes = rfc8785.dumps(pkg)
        digest = hashlib.sha256(canonical_bytes).digest()
        sig_bytes = key.sign(digest)
        
        pkg["ruleset_hash"] = hashlib.sha256(canonical_bytes).hexdigest()
        pkg["integrity"] = {
            "algorithm": "Ed25519",
            "signature": base64.b64encode(sig_bytes).decode("ascii")
        }
        return pkg

    def _valid_rule(self, rid="R1", stype="NODE", comp="C1", target="NODE_A"):
        return {
            "rule_id": rid, "source_type": stype, "component_id": comp,
            "record_scope": {"scope_type": "ALL"},
            "normalized_pattern": {"type": "EXACT", "value": "VAL"},
            "target_id": target, "evidence_ref": "EV_01"
        }

    # --- 1. Schema & Package Structural Failures (FR-INV-01) ---
    def test_T_FRR_01_malformed_package_non_dict(self):
        rep = self.validator.validate_ruleset_package("not_a_dict")
        self.assertEqual(rep.status, "FAIL")

    def test_T_FRR_02_malformed_rule_non_dict(self):
        pkg = self._build_signed_package(["string_rule"])
        rep = self.validator.validate_ruleset_package(pkg)
        self.assertTrue(any(v.invariant_id == "FR-INV-01" for v in rep.violations))

    def test_T_FRR_03_missing_required_field(self):
        r = self._valid_rule()
        del r["component_id"]
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r]))
        self.assertEqual(rep.status, "FAIL")

    def test_T_FRR_29_duplicate_record_indices_rejected_by_schema(self):
        r = self._valid_rule()
        r["record_scope"] = {"scope_type": "EXACT_RECORD_INDICES", "record_indices": [1, 1]}
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r]))
        self.assertTrue(any(v.invariant_id == "FR-INV-01" for v in rep.violations))

    # --- 2. Cryptographic Integrity Checks (FR-INV-02) ---
    def test_T_FRR_17_hash_mismatch(self):
        pkg = self._build_signed_package([self._valid_rule()])
        pkg["ruleset_hash"] = "a" * 64
        rep = self.validator.validate_ruleset_package(pkg)
        self.assertTrue(any(v.invariant_id == "FR-INV-02" for v in rep.violations))

    def test_T_FRR_18_missing_hash(self):
        pkg = self._build_signed_package([self._valid_rule()])
        del pkg["ruleset_hash"]
        rep = self.validator.validate_ruleset_package(pkg)
        self.assertEqual(rep.status, "FAIL")

    def test_T_FRR_19_invalid_signature(self):
        pkg = self._build_signed_package([self._valid_rule()])
        pkg["integrity"]["signature"] = base64.b64encode(b"invalid_sig_bytes_32_len_test!!").decode()
        rep = self.validator.validate_ruleset_package(pkg)
        self.assertTrue(any(v.invariant_id == "FR-INV-02" for v in rep.violations))

    def test_T_FRR_20_missing_signature(self):
        pkg = self._build_signed_package([self._valid_rule()])
        del pkg["integrity"]
        rep = self.validator.validate_ruleset_package(pkg)
        self.assertEqual(rep.status, "FAIL")

    def test_T_FRR_21_missing_verification_key_fail_closed(self):
        val = FRRIntegrityValidator(target_universe=self.universe, verification_key=None, known_evidence_ids=self.evidence_store)
        rep = val.validate_ruleset_package(self._build_signed_package([self._valid_rule()]))
        self.assertTrue(any(v.severity == IntegritySeverity.UNAVAILABLE and v.invariant_id == "FR-INV-02" for v in rep.violations))

    def test_T_FRR_22_wrong_public_key(self):
        other_priv = ed25519.Ed25519PrivateKey.generate()
        pkg = self._build_signed_package([self._valid_rule()], custom_key=other_priv)
        rep = self.validator.validate_ruleset_package(pkg)
        self.assertTrue(any(v.invariant_id == "FR-INV-02" for v in rep.violations))

    def test_T_FRR_23_tampered_payload_hash_valid_sig_invalid(self):
        pkg = self._build_signed_package([self._valid_rule()])
        pkg["rules"][0]["component_id"] = "TAMPERED"
        rep = self.validator.validate_ruleset_package(pkg)
        self.assertTrue(any(v.invariant_id == "FR-INV-02" for v in rep.violations))

    # --- 3. Rule ID & Semantic Redundancy (FR-INV-03a, FR-INV-03b) ---
    def test_T_FRR_04_duplicate_rule_id(self):
        r1, r2 = self._valid_rule("R1"), self._valid_rule("R1")
        r2["target_id"] = "NODE_B"
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r1, r2]))
        self.assertTrue(any(v.invariant_id == "FR-INV-03a" for v in rep.violations))

    def test_T_FRR_05_semantic_redundancy(self):
        r1, r2 = self._valid_rule("R1"), self._valid_rule("R2")
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r1, r2]))
        self.assertTrue(any(v.invariant_id == "FR-INV-03b" and v.severity == IntegritySeverity.REDUNDANT for v in rep.violations))

    # --- 4. Conflict & Overlap Invariants (FR-INV-04, 05, 06) ---
    def test_T_FRR_06_alias_conflict(self):
        r1 = self._valid_rule("R1", stype="ALIAS", target="NODE_A")
        r2 = self._valid_rule("R2", stype="ALIAS", target="NODE_B")
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r1, r2]))
        self.assertTrue(any(v.invariant_id == "FR-INV-04" for v in rep.violations))

    def test_T_FRR_15_relation_normalization_conflict(self):
        r1 = self._valid_rule("R1", stype="RELATION_NORMALIZATION", target="EDGE_X")
        r2 = self._valid_rule("R2", stype="RELATION_NORMALIZATION", target="EDGE_Y")
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r1, r2]))
        self.assertTrue(any(v.invariant_id == "FR-INV-05" for v in rep.violations))

    def test_T_FRR_08_scope_pattern_overlap_conflict(self):
        r1 = self._valid_rule("R1", target="NODE_A")
        r2 = self._valid_rule("R2", target="NODE_B")
        r2["record_scope"] = {"scope_type": "EXACT_RECORD_INDICES", "record_indices": [10]}
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r1, r2]))
        self.assertTrue(any(v.invariant_id == "FR-INV-06" for v in rep.violations))

    def test_T_FRR_24_exact_prefix_pattern_overlap(self):
        r1 = self._valid_rule("R1", target="NODE_A")
        r1["normalized_pattern"] = {"type": "EXACT", "value": "ABC_123"}
        r2 = self._valid_rule("R2", target="NODE_B")
        r2["normalized_pattern"] = {"type": "PREFIX", "prefix": "ABC_"}
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r1, r2]))
        self.assertTrue(any(v.invariant_id == "FR-INV-06" for v in rep.violations))

    def test_T_FRR_26_prefix_charset_pattern_disjoint_no_overlap(self):
        r1 = self._valid_rule("R1", target="NODE_A")
        r1["normalized_pattern"] = {"type": "PREFIX_CHARSET", "prefix": "P_", "allowed_chars": ["A", "B"], "min_suffix_len": 1}
        r2 = self._valid_rule("R2", target="NODE_B")
        r2["normalized_pattern"] = {"type": "PREFIX_CHARSET", "prefix": "P_", "allowed_chars": ["X", "Y"], "min_suffix_len": 1}
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r1, r2]))
        self.assertFalse(any(v.invariant_id == "FR-INV-06" for v in rep.violations))

    def test_T_FRR_30_exact_suffix_pattern_overlap(self):
        r1 = self._valid_rule("R1", target="NODE_A")
        r1["normalized_pattern"] = {"type": "EXACT", "value": "ITEM_XYZ"}
        r2 = self._valid_rule("R2", target="NODE_B")
        r2["normalized_pattern"] = {"type": "SUFFIX", "suffix": "XYZ"}
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r1, r2]))
        self.assertTrue(any(v.invariant_id == "FR-INV-06" for v in rep.violations))

    # --- 5. Inter-Table 5-System Consistency (FR-INV-09) ---
    def test_T_FRR_12_inter_table_alias_transform_conflict(self):
        r1 = self._valid_rule("R1", stype="ALIAS", target="NODE_A")
        r2 = self._valid_rule("R2", stype="TRANSFORM", target="NODE_B")
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r1, r2]))
        self.assertTrue(any(v.invariant_id == "FR-INV-09" for v in rep.violations))

    def test_T_FRR_13_inter_table_alias_spec_binding_conflict(self):
        r1 = self._valid_rule("R1", stype="ALIAS", target="NODE_A")
        r2 = self._valid_rule("R2", stype="SPEC_BINDING", target="SPEC_1")
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r1, r2]))
        self.assertTrue(any(v.invariant_id == "FR-INV-09" for v in rep.violations))

    def test_T_FRR_14_inter_table_authority_transform_conflict(self):
        r1 = self._valid_rule("R1", stype="AUTHORITY", target="AUTH_1")
        r2 = self._valid_rule("R2", stype="TRANSFORM", target="NODE_A")
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r1, r2]))
        self.assertTrue(any(v.invariant_id == "FR-INV-09" for v in rep.violations))

    # --- 6. Universe Disambiguation & Evidence (FR-INV-07, FR-INV-08, FR-INV-10) ---
    def test_T_FRR_07_nonexistent_canonical_target(self):
        r = self._valid_rule(target="NON_EXISTENT_TARGET")
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r]))
        self.assertTrue(any(v.invariant_id == "FR-INV-07" for v in rep.violations))

    def test_T_FRR_09_type_separation_violation_node_to_edge(self):
        r = self._valid_rule(stype="NODE", target="EDGE_X")
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r]))
        self.assertTrue(any(v.invariant_id == "FR-INV-08" for v in rep.violations))

    def test_T_FRR_10_type_separation_violation_edge_to_node(self):
        r = self._valid_rule(stype="EDGE", target="NODE_A")
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r]))
        self.assertTrue(any(v.invariant_id == "FR-INV-08" for v in rep.violations))

    def test_T_FRR_11_spec_binding_type_violation(self):
        r = self._valid_rule(stype="SPEC_BINDING", target="NODE_A")
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r]))
        self.assertTrue(any(v.invariant_id == "FR-INV-08" for v in rep.violations))

    def test_T_FRR_16_nonexistent_evidence(self):
        r = self._valid_rule()
        r["evidence_ref"] = "NON_EXISTENT_EV"
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r]))
        self.assertTrue(any(v.invariant_id == "FR-INV-10" for v in rep.violations))

    def test_T_FRR_25_unregistered_universe_unavailable(self):
        val = FRRIntegrityValidator(target_universe=None, verification_key=self.pub_key, known_evidence_ids=self.evidence_store)
        rep = val.validate_ruleset_package(self._build_signed_package([self._valid_rule()]))
        self.assertTrue(any(v.severity == IntegritySeverity.UNAVAILABLE for v in rep.violations))

    # --- 7. Positive Execution Contracts ---
    def test_T_FRR_27_valid_complete_package_pass(self):
        r1 = self._valid_rule("R1", target="NODE_A")
        r2 = self._valid_rule("R2", comp="C2", target="NODE_B")
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r1, r2]))
        self.assertEqual(rep.status, "PASS")
        self.assertEqual(rep.integrity_valid_rules_count, 2)

    def test_T_FRR_28_valid_spec_binding_and_authority_pass(self):
        r1 = self._valid_rule("R1", stype="SPEC_BINDING", target="SPEC_1")
        r2 = self._valid_rule("R2", stype="AUTHORITY", comp="C2", target="AUTH_1")
        rep = self.validator.validate_ruleset_package(self._build_signed_package([r1, r2]))
        self.assertEqual(rep.status, "PASS")
        self.assertEqual(rep.integrity_valid_rules_count, 2)


if __name__ == "__main__":
    unittest.main()