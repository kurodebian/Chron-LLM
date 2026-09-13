from dataclasses import dataclass
from typing import Any

from commit import commit_proposal
from evaluator import evaluate_proposal
from models import LoopState, Proposal


@dataclass
class StepResult:
    state_before: LoopState
    proposal: Proposal
    accepted: bool
    reason: str
    state_after: LoopState


class LoopController:
    def __init__(self, state: LoopState):
        self.state = state

    def step(self, proposal_data: dict[str, Any]) -> StepResult:
        state_before = self.state

        proposal = Proposal(
            action=proposal_data["action"],
            amount=proposal_data["amount"],
        )

        evaluation = evaluate_proposal(
            state=self.state,
            proposal=proposal_data,
        )

        if evaluation.accepted:
            self.state = commit_proposal(
                state=self.state,
                proposal=proposal,
            )

        return StepResult(
            state_before=state_before,
            proposal=proposal,
            accepted=evaluation.accepted,
            reason=evaluation.reason,
            state_after=self.state,
        )
