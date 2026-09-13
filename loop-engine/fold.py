from history import History
from models import LoopState


def fold_history(
    history: History,
    initial_state: LoopState,
) -> LoopState:
    state = initial_state

    for entry in history.entries():
        if not entry.accepted:
            continue

        state = LoopState(
            current=entry.state_after["current"],
            target=entry.state_after["target"],
            iteration=entry.state_after["iteration"],
        )

    return state