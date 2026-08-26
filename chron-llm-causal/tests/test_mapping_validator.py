"""Unit tests for MappingValidator."""

import json
from pathlib import Path
import pytest
from causal_kernel.kernel.validator.mapping_validator import MappingValidator


@pytest.fixture(scope="module")
def audit_traceability():
    path = Path("data/audit/delta1_delta2_traceability_v1.json")
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def test_valid_audit_mapping_structures(audit_traceability):
    """正常系: 既存 audit traceability アーティファクト (classification 構造) の検証"""
    if not audit_traceability:
        pytest.skip("Audit traceability artifact v1 not found")

    validator = MappingValidator()
    result = validator.validate(audit_traceability)
    assert result.is_valid, f"Expected PASS, got errors: {result.errors}"


def test_one_to_n_mapping_allowed():
    """正常系: 1:N (同一 Source ID が異なる Target ID にマッピング) の正当な受け入れ"""
    validator = MappingValidator()
    data = {
        "node_mappings": [
            {
                "source_delta1_id": "D1_NODE_001",
                "target_delta2_id": "D2_A",
                "classification": "PRESERVED",
                "evidence": "Ref A",
            },
            {
                "source_delta1_id": "D1_NODE_001",
                "target_delta2_id": "D2_B",
                "classification": "PRESERVED",
                "evidence": "Ref B",
            },
        ]
    }
    result = validator.validate(data)
    assert result.is_valid, f"1:N mapping should be allowed, got errors: {result.errors}"


def test_duplicate_pair_mapping_rejection():
    """異常系: 同一 (source, target) ペアの二重登録拒否"""
    validator = MappingValidator()
    data = {
        "node_mappings": [
            {
                "source_delta1_id": "D1_NODE_001",
                "target_delta2_id": "D2_A",
                "classification": "PRESERVED",
                "evidence": "Ref 1",
            },
            {
                "source_delta1_id": "D1_NODE_001",
                "target_delta2_id": "D2_A",
                "classification": "PRESERVED",
                "evidence": "Ref 2 duplicate",
            },
        ]
    }
    result = validator.validate(data)
    assert not result.is_valid
    assert any("duplicate mapping relationship" in err for err in result.errors)


def test_missing_target_on_resolved_status():
    """異常系: RESOLVED (PRESERVED) なのに target_id が欠損しているケース"""
    validator = MappingValidator()
    data = {
        "node_mappings": [
            {
                "source_delta1_id": "D1_NODE_001",
                "classification": "PRESERVED",
                "evidence": "Mapped directly in spec",
            }
        ]
    }
    result = validator.validate(data)
    assert not result.is_valid
    assert any("requires a valid target Delta2 ID" in err for err in result.errors)


def test_unresolved_explicit_preservation():
    """正常系: UNRESOLVED ステータスで target_id なし、evidence ありの正常保存"""
    validator = MappingValidator()
    data = {
        "node_mappings": [
            {
                "source_delta1_id": "D1_NODE_ORPHAN",
                "classification": "UNRESOLVED",
                "evidence": "No corresponding abstraction found in Delta2",
            }
        ]
    }
    result = validator.validate(data)
    assert result.is_valid


def test_e0_verified_contradiction():
    """異常系: E0 エビデンス強度で VERIFIED 状態となっている矛盾の検出"""
    validator = MappingValidator()
    data = {
        "node_mappings": [
            {
                "source_delta1_id": "D1_NODE_001",
                "target_delta2_id": "D2_A",
                "classification": "PRESERVED",
                "evidence": "Hypothetical link",
                "evidence_strength": "E0",
                "verification_status": "VERIFIED",
            }
        ]
    }
    result = validator.validate(data)
    assert not result.is_valid
    assert any("cannot be VERIFIED with E0" in err for err in result.errors)