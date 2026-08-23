"""
step2_production_parser.py — STEP 2: Production Parser with Immutable Trace Certificate (Fixed)
"""

import re
from typing import NamedTuple, Optional, Tuple, Any
from step0_ssot import ParseStatus, ClaimType

REGEX_ID_PATTERN = r"[A-Za-z0-9_]+(?:[.-][A-Za-z0-9_]+)*"
RE_STRICT_ID = re.compile(rf"\A{REGEX_ID_PATTERN}\Z")

RE_BLANK = re.compile(r"\A[ \t]*\Z")
RE_COMMENT = re.compile(r"\A[ \t]*#.*\Z")

RE_UNIT_CLAIM = re.compile(
    rf"\A[ \t]*unit[ \t]*:[ \t]*(?P<target>{REGEX_ID_PATTERN})[ \t]*\Z"
)
RE_REQUIRES_CLAIM = re.compile(
    rf"\A[ \t]*requires[ \t]*:[ \t]*(?P<target>{REGEX_ID_PATTERN})[ \t]*\Z"
)
RE_DEPENDS_ON_CLAIM = re.compile(
    rf"\A[ \t]*depends_on[ \t]*:[ \t]*(?P<target>{REGEX_ID_PATTERN})[ \t]*\Z"
)

RE_CANDIDATE_PREFIX = re.compile(r"\A[ \t]*(?:unit|requires|depends_on)[ \t]*:")


class ProductionParseResult(NamedTuple):
    status: ParseStatus
    claim_type: Optional[ClaimType]
    target: Optional[str]
    trace: Tuple[str, ...]  # Immutable Trace Certificate (Enforced Tuple)


class ProductionParser:
    @classmethod
    def validate_context_domain(cls, current_unit: Any) -> bool:
        if current_unit is None:
            return True
        if not isinstance(current_unit, str):
            return False
        return bool(RE_STRICT_ID.match(current_unit))

    @classmethod
    def parse_line(cls, line: str, current_unit: Any = None) -> ProductionParseResult:
        trace_list = []

        # 0. PhysicalLine Strict Guard
        if "\r" in line or "\n" in line:
            return ProductionParseResult(
                ParseStatus.INVALID_GRAMMAR, None, None, tuple(trace_list)
            )

        # P1: Blank / Comment Check
        trace_list.append("P1")
        if RE_BLANK.match(line):
            return ProductionParseResult(
                ParseStatus.BLANK_LINE, None, None, tuple(trace_list)
            )
        if RE_COMMENT.match(line):
            return ProductionParseResult(
                ParseStatus.COMMENT_LINE, None, None, tuple(trace_list)
            )

        # P2: Candidate Detection Check
        trace_list.append("P2")
        if not RE_CANDIDATE_PREFIX.match(line):
            return ProductionParseResult(
                ParseStatus.NOT_A_CANDIDATE, None, None, tuple(trace_list)
            )

        # P3: Context Domain Guard
        trace_list.append("P3")
        if not cls.validate_context_domain(current_unit):
            return ProductionParseResult(
                ParseStatus.INVALID_CONTEXT, None, None, tuple(trace_list)
            )

        # P4: Grammar Parse Evaluation
        trace_list.append("P4")
        claims_map = (
            (RE_UNIT_CLAIM, ClaimType.UNIT),
            (RE_REQUIRES_CLAIM, ClaimType.REQUIRES),
            (RE_DEPENDS_ON_CLAIM, ClaimType.DEPENDS_ON),
        )

        for pattern, claim_type in claims_map:
            match = pattern.match(line)
            if match:
                # P5: Typed Claim Construction
                trace_list.append("P5")
                return ProductionParseResult(
                    ParseStatus.VALID_CLAIM,
                    claim_type,
                    match.group("target"),
                    tuple(trace_list)
                )

        # Candidate prefix matched, but P4 grammar failed -> INVALID_GRAMMAR
        return ProductionParseResult(
            ParseStatus.INVALID_GRAMMAR, None, None, tuple(trace_list)
        )


def parse_production(line: str, current_unit: Any = None) -> ProductionParseResult:
    return ProductionParser.parse_line(line, current_unit)