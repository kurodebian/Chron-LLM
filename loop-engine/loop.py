import json

from dataclasses import dataclass
from enum import Enum

from controller import LoopController
from history import History, HistoryEntry
from llm import LLMClient
from models import FailureType, LoopState, LoopStatistics
from prompt_builder import build_proposal_prompt
from schema_validator import validate_proposal_schema


class TerminationReason(str, Enum):
    COMPLETED = "completed"
    MAX_STEPS_REACHED = "max_steps_reached"

@dataclass(frozen=True)
class RunTrace:
    initial_state: LoopState
    history: tuple[HistoryEntry, ...]
    final_state: LoopState
    statistics: LoopStatistics
    completed: bool
    steps: int
    termination_reason: TerminationReason

def project_run_trace(trace: RunTrace) -> dict:
    return {
        "initial_state": {
            "current": trace.initial_state.current,
            "target": trace.initial_state.target,
            "iteration": trace.initial_state.iteration,
        },
        "history": [
            {
                "step": entry.step,
                "state_before": dict(entry.state_before),
                "proposal": (
                    dict(entry.proposal)
                    if entry.proposal is not None
                    else None
                ),
                "accepted": entry.accepted,
                "reason": entry.reason,
                "state_after": dict(entry.state_after),
                "failure_type": (
                    entry.failure_type.value
                    if entry.failure_type is not None
                    else None
                ),
            }
            for entry in trace.history
        ],
        "final_state": {
            "current": trace.final_state.current,
            "target": trace.final_state.target,
            "iteration": trace.final_state.iteration,
        },
        "statistics": {
            "total_steps": trace.statistics.total_steps,
            "accepted_count": trace.statistics.accepted_count,
            "rejected_count": trace.statistics.rejected_count,
            "validation_failure_count": (
                trace.statistics.validation_failure_count
            ),
            "semantic_rejection_count": (
                trace.statistics.semantic_rejection_count
            ),
            "llm_generation_failure_count": (
                trace.statistics.llm_generation_failure_count
            ),
        },
        "completed": trace.completed,
        "steps": trace.steps,
        "termination_reason": trace.termination_reason.value,
    }

def derive_statistics(history: History) -> LoopStatistics:
    entries = history.entries()

    accepted_count = sum(
        1 for entry in entries
        if entry.accepted
    )

    rejected_count = sum(
        1 for entry in entries
        if not entry.accepted
    )

    validation_failure_count = sum(
        1 for entry in entries
        if entry.failure_type == FailureType.VALIDATION_FAILURE
    )

    semantic_rejection_count = sum(
        1 for entry in entries
        if entry.failure_type == FailureType.SEMANTIC_REJECTION
    )

    llm_generation_failure_count = sum(
        1 for entry in entries
        if entry.failure_type == FailureType.LLM_GENERATION_FAILURE
    )

    return LoopStatistics(
        total_steps=len(entries),
        accepted_count=accepted_count,
        rejected_count=rejected_count,
        validation_failure_count=validation_failure_count,
        semantic_rejection_count=semantic_rejection_count,
        llm_generation_failure_count=llm_generation_failure_count,
    )


@dataclass
class LoopRunResult:
    completed: bool
    steps: int
    state: LoopState
    history: History
    termination_reason: TerminationReason
    statistics: LoopStatistics

def build_run_trace(
    initial_state: LoopState,
    result: LoopRunResult,
) -> RunTrace:
    return RunTrace(
        initial_state=initial_state,
        history=tuple(result.history.entries()),
        final_state=result.state,
        statistics=result.statistics,
        completed=result.completed,
        steps=result.steps,
        termination_reason=result.termination_reason,
    )

class LoopEngine:
    def __init__(
        self,
        state: LoopState,
        max_steps: int = 100,
    ):
        self.controller = LoopController(state)
        self.llm = LLMClient()
        self.max_steps = max_steps
        self.history = History()

    def run(self) -> LoopRunResult:
        for step in range(self.max_steps):
            state_before = self.controller.state

            if state_before.current == state_before.target:
                return LoopRunResult(
                    completed=True,
                    steps=step,
                    state=state_before,
                    history=self.history,
                    termination_reason=TerminationReason.COMPLETED,
                    statistics=derive_statistics(self.history),
                )

            prompt = build_proposal_prompt(state_before)

            try:
                raw_output = self.llm.generate(prompt)
            except Exception as exc:
                self.history.append(
                    HistoryEntry(
                        step=step + 1,
                        state_before={
                            "current": state_before.current,
                            "target": state_before.target,
                            "iteration": state_before.iteration,
                        },
                        proposal=None,
                        accepted=False,
                        reason=f"LLM generation failed: {exc}",
                        state_after={
                            "current": self.controller.state.current,
                            "target": self.controller.state.target,
                            "iteration": self.controller.state.iteration,
                        },
                        failure_type=FailureType.LLM_GENERATION_FAILURE,
                    )
                )
                continue

            try:
                proposal_data = json.loads(raw_output)
                validate_proposal_schema(proposal_data)
            except Exception as exc:
                self.history.append(
                    HistoryEntry(
                        step=step + 1,
                        state_before={
                            "current": state_before.current,
                            "target": state_before.target,
                            "iteration": state_before.iteration,
                        },
                        proposal=None,
                        accepted=False,
                        reason=f"proposal validation failed: {exc}",
                        state_after={
                            "current": self.controller.state.current,
                            "target": self.controller.state.target,
                            "iteration": self.controller.state.iteration,
                        },
                        failure_type=FailureType.VALIDATION_FAILURE,
                    )
                )
                continue

            result = self.controller.step(proposal_data)

            self.history.append(
                HistoryEntry(
                    step=step + 1,
                    state_before={
                        "current": state_before.current,
                        "target": state_before.target,
                        "iteration": state_before.iteration,
                    },
                    proposal=proposal_data,
                    accepted=result.accepted,
                    reason=result.reason,
                    state_after={
                        "current": result.state_after.current,
                        "target": result.state_after.target,
                        "iteration": result.state_after.iteration,
                    },
                    failure_type=(
                        FailureType.SEMANTIC_REJECTION
                        if not result.accepted
                        else None
                    ),
                )
            )

            if result.accepted:
                continue

            continue

        if self.controller.state.current == self.controller.state.target:
            return LoopRunResult(
                completed=True,
                steps=self.max_steps,
                state=self.controller.state,
                history=self.history,
                termination_reason=TerminationReason.COMPLETED,
                statistics=derive_statistics(self.history),
            )

        return LoopRunResult(
            completed=False,
            steps=self.max_steps,
            state=self.controller.state,
            history=self.history,
            termination_reason=TerminationReason.MAX_STEPS_REACHED,
            statistics=derive_statistics(self.history),
        )