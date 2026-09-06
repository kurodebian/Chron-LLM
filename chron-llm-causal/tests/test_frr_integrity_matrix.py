"""
FRR Global Integrity Validator v1.2
30-Case Comprehensive Test Suite

Covers:
    FR-INV-01  Schema & Structural Integrity
    FR-INV-02  Cryptographic Integrity & Tamper Proof
    FR-INV-03a Unique rule_id
    FR-INV-03b Semantic Key uniqueness
    FR-INV-04  Single-Domain Target Conflict
    FR-INV-05  Relation Normalization Conflict
    FR-INV-06  Deterministic Pattern Overlap
    FR-INV-07  Target Universe existence
    FR-INV-08  Target entity type compatibility
    FR-INV-09  Inter-Table Target Collision
    FR-INV-10  Evidence reference integrity

This suite is aligned with the strict v1.2 contract:

    rule_type:
        ALIAS
        TRANSFORM
        RELATION_NORMALIZATION
        SPEC_BINDING
        AUTHORITY

    source_type:
        NODE
        EDGE
        SPEC
        AUTHORITY

Cryptographic contract:

    ruleset_hash =
        SHA256(JCS(rules))

    signature =
        Ed25519.Sign(
            JCS({
                "ruleset_hash": ...,
                "integrity": {
                    "algorithm": "Ed25519"
                },
                "rules": [...]
            })
        )

Signature representation:
    lowercase/uppercase hexadecimal accepted by schema.
"""


import hashlib
import unittest

import rfc8785
from cryptography.hazmat.primitives.asymmetric import ed25519

from causal_kernel.kernel.validator.frr_integrity_validator import (
    FRRIntegrityValidator,
    CanonicalTargetUniverse,
    IntegritySeverity,
    check_pattern_overlap,
)


class TestFRRIntegrityMatrix(unittest.TestCase):

    # ==================================================================
    # Fixture
    # ==================================================================

    def setUp(self):
        self.priv_key = ed25519.Ed25519PrivateKey.generate()
        self.pub_key = self.priv_key.public_key()

        self.universe = CanonicalTargetUniverse(
            node_ids={
                "NODE_A",
                "NODE_B",
                "NODE_C",
            },
            edge_ids={
                "EDGE_X",
                "EDGE_Y",
            },
            spec_ids={
                "SPEC_1",
                "SPEC_2",
            },
            authority_ids={
                "AUTH_1",
                "AUTH_2",
            },
        )

        self.evidence_store = {
            "EV_01",
            "EV_02",
            "EV_03",
        }

        self.validator = FRRIntegrityValidator(
            target_universe=self.universe,
            verification_key=self.pub_key,
            known_evidence_ids=self.evidence_store,
        )

    # ==================================================================
    # Package construction
    # ==================================================================

    def _build_signed_package(
        self,
        rules: list,
        custom_key=None,
    ) -> dict:
        """
        Build a package according to FR-INV-02.

        Hash:
            SHA256(JCS(rules))

        Signature:
            Ed25519 over JCS({
                ruleset_hash,
                integrity.algorithm,
                rules
            })

        Signature is encoded as hexadecimal, not Base64.
        """

        key = custom_key or self.priv_key

        rules_hash = hashlib.sha256(
            rfc8785.dumps(rules)
        ).hexdigest()

        signing_payload = {
            "ruleset_hash": rules_hash,
            "integrity": {
                "algorithm": "Ed25519",
            },
            "rules": rules,
        }

        signature_bytes = key.sign(
            rfc8785.dumps(signing_payload)
        )

        return {
            "ruleset_hash": rules_hash,
            "integrity": {
                "algorithm": "Ed25519",
                "signature": signature_bytes.hex(),
            },
            "rules": rules,
        }

    # ==================================================================
    # Rule construction
    # ==================================================================

    def _valid_rule(
        self,
        rid="R1",
        rule_type="ALIAS",
        source_type="NODE",
        comp="C1",
        target="NODE_A",
        pattern=None,
        scope=None,
        evidence=None,
    ):
        if pattern is None:
            pattern = {
                "type": "EXACT",
                "value": "VAL",
            }

        if scope is None:
            scope = {
                "scope_type": "ALL",
            }

        if evidence is None:
            evidence = [
                "EV_01",
            ]

        return {
            "rule_id": rid,
            "rule_type": rule_type,
            "source_type": source_type,
            "component_id": comp,
            "record_scope": scope,
            "normalized_pattern": pattern,
            "target_id": target,
            "evidence_ref": evidence,
        }

    # ==================================================================
    # Helpers
    # ==================================================================

    @staticmethod
    def _has_violation(rep, invariant_id):
        return any(
            v.invariant_id == invariant_id
            for v in rep.violations
        )

    @staticmethod
    def _has_unavailable(rep, invariant_id):
        return any(
            v.invariant_id == invariant_id
            and v.severity == IntegritySeverity.UNAVAILABLE
            for v in rep.violations
        )

    # ==================================================================
    # 01-04 : FR-INV-01
    # ==================================================================

    def test_T_FRR_01_malformed_package_non_dict(self):
        rep = self.validator.validate_ruleset_package(
            "not_a_dict"
        )

        self.assertEqual(
            rep.status,
            "FAIL",
        )

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-01",
            )
        )

    def test_T_FRR_02_malformed_rule_non_dict(self):
        pkg = self._build_signed_package(
            ["string_rule"]
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertEqual(
            rep.status,
            "FAIL",
        )

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-01",
            )
        )

    def test_T_FRR_03_missing_required_field(self):
        rule = self._valid_rule()

        del rule["component_id"]

        pkg = self._build_signed_package(
            [rule]
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertEqual(
            rep.status,
            "FAIL",
        )

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-01",
            )
        )

    def test_T_FRR_04_invalid_source_type_rejected(self):
        rule = self._valid_rule()

        rule["source_type"] = "ALIAS"

        pkg = self._build_signed_package(
            [rule]
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertEqual(
            rep.status,
            "FAIL",
        )

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-01",
            )
        )

    # ==================================================================
    # 05-10 : FR-INV-02
    # ==================================================================

    def test_T_FRR_05_hash_mismatch(self):
        pkg = self._build_signed_package(
            [self._valid_rule()]
        )

        pkg["ruleset_hash"] = "a" * 64

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertEqual(
            rep.status,
            "FAIL",
        )

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-02",
            )
        )

    def test_T_FRR_06_missing_hash(self):
        pkg = self._build_signed_package(
            [self._valid_rule()]
        )

        del pkg["ruleset_hash"]

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertEqual(
            rep.status,
            "FAIL",
        )

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-01",
            )
        )

    def test_T_FRR_07_invalid_signature(self):
        pkg = self._build_signed_package(
            [self._valid_rule()]
        )

        pkg["integrity"]["signature"] = "00" * 64

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertEqual(
            rep.status,
            "FAIL",
        )

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-02",
            )
        )

    def test_T_FRR_08_missing_signature(self):
        pkg = self._build_signed_package(
            [self._valid_rule()]
        )

        del pkg["integrity"]["signature"]

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertEqual(
            rep.status,
            "FAIL",
        )

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-01",
            )
        )

    def test_T_FRR_09_missing_verification_key_fail_closed(self):
        validator = FRRIntegrityValidator(
            target_universe=self.universe,
            verification_key=None,
            known_evidence_ids=self.evidence_store,
        )

        pkg = self._build_signed_package(
            [self._valid_rule()]
        )

        rep = validator.validate_ruleset_package(pkg)

        self.assertEqual(
            rep.status,
            "FAIL",
        )

        self.assertTrue(
            self._has_unavailable(
                rep,
                "FR-INV-02",
            )
        )

    def test_T_FRR_10_wrong_public_key(self):
        other_priv = (
            ed25519.Ed25519PrivateKey.generate()
        )

        pkg = self._build_signed_package(
            [self._valid_rule()],
            custom_key=other_priv,
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertEqual(
            rep.status,
            "FAIL",
        )

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-02",
            )
        )

    # ==================================================================
    # 11-12 : FR-INV-03a / FR-INV-03b
    # ==================================================================

    def test_T_FRR_11_duplicate_rule_id(self):
        r1 = self._valid_rule(
            rid="R1",
            target="NODE_A",
        )

        r2 = self._valid_rule(
            rid="R1",
            target="NODE_B",
        )

        pkg = self._build_signed_package(
            [r1, r2]
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-03a",
            )
        )

    def test_T_FRR_12_semantic_redundancy(self):
        r1 = self._valid_rule(
            rid="R1"
        )

        r2 = self._valid_rule(
            rid="R2"
        )

        pkg = self._build_signed_package(
            [r1, r2]
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertTrue(
            any(
                v.invariant_id == "FR-INV-03b"
                and v.severity == IntegritySeverity.REDUNDANT
                for v in rep.violations
            )
        )

    # ==================================================================
    # 13-16 : FR-INV-04 / FR-INV-05 / FR-INV-06
    # ==================================================================

    def test_T_FRR_13_alias_conflict(self):
        r1 = self._valid_rule(
            rid="R1",
            rule_type="ALIAS",
            source_type="NODE",
            target="NODE_A",
        )

        r2 = self._valid_rule(
            rid="R2",
            rule_type="ALIAS",
            source_type="NODE",
            target="NODE_B",
        )

        pkg = self._build_signed_package(
            [r1, r2]
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-04",
            )
        )

    def test_T_FRR_14_relation_normalization_conflict(self):
        r1 = self._valid_rule(
            rid="R1",
            rule_type="RELATION_NORMALIZATION",
            source_type="EDGE",
            target="EDGE_X",
        )

        r2 = self._valid_rule(
            rid="R2",
            rule_type="RELATION_NORMALIZATION",
            source_type="EDGE",
            target="EDGE_Y",
        )

        pkg = self._build_signed_package(
            [r1, r2]
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-05",
            )
        )

    def test_T_FRR_15_exact_prefix_overlap_is_deterministic(self):
        exact = {
            "type": "EXACT",
            "value": "ABC_123",
        }

        prefix = {
            "type": "PREFIX",
            "prefix": "ABC_",
        }

        self.assertTrue(
            check_pattern_overlap(
                exact,
                prefix,
            )
        )

        self.assertTrue(
            check_pattern_overlap(
                prefix,
                exact,
            )
        )

    def test_T_FRR_16_exact_prefix_charset_overlap_is_deterministic(self):
        exact = {
            "type": "EXACT",
            "value": "ABX",
        }

        pc = {
            "type": "PREFIX_CHARSET",
            "prefix": "AB",
            "allowed_chars": ["X"],
            "min_suffix_len": 1,
        }

        self.assertTrue(
            check_pattern_overlap(
                exact,
                pc,
            )
        )

        self.assertTrue(
            check_pattern_overlap(
                pc,
                exact,
            )
        )

    # ==================================================================
    # 17-20 : Critical PREFIX_CHARSET boundaries
    # ==================================================================

    def test_T_FRR_17_prefix_longer_than_pc_disallowed_next_char(self):
        """
        Critical boundary:

            PREFIX("abcd")
            PREFIX_CHARSET("ab", {"x"})

        The fixed next character is "c", which is not allowed.

        Therefore intersection MUST be empty.
        """

        prefix = {
            "type": "PREFIX",
            "prefix": "abcd",
        }

        pc = {
            "type": "PREFIX_CHARSET",
            "prefix": "ab",
            "allowed_chars": ["x"],
            "min_suffix_len": 1,
        }

        self.assertFalse(
            check_pattern_overlap(
                prefix,
                pc,
            )
        )

        self.assertFalse(
            check_pattern_overlap(
                pc,
                prefix,
            )
        )

    def test_T_FRR_18_prefix_longer_than_pc_allowed_next_char(self):
        prefix = {
            "type": "PREFIX",
            "prefix": "abcd",
        }

        pc = {
            "type": "PREFIX_CHARSET",
            "prefix": "ab",
            "allowed_chars": ["c"],
            "min_suffix_len": 1,
        }

        self.assertTrue(
            check_pattern_overlap(
                prefix,
                pc,
            )
        )

        self.assertTrue(
            check_pattern_overlap(
                pc,
                prefix,
            )
        )

    def test_T_FRR_19_pc_pc_nested_prefix_disallowed_extension(self):
        pc1 = {
            "type": "PREFIX_CHARSET",
            "prefix": "ab",
            "allowed_chars": ["x"],
            "min_suffix_len": 1,
        }

        pc2 = {
            "type": "PREFIX_CHARSET",
            "prefix": "abc",
            "allowed_chars": ["y"],
            "min_suffix_len": 1,
        }

        self.assertFalse(
            check_pattern_overlap(
                pc1,
                pc2,
            )
        )

        self.assertFalse(
            check_pattern_overlap(
                pc2,
                pc1,
            )
        )

    def test_T_FRR_20_pc_pc_equal_prefix_charset_intersection(self):
        pc1 = {
            "type": "PREFIX_CHARSET",
            "prefix": "P_",
            "allowed_chars": ["A", "B"],
            "min_suffix_len": 1,
        }

        pc2 = {
            "type": "PREFIX_CHARSET",
            "prefix": "P_",
            "allowed_chars": ["B", "C"],
            "min_suffix_len": 1,
        }

        self.assertTrue(
            check_pattern_overlap(
                pc1,
                pc2,
            )
        )

        self.assertTrue(
            check_pattern_overlap(
                pc2,
                pc1,
            )
        )

    # ==================================================================
    # 21-23 : FR-INV-09
    # ==================================================================

    def test_T_FRR_21_alias_transform_cross_table_collision(self):
        r1 = self._valid_rule(
            rid="R1",
            rule_type="ALIAS",
            source_type="NODE",
            target="NODE_A",
        )

        r2 = self._valid_rule(
            rid="R2",
            rule_type="TRANSFORM",
            source_type="NODE",
            target="NODE_B",
        )

        pkg = self._build_signed_package(
            [r1, r2]
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-09",
            )
        )

    def test_T_FRR_22_alias_spec_binding_cross_table_collision(self):
        r1 = self._valid_rule(
            rid="R1",
            rule_type="ALIAS",
            source_type="NODE",
            target="NODE_A",
        )

        r2 = self._valid_rule(
            rid="R2",
            rule_type="SPEC_BINDING",
            source_type="SPEC",
            target="SPEC_1",
        )

        pkg = self._build_signed_package(
            [r1, r2]
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-09",
            )
        )

    def test_T_FRR_23_same_target_different_rule_type_is_still_collision(self):
        """
        Normative FR-INV-09 boundary:

        Different rule_type is invalid even when the typed target
        identity is identical.
        """

        r1 = self._valid_rule(
            rid="R1",
            rule_type="ALIAS",
            source_type="NODE",
            target="NODE_A",
        )

        r2 = self._valid_rule(
            rid="R2",
            rule_type="TRANSFORM",
            source_type="NODE",
            target="NODE_A",
        )

        pkg = self._build_signed_package(
            [r1, r2]
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-09",
            )
        )

    # ==================================================================
    # 24-27 : FR-INV-07 / FR-INV-08 / FR-INV-10
    # ==================================================================

    def test_T_FRR_24_nonexistent_canonical_target(self):
        rule = self._valid_rule(
            target="NON_EXISTENT_TARGET"
        )

        pkg = self._build_signed_package(
            [rule]
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-07",
            )
        )

    def test_T_FRR_25_node_to_edge_type_violation(self):
        rule = self._valid_rule(
            source_type="NODE",
            target="EDGE_X",
        )

        pkg = self._build_signed_package(
            [rule]
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-08",
            )
        )

    def test_T_FRR_26_edge_to_node_type_violation(self):
        rule = self._valid_rule(
            rule_type="RELATION_NORMALIZATION",
            source_type="EDGE",
            target="NODE_A",
        )

        pkg = self._build_signed_package(
            [rule]
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-08",
            )
        )

    def test_T_FRR_27_nonexistent_evidence(self):
        rule = self._valid_rule(
            evidence=["NON_EXISTENT_EV"]
        )

        pkg = self._build_signed_package(
            [rule]
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertTrue(
            self._has_violation(
                rep,
                "FR-INV-10",
            )
        )

    # ==================================================================
    # 28 : Fail-closed dependency
    # ==================================================================

    def test_T_FRR_28_unregistered_target_universe_unavailable(self):
        validator = FRRIntegrityValidator(
            target_universe=None,
            verification_key=self.pub_key,
            known_evidence_ids=self.evidence_store,
        )

        pkg = self._build_signed_package(
            [self._valid_rule()]
        )

        rep = validator.validate_ruleset_package(pkg)

        self.assertEqual(
            rep.status,
            "FAIL",
        )

        self.assertTrue(
            any(
                v.severity == IntegritySeverity.UNAVAILABLE
                and v.invariant_id == "FR-INV-07"
                for v in rep.violations
            )
        )

    # ==================================================================
    # 29-30 : Positive execution contracts
    # ==================================================================

    def test_T_FRR_29_valid_complete_package_pass(self):
        r1 = self._valid_rule(
            rid="R1",
            rule_type="ALIAS",
            source_type="NODE",
            comp="C1",
            target="NODE_A",
        )

        r2 = self._valid_rule(
            rid="R2",
            rule_type="ALIAS",
            source_type="NODE",
            comp="C2",
            target="NODE_B",
        )

        pkg = self._build_signed_package(
            [r1, r2]
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertEqual(
            rep.status,
            "PASS",
        )

        self.assertEqual(
            rep.total_rules_scanned,
            2,
        )

        self.assertEqual(
            rep.schema_valid_rules_count,
            2,
        )

        self.assertEqual(
            rep.integrity_valid_rules_count,
            2,
        )

    def test_T_FRR_30_valid_spec_binding_and_authority_pass(self):
        r1 = self._valid_rule(
            rid="R1",
            rule_type="SPEC_BINDING",
            source_type="SPEC",
            comp="C1",
            target="SPEC_1",
        )

        r2 = self._valid_rule(
            rid="R2",
            rule_type="AUTHORITY",
            source_type="AUTHORITY",
            comp="C2",
            target="AUTH_1",
        )

        pkg = self._build_signed_package(
            [r1, r2]
        )

        rep = self.validator.validate_ruleset_package(pkg)

        self.assertEqual(
            rep.status,
            "PASS",
        )

        self.assertEqual(
            rep.total_rules_scanned,
            2,
        )

        self.assertEqual(
            rep.schema_valid_rules_count,
            2,
        )

        self.assertEqual(
            rep.integrity_valid_rules_count,
            2,
        )


if __name__ == "__main__":
    unittest.main()