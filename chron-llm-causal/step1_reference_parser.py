"""
step1_reference_parser.py — STEP 1: EBNF Reference Parser (Fixed)
"""

from dataclasses import dataclass
from typing import Optional
from step0_ssot import ParseStatus, ClaimType


@dataclass(frozen=True)
class ReferenceAST:
    claim_type: ClaimType
    target_id: str


@dataclass(frozen=True)
class ReferenceParseResult:
    status: ParseStatus
    ast: Optional[ReferenceAST] = None
    error_reason: Optional[str] = None


class CursorScanner:
    def __init__(self, text: str) -> None:
        self.text: str = text
        self.pos: int = 0
        self.length: int = len(text)

    @property
    def current(self) -> Optional[str]:
        return self.text[self.pos] if self.pos < self.length else None

    def is_eof(self) -> bool:
        return self.pos >= self.length

    def advance(self) -> None:
        if self.pos < self.length:
            self.pos += 1

    def skip_ws(self) -> int:
        start = self.pos
        while self.current in (' ', '\t'):
            self.advance()
        return self.pos - start

    def match_literal(self, literal: str) -> bool:
        if self.text.startswith(literal, self.pos):
            self.pos += len(literal)
            return True
        return False


class EBNFReferenceParser:
    @staticmethod
    def _is_id_head(ch: Optional[str]) -> bool:
        if ch is None:
            return False
        return ('a' <= ch <= 'z') or ('A' <= ch <= 'Z') or ('0' <= ch <= '9') or (ch == '_')

    @classmethod
    def parse_id(cls, scanner: CursorScanner) -> Optional[str]:
        start_pos = scanner.pos
        if not cls._is_id_head(scanner.current):
            return None
        scanner.advance()

        while not scanner.is_eof():
            ch = scanner.current
            if cls._is_id_head(ch):
                scanner.advance()
            elif ch in ('.', '-'):
                next_pos = scanner.pos + 1
                next_ch = scanner.text[next_pos] if next_pos < scanner.length else None
                if cls._is_id_head(next_ch):
                    scanner.advance()
                    scanner.advance()
                else:
                    break
            else:
                break

        return scanner.text[start_pos:scanner.pos]

    @classmethod
    def parse_line(cls, line_text: str) -> ReferenceParseResult:
        # PhysicalLine Strict Guard: Rejects any embedded line terminators (\r, \n)
        if '\r' in line_text or '\n' in line_text:
            return ReferenceParseResult(
                status=ParseStatus.INVALID_GRAMMAR,
                error_reason="PhysicalLine MUST NOT contain line terminators (\\r, \\n)"
            )

        scanner = CursorScanner(line_text)

        # P1: Blank / Comment Check
        scanner.skip_ws()
        if scanner.is_eof():
            return ReferenceParseResult(status=ParseStatus.BLANK_LINE)

        if scanner.current == '#':
            return ReferenceParseResult(status=ParseStatus.COMMENT_LINE)

        # P2: Candidate Detection
        claim_type: Optional[ClaimType] = None
        if scanner.match_literal("unit"):
            claim_type = ClaimType.UNIT
        elif scanner.match_literal("requires"):
            claim_type = ClaimType.REQUIRES
        elif scanner.match_literal("depends_on"):
            claim_type = ClaimType.DEPENDS_ON

        if claim_type is None:
            return ReferenceParseResult(status=ParseStatus.NOT_A_CANDIDATE)

        scanner.skip_ws()
        if not scanner.match_literal(":"):
            return ReferenceParseResult(status=ParseStatus.NOT_A_CANDIDATE)

        # P4: Grammar Parse
        scanner.skip_ws()
        target_id = cls.parse_id(scanner)
        if target_id is None:
            return ReferenceParseResult(
                status=ParseStatus.INVALID_GRAMMAR,
                error_reason="Missing or invalid target ID syntax"
            )

        scanner.skip_ws()
        if not scanner.is_eof():
            return ReferenceParseResult(
                status=ParseStatus.INVALID_GRAMMAR,
                error_reason="Trailing unexpected tokens after valid ID"
            )

        # P5: Typed Claim Construction
        return ReferenceParseResult(
            status=ParseStatus.VALID_CLAIM,
            ast=ReferenceAST(claim_type=claim_type, target_id=target_id)
        )


def parse_reference(line_text: str) -> ReferenceParseResult:
    return EBNFReferenceParser.parse_line(line_text)