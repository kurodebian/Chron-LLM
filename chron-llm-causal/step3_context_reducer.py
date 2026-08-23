"""
step3_context_reducer.py — STEP 3: Stateful ContextReducer
Pure deterministic state machine for managing current_unit contexts.
Grammar rules are NOT re-evaluated here; relies strictly on P5 Typed Claims.
"""

from dataclasses import dataclass, replace
from typing import Optional
from step0_ssot import ParseStatus, ClaimType
from step2_production_parser import ProductionParseResult


@dataclass(frozen=True)
class ContextState:
    """
    Immutable state container representing Context_t.
    """
    current_unit: Optional[str] = None


class ContextReducer:
    """
    Deterministic state reducer.
    Transition Rule:
      - ParseStatus == VALID_CLAIM and ClaimType == UNIT -> Transition to target
      - Otherwise -> Retain existing current_unit without mutation (with non-aliasing instance generation)
    """

    @classmethod
    def reduce(cls, state: ContextState, result: ProductionParseResult) -> ContextState:
        # P5 Typed Claim が VALID かつ UNIT である場合のみ Active Context を更新
        if result.status == ParseStatus.VALID_CLAIM and result.claim_type == ClaimType.UNIT:
            return ContextState(current_unit=result.target)

        # 非UNIT Claim、構文エラー、空白、コメント、非候補行はすべてコンテキストを「維持」するが、
        # 履歴全体のオブジェクト独立性 (is not / id() 一意性) を保証するため、常に新しいインスタンスを生成する。
        return replace(state)