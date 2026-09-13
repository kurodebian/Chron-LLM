from history import History, HistoryEntry


def test_history_is_append_only():
    history = History()

    entry = HistoryEntry(
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
        failure_type=None,
    )

    history.append(entry)

    assert len(history) == 1
    assert history.entries() == [entry]


def test_history_entries_returns_copy():
    history = History()

    entry = HistoryEntry(
        step=1,
        state_before={
            "current": 0,
            "target": 7,
            "iteration": 0,
        },
        proposal=None,
        accepted=False,
        reason="validation failed",
        state_after={
            "current": 0,
            "target": 7,
            "iteration": 0,
        },
        failure_type=None,
    )

    history.append(entry)

    entries = history.entries()
    entries.clear()

    assert len(history) == 1