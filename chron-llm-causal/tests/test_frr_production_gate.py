from unittest.mock import MagicMock
import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519

from causal_kernel.kernel.validator.exceptions import FRRIntegrityException
from causal_kernel.kernel.validator.frr_production_gate import FRRProductionGate
from causal_kernel.kernel.validator.frr_integrity_validator import CanonicalTargetUniverse


def test_gate_init_propagates_trusted_di():
    """信頼された 3 依存 (TargetUniverse, VerificationKey, EvidenceIDs) が正確に Validator に渡ることを確認。"""
    mock_universe = MagicMock(spec=CanonicalTargetUniverse)
    mock_key = MagicMock(spec=ed25519.Ed25519PublicKey)
    mock_evidences = {"EVID-001", "EVID-002"}

    gate = FRRProductionGate(
        target_universe=mock_universe,
        verification_key=mock_key,
        known_evidence_ids=mock_evidences,
    )

    assert gate.validator.target_universe is mock_universe
    assert gate.validator.verification_key is mock_key
    assert gate.validator.known_evidence_ids == mock_evidences


def test_enforce_allows_valid_package():
    """Validator が PASS かつ fatal error なしの場合は Report を返し透過すること。"""
    mock_universe = MagicMock(spec=CanonicalTargetUniverse)
    mock_key = MagicMock(spec=ed25519.Ed25519PublicKey)
    gate = FRRProductionGate(mock_universe, mock_key, set())

    mock_report = MagicMock()
    mock_report.status = "PASS"
    mock_report.has_fatal_errors.return_value = False
    mock_report.violations = []

    gate.validator.validate_ruleset_package = MagicMock(return_value=mock_report)
    payload = {"rules": []}

    result = gate.enforce(payload)

    assert result is mock_report
    gate.validator.validate_ruleset_package.assert_called_once_with(payload)


def test_enforce_rejects_non_pass_status():
    """FAIL / UNAVAILABLE などの非 PASS ステータスで即座に例外を投げること。"""
    mock_universe = MagicMock(spec=CanonicalTargetUniverse)
    mock_key = MagicMock(spec=ed25519.Ed25519PublicKey)
    gate = FRRProductionGate(mock_universe, mock_key, set())

    mock_report = MagicMock()
    mock_report.status = "FAIL"
    mock_report.has_fatal_errors.return_value = False
    mock_report.violations = [{"code": "ERR_SIGNATURE"}]

    gate.validator.validate_ruleset_package = MagicMock(return_value=mock_report)

    with pytest.raises(FRRIntegrityException) as exc_info:
        gate.enforce({"rules": []})

    assert "FRR Production Gate rejected ruleset package" in str(exc_info.value)


def test_enforce_rejects_fatal_errors():
    """status == PASS であっても has_fatal_errors() が True の場合は拒否すること。"""
    mock_universe = MagicMock(spec=CanonicalTargetUniverse)
    mock_key = MagicMock(spec=ed25519.Ed25519PublicKey)
    gate = FRRProductionGate(mock_universe, mock_key, set())

    mock_report = MagicMock()
    mock_report.status = "PASS"
    mock_report.has_fatal_errors.return_value = True
    mock_report.violations = [{"code": "ERR_FATAL"}]

    gate.validator.validate_ruleset_package = MagicMock(return_value=mock_report)

    with pytest.raises(FRRIntegrityException):
        gate.enforce({"rules": []})