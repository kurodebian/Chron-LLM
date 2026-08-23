"""
t1_differential_adapter.py — Canonical Outcome Adapter (Synchronized with INVALID_CONTEXT)
"""

from typing import NamedTuple, Optional
from enum import Enum, auto
from step0_ssot import ClaimType, ParseStatus


class UnifiedStatus(Enum):
    VALID_CLAIM = auto()
    BLANK_LINE = auto()
    COMMENT_LINE = auto()
    NOT_A_CANDIDATE = auto()
    INVALID_CONTEXT = auto()
    INVALID_GRAMMAR = auto()


class CanonicalParseOutcome(NamedTuple):
    status: UnifiedStatus
    claim_type: Optional[ClaimType]
    target: Optional[str]


class DifferentialAdapter:
    @staticmethod
    def _map_status(status: ParseStatus) -> UnifiedStatus:
        mapping = {
            ParseStatus.VALID_CLAIM: UnifiedStatus.VALID_CLAIM,
            ParseStatus.BLANK_LINE: UnifiedStatus.BLANK_LINE,
            ParseStatus.COMMENT_LINE: UnifiedStatus.COMMENT_LINE,
            ParseStatus.NOT_A_CANDIDATE: UnifiedStatus.NOT_A_CANDIDATE,
            ParseStatus.INVALID_CONTEXT: UnifiedStatus.INVALID_CONTEXT,
            ParseStatus.INVALID_GRAMMAR: UnifiedStatus.INVALID_GRAMMAR,
        }
        return mapping[status]

    @classmethod
    def adapt_reference(cls, ref_result) -> CanonicalParseOutcome:
        status = cls._map_status(ref_result.status)
        if ref_result.ast is not None:
            return CanonicalParseOutcome(
                status=status,
                claim_type=ref_result.ast.claim_type,
                target=ref_result.ast.target_id
            )
        return CanonicalParseOutcome(status=status, claim_type=None, target=None)

    @classmethod
    def adapt_production(cls, prod_result) -> CanonicalParseOutcome:
        status = cls._map_status(prod_result.status)
        return CanonicalParseOutcome(
            status=status,
            claim_type=prod_result.claim_type,
            target=prod_result.target
        )