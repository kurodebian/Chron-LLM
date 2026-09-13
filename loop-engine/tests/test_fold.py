from fold import fold_history
from history import History, HistoryEntry
from models import LoopState
from loop import LoopEngine


def test_fold_empty_history_returns_initial_state():
    history = History()

    initial = LoopState(
        current=0,
        target=7,
        iteration=0,
    )

    result = fold_history(
        history=history,
        initial_state=initial,
    )

    assert result == initial


def test_fold_accept_transitions_state():
    history = History()

    history.append(
        HistoryEntry(
            step=1,
            state_before={
                "current": 0,
                "target": 7,
                "iteration": 0,
            },
            proposal={
                "action": "increment",
                "amount": 3,
            },
            accepted=True,
            reason="proposal accepted",
            state_after={
                "current": 3,
                "target": 7,
                "iteration": 1,
            },
        )
    )

    initial = LoopState(
        current=0,
        target=7,
        iteration=0,
    )

    result = fold_history(
        history=history,
        initial_state=initial,
    )

    assert result == LoopState(
        current=3,
        target=7,
        iteration=1,
    )


def test_fold_reject_does_not_transition_state():
    history = History()

    history.append(
        HistoryEntry(
            step=1,
            state_before={
                "current": 6,
                "target": 7,
                "iteration": 0,
            },
            proposal={
                "action": "increment",
                "amount": 3,
            },
            accepted=False,
            reason="proposal exceeds target",
            state_after={
                "current": 6,
                "target": 7,
                "iteration": 0,
            },
        )
    )

    initial = LoopState(
        current=6,
        target=7,
        iteration=0,
    )

    result = fold_history(
        history=history,
        initial_state=initial,
    )

    assert result == initial


def test_fold_multistep_history():
    history = History()

    history.append(
        HistoryEntry(
            step=1,
            state_before={
                "current": 0,
                "target": 7,
                "iteration": 0,
            },
            proposal={
                "action": "increment",
                "amount": 3,
            },
            accepted=True,
            reason="proposal accepted",
            state_after={
                "current": 3,
                "target": 7,
                "iteration": 1,
            },
        )
    )

    history.append(
        HistoryEntry(
            step=2,
            state_before={
                "current": 3,
                "target": 7,
                "iteration": 1,
            },
            proposal={
                "action": "increment",
                "amount": 3,
            },
            accepted=True,
            reason="proposal accepted",
            state_after={
                "current": 6,
                "target": 7,
                "iteration": 2,
            },
        )
    )

    history.append(
        HistoryEntry(
            step=3,
            state_before={
                "current": 6,
                "target": 7,
                "iteration": 2,
            },
            proposal={
                "action": "increment",
                "amount": 1,
            },
            accepted=True,
            reason="proposal accepted",
            state_after={
                "current": 7,
                "target": 7,
                "iteration": 3,
            },
        )
    )

    initial = LoopState(
        current=0,
        target=7,
        iteration=0,
    )

    result = fold_history(
        history=history,
        initial_state=initial,
    )

    assert result == LoopState(
        current=7,
        target=7,
        iteration=3,
    )

def test_engine_state_matches_folded_history():
    initial = LoopState(
        current=0,
        target=7,
        iteration=0,
    )

    engine = LoopEngine(
        state=initial,
        max_steps=5,
    )

    outputs = iter([
        '{"action":"increment","amount":3}',
        '{"action":"increment","amount":3}',
        '{"action":"increment","amount":1}',
    ])

    engine.llm.generate = lambda prompt: next(outputs)

    result = engine.run()

    folded_state = fold_history(
        history=result.history,
        initial_state=initial,
    )

    assert result.state == folded_state
    assert engine.controller.state == folded_state

def test_state_can_be_reconstructed_from_history():
    initial = LoopState(
        current=0,
        target=7,
        iteration=0,
    )

    history = History()

    history.append(
        HistoryEntry(
            step=1,
            state_before={
                "current": 0,
                "target": 7,
                "iteration": 0,
            },
            proposal={
                "action": "increment",
                "amount": 3,
            },
            accepted=True,
            reason="proposal accepted",
            state_after={
                "current": 3,
                "target": 7,
                "iteration": 1,
            },
        )
    )

    history.append(
        HistoryEntry(
            step=2,
            state_before={
                "current": 3,
                "target": 7,
                "iteration": 1,
            },
            proposal={
                "action": "increment",
                "amount": 3,
            },
            accepted=True,
            reason="proposal accepted",
            state_after={
                "current": 6,
                "target": 7,
                "iteration": 2,
            },
        )
    )

    history.append(
        HistoryEntry(
            step=3,
            state_before={
                "current": 6,
                "target": 7,
                "iteration": 2,
            },
            proposal={
                "action": "increment",
                "amount": 1,
            },
            accepted=True,
            reason="proposal accepted",
            state_after={
                "current": 7,
                "target": 7,
                "iteration": 3,
            },
        )
    )

    # Original runtime State is intentionally discarded.
    reconstructed_state = fold_history(
        history=history,
        initial_state=initial,
    )

    assert reconstructed_state == LoopState(
        current=7,
        target=7,
        iteration=3,
    )

def test_replay_ignores_rejected_proposals():
    initial = LoopState(
        current=6,
        target=7,
        iteration=0,
    )

    history = History()

    history.append(
        HistoryEntry(
            step=1,
            state_before={
                "current": 6,
                "target": 7,
                "iteration": 0,
            },
            proposal={
                "action": "increment",
                "amount": 3,
            },
            accepted=False,
            reason="proposal exceeds target",
            state_after={
                "current": 6,
                "target": 7,
                "iteration": 0,
            },
        )
    )

    history.append(
        HistoryEntry(
            step=2,
            state_before={
                "current": 6,
                "target": 7,
                "iteration": 0,
            },
            proposal={
                "action": "increment",
                "amount": 1,
            },
            accepted=True,
            reason="proposal accepted",
            state_after={
                "current": 7,
                "target": 7,
                "iteration": 1,
            },
        )
    )

    reconstructed_state = fold_history(
        history=history,
        initial_state=initial,
    )

    assert reconstructed_state == LoopState(
        current=7,
        target=7,
        iteration=1,
    )