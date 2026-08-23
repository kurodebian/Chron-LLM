"""
step0_ssot.py — STEP 0: Single Source of Truth (SSOT) Definitions (Fixed)
"""

from enum import Enum, auto


class ParseStatus(Enum):
    VALID_CLAIM = auto()
    BLANK_LINE = auto()
    COMMENT_LINE = auto()
    NOT_A_CANDIDATE = auto()
    INVALID_CONTEXT = auto()  # P3 Context Domain Guard Failure
    INVALID_GRAMMAR = auto()  # PhysicalLine or P4 Syntax Failure


class ClaimType(Enum):
    UNIT = auto()
    REQUIRES = auto()
    DEPENDS_ON = auto()