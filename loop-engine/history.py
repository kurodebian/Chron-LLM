from dataclasses import dataclass
from typing import Any

from models import FailureType


@dataclass(frozen=True)
class HistoryEntry:
    step: int
    state_before: dict[str, Any]
    proposal: dict[str, Any] | None
    accepted: bool
    reason: str
    state_after: dict[str, Any]
    failure_type: FailureType | None = None


class History:
    def __init__(self):
        self._entries: list[HistoryEntry] = []

    def append(self, entry: HistoryEntry) -> None:
        self._entries.append(entry)

    def entries(self) -> list[HistoryEntry]:
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
