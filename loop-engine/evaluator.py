from dataclasses import dataclass
from typing import Any

from models import LoopState


@dataclass
class EvaluationResult:
    accepted: bool
    reason: str


def evaluate_proposal(
    state: LoopState,
    proposal: dict[str, Any],
) -> EvaluationResult:

    # action の意味的検証
    if proposal.get("action") != "increment":
        return EvaluationResult(
            accepted=False,
            reason="unsupported action",
        )

    # amount の意味的検証
    amount = proposal.get("amount")

    # bool は Python 上では int の subclass なので明示的に除外する
    if isinstance(amount, bool) or not isinstance(amount, int):
        return EvaluationResult(
            accepted=False,
            reason="amount must be integer",
        )

    if amount <= 0:
        return EvaluationResult(
            accepted=False,
            reason="amount must be positive",
        )

    # target 超過を禁止
    if state.current + amount > state.target:
        return EvaluationResult(
            accepted=False,
            reason="proposal exceeds target",
        )

    return EvaluationResult(
        accepted=True,
        reason="proposal accepted",
    )
