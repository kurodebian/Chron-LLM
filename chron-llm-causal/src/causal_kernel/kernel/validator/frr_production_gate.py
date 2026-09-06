from typing import Any, Dict, Set

from cryptography.hazmat.primitives.asymmetric import ed25519

# Root 直下の既存基準実装からインポート (H-2 にて同パッケージへ移設予定)
from .frr_integrity_validator import (
    CanonicalTargetUniverse,
    FRRIntegrityValidator,
    GlobalIntegrityReport,
)
from .exceptions import FRRIntegrityException


class FRRProductionGate:
    """
    FRR Production Gate.

    Responsibilities:
    - trusted dependency injection
    - delegation to FRRIntegrityValidator
    - fail-closed enforcement

    Non-responsibilities:
    - schema validation
    - cryptographic verification
    - semantic conflict detection
    - pattern overlap detection
    - target/evidence validation
    """

    def __init__(
        self,
        target_universe: CanonicalTargetUniverse,
        verification_key: ed25519.Ed25519PublicKey,
        known_evidence_ids: Set[str],
    ) -> None:
        self.validator = FRRIntegrityValidator(
            target_universe=target_universe,
            verification_key=verification_key,
            known_evidence_ids=known_evidence_ids,
        )

    def enforce(
        self,
        package_payload: Dict[str, Any],
    ) -> GlobalIntegrityReport:
        report = self.validator.validate_ruleset_package(package_payload)

        if report.status != "PASS" or report.has_fatal_errors():
            raise FRRIntegrityException(
                "FRR Production Gate rejected ruleset package: "
                f"status={report.status}, fatal_errors={report.has_fatal_errors()}, "
                f"violations={report.violations}"
            )

        return report