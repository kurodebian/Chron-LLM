from dataclasses import dataclass
from enum import Enum


class FailureType(str, Enum):
    VALIDATION_FAILURE = "validation_failure"
    SEMANTIC_REJECTION = "semantic_rejection"
    LLM_GENERATION_FAILURE = "llm_generation_failure"


@dataclass
class LoopState:
    current: int
    target: int
    iteration: int = 0


@dataclass
class Proposal:
    action: str
    amount: int


@dataclass(frozen=True)
class LoopStatistics:
    total_steps: int
    accepted_count: int
    rejected_count: int
    validation_failure_count: int
    semantic_rejection_count: int
    llm_generation_failure_count: int
