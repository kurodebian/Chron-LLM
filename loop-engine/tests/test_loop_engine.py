import json

from controller import LoopController
from loop import LoopEngine, build_run_trace, project_run_trace
from models import FailureType, LoopState
from schema_validator import validate_proposal_schema


def test_multistep_accept():
    engine = LoopEngine(
        state=LoopState(current=0, target=7),
        max_steps=5,
    )

    outputs = iter([
        '{"action":"increment","amount":3}',
        '{"action":"increment","amount":3}',
        '{"action":"increment","amount":1}',
    ])

    engine.llm.generate = lambda prompt: next(outputs)

    result = engine.run()

    assert result.completed is True
    assert result.steps == 3
    assert result.termination_reason.value == "completed"
    assert result.state == LoopState(
        current=7,
        target=7,
        iteration=3,
    )

    entries = result.history.entries()

    assert [entry.accepted for entry in entries] == [
        True,
        True,
        True,
    ]

    assert [entry.state_after["current"] for entry in entries] == [
        3,
        6,
        7,
    ]


def test_reject_does_not_mutate_state():
    controller = LoopController(
        LoopState(current=6, target=7)
    )

    proposal = {
        "action": "increment",
        "amount": 3,
    }

    validate_proposal_schema(proposal)

    before = controller.state

    result = controller.step(proposal)

    assert result.accepted is False
    assert result.reason == "proposal exceeds target"

    assert controller.state == before
    assert result.state_before == before
    assert result.state_after == before


def test_reject_retry_then_accept():
    engine = LoopEngine(
        state=LoopState(current=6, target=7),
        max_steps=5,
    )

    outputs = iter([
        '{"action":"increment","amount":3}',
        '{"action":"increment","amount":1}',
    ])

    engine.llm.generate = lambda prompt: next(outputs)

    result = engine.run()

    assert result.completed is True
    assert result.steps == 2

    # 2 attempts, but only 1 committed transition.
    assert result.state == LoopState(
        current=7,
        target=7,
        iteration=1,
    )

    first, second = result.history.entries()

    # First proposal: schema-valid, semantic reject, no mutation.
    assert first.proposal == {
        "action": "increment",
        "amount": 3,
    }
    assert first.accepted is False
    assert first.reason == "proposal exceeds target"
    assert first.state_before == {
        "current": 6,
        "target": 7,
        "iteration": 0,
    }
    assert first.state_after == {
        "current": 6,
        "target": 7,
        "iteration": 0,
    }

    # Retry: new proposal, accepted, committed.
    assert second.proposal == {
        "action": "increment",
        "amount": 1,
    }
    assert second.accepted is True
    assert second.reason == "proposal accepted"
    assert second.state_before == {
        "current": 6,
        "target": 7,
        "iteration": 0,
    }
    assert second.state_after == {
        "current": 7,
        "target": 7,
        "iteration": 1,
    }


def test_validation_failure_does_not_mutate_state_and_retries():
    engine = LoopEngine(
        state=LoopState(current=0, target=7),
        max_steps=2,
    )

    outputs = iter([
        '{"action":"increment","amount":0}',
        '{"action":"increment","amount":3}',
    ])

    engine.llm.generate = lambda prompt: next(outputs)

    result = engine.run()

    # Two attempts, but only the second proposal is committed.
    assert result.completed is False
    assert result.steps == 2
    assert result.state == LoopState(
        current=3,
        target=7,
        iteration=1,
    )

    first, second = result.history.entries()

    # First proposal: schema-invalid.
    assert first.proposal is None
    assert first.accepted is False
    assert first.state_before == {
        "current": 0,
        "target": 7,
        "iteration": 0,
    }
    assert first.state_after == {
        "current": 0,
        "target": 7,
        "iteration": 0,
    }

    # Retry: new schema-valid proposal, accepted and committed.
    assert second.proposal == {
        "action": "increment",
        "amount": 3,
    }
    assert second.accepted is True

def test_max_steps_termination():
    engine = LoopEngine(
        state=LoopState(current=0, target=100),
        max_steps=2,
    )

    outputs = iter([
        '{"action":"increment","amount":3}',
        '{"action":"increment","amount":3}',
    ])

    engine.llm.generate = lambda prompt: next(outputs)

    result = engine.run()

    assert result.completed is False
    assert result.steps == 2
    assert result.state == LoopState(
        current=6,
        target=100,
        iteration=2,
    )
    assert result.termination_reason.value == "max_steps_reached"

    assert len(result.history.entries()) == 2

def test_completion_at_max_steps_boundary():
    engine = LoopEngine(
        state=LoopState(current=0, target=6),
        max_steps=2,
    )

    outputs = iter([
        '{"action":"increment","amount":3}',
        '{"action":"increment","amount":3}',
    ])

    engine.llm.generate = lambda prompt: next(outputs)

    result = engine.run()

    assert result.completed is True
    assert result.steps == 2
    assert result.state == LoopState(
        current=6,
        target=6,
        iteration=2,
    )
    assert result.termination_reason.value == "completed"

def test_validation_failure_is_classified():
    engine = LoopEngine(
        state=LoopState(current=0, target=7),
        max_steps=1,
    )

    engine.llm.generate = lambda prompt: (
        '{"action":"increment","amount":0}'
    )

    result = engine.run()

    assert result.completed is False
    assert result.termination_reason.value == "max_steps_reached"

    entry = result.history.entries()[0]

    assert entry.accepted is False
    assert entry.failure_type == FailureType.VALIDATION_FAILURE

def test_semantic_rejection_is_classified():
    engine = LoopEngine(
        state=LoopState(current=6, target=7),
        max_steps=1,
    )

    engine.llm.generate = lambda prompt: (
        '{"action":"increment","amount":3}'
    )

    result = engine.run()

    assert result.completed is False
    assert result.termination_reason.value == "max_steps_reached"

    entry = result.history.entries()[0]

    assert entry.accepted is False
    assert entry.failure_type == FailureType.SEMANTIC_REJECTION

def test_llm_generation_failure_is_classified():
    engine = LoopEngine(
        state=LoopState(current=0, target=7),
        max_steps=1,
    )

    def fail_generation(prompt):
        raise RuntimeError("LLM unavailable")

    engine.llm.generate = fail_generation

    result = engine.run()

    assert result.completed is False
    assert result.termination_reason.value == "max_steps_reached"

    entry = result.history.entries()[0]

    assert entry.accepted is False
    assert entry.failure_type == FailureType.LLM_GENERATION_FAILURE
    assert "LLM generation failed" in entry.reason

def test_statistics_all_accepted():
    engine = LoopEngine(
        state=LoopState(current=0, target=3),
        max_steps=3,
    )

    proposals = iter([
        '{"action":"increment","amount":1}',
        '{"action":"increment","amount":1}',
        '{"action":"increment","amount":1}',
    ])
    engine.llm.generate = lambda prompt: next(proposals)

    result = engine.run()

    assert result.completed is True
    assert result.statistics.total_steps == 3
    assert result.statistics.accepted_count == 3
    assert result.statistics.rejected_count == 0
    assert result.statistics.validation_failure_count == 0
    assert result.statistics.semantic_rejection_count == 0
    assert result.statistics.llm_generation_failure_count == 0


def test_statistics_validation_failure():
    engine = LoopEngine(
        state=LoopState(current=0, target=3),
        max_steps=2,
    )

    proposals = iter([
        '{"action":"increment","amount":0}',
        '{"action":"increment","amount":1}',
    ])
    engine.llm.generate = lambda prompt: next(proposals)

    result = engine.run()

    assert result.completed is False
    assert result.statistics.total_steps == 2
    assert result.statistics.accepted_count == 1
    assert result.statistics.rejected_count == 1
    assert result.statistics.validation_failure_count == 1
    assert result.statistics.semantic_rejection_count == 0
    assert result.statistics.llm_generation_failure_count == 0


def test_statistics_semantic_rejection():
    engine = LoopEngine(
        state=LoopState(current=2, target=3),
        max_steps=2,
    )

    proposals = iter([
        '{"action":"increment","amount":2}',
        '{"action":"increment","amount":1}',
    ])
    engine.llm.generate = lambda prompt: next(proposals)

    result = engine.run()

    assert result.completed is True
    assert result.statistics.total_steps == 2
    assert result.statistics.accepted_count == 1
    assert result.statistics.rejected_count == 1
    assert result.statistics.validation_failure_count == 0
    assert result.statistics.semantic_rejection_count == 1
    assert result.statistics.llm_generation_failure_count == 0


def test_statistics_llm_generation_failure():
    engine = LoopEngine(
        state=LoopState(current=0, target=1),
        max_steps=2,
    )

    calls = iter([
        RuntimeError("LLM unavailable"),
        '{"action":"increment","amount":1}',
    ])

    def generate(prompt):
        value = next(calls)
        if isinstance(value, Exception):
            raise value
        return value

    engine.llm.generate = generate

    result = engine.run()

    assert result.completed is True
    assert result.statistics.total_steps == 2
    assert result.statistics.accepted_count == 1
    assert result.statistics.rejected_count == 1
    assert result.statistics.validation_failure_count == 0
    assert result.statistics.semantic_rejection_count == 0
    assert result.statistics.llm_generation_failure_count == 1

def test_same_proposal_sequence_is_reproducible():
    def run_with_proposals():
        engine = LoopEngine(
            state=LoopState(current=0, target=7),
            max_steps=5,
        )

        outputs = iter([
            '{"action":"increment","amount":3}',
            '{"action":"increment","amount":3}',
            '{"action":"increment","amount":3}',
            '{"action":"increment","amount":1}',
        ])

        engine.llm.generate = lambda prompt: next(outputs)

        return engine.run()

    first = run_with_proposals()
    second = run_with_proposals()

    assert first.completed == second.completed
    assert first.steps == second.steps
    assert first.state == second.state
    assert first.termination_reason == second.termination_reason
    assert first.statistics == second.statistics

    first_entries = first.history.entries()
    second_entries = second.history.entries()

    assert first_entries == second_entries

def test_mixed_failure_sequence_is_reproducible():
    def run_with_sequence():
        engine = LoopEngine(
            state=LoopState(current=0, target=3),
            max_steps=4,
        )

        outputs = iter([
            '{"action":"increment","amount":0}',
            '{"action":"increment","amount":5}',
            RuntimeError("LLM unavailable"),
            '{"action":"increment","amount":3}',
        ])

        def generate(prompt):
            value = next(outputs)
            if isinstance(value, Exception):
                raise value
            return value

        engine.llm.generate = generate

        return engine.run()

    first = run_with_sequence()
    second = run_with_sequence()

    assert first.completed == second.completed
    assert first.steps == second.steps
    assert first.state == second.state
    assert first.termination_reason == second.termination_reason
    assert first.statistics == second.statistics

    first_entries = first.history.entries()
    second_entries = second.history.entries()

    assert first_entries == second_entries

    assert [
        entry.failure_type
        for entry in first_entries
    ] == [
        FailureType.VALIDATION_FAILURE,
        FailureType.SEMANTIC_REJECTION,
        FailureType.LLM_GENERATION_FAILURE,
        None,
    ]

def test_run_trace_is_reproducible():
    def run_with_sequence():
        engine = LoopEngine(
            state=LoopState(current=0, target=7),
            max_steps=4,
        )

        outputs = iter([
            '{"action":"increment","amount":0}',
            '{"action":"increment","amount":3}',
            '{"action":"increment","amount":5}',
            '{"action":"increment","amount":4}',
        ])

        def generate(prompt):
            value = next(outputs)
            if isinstance(value, Exception):
                raise value
            return value

        engine.llm.generate = generate

        initial_state = engine.controller.state
        result = engine.run()

        return build_run_trace(
            initial_state=initial_state,
            result=result,
        )

    first = run_with_sequence()
    second = run_with_sequence()

    assert first == second

def test_run_trace_projection_is_json_compatible():
    engine = LoopEngine(
        state=LoopState(current=0, target=3),
        max_steps=2,
    )

    outputs = iter([
        '{"action":"increment","amount":0}',
        '{"action":"increment","amount":3}',
    ])

    engine.llm.generate = lambda prompt: next(outputs)

    initial_state = engine.controller.state
    result = engine.run()

    trace = build_run_trace(
        initial_state=initial_state,
        result=result,
    )

    projected = project_run_trace(trace)

    assert projected["initial_state"] == {
        "current": 0,
        "target": 3,
        "iteration": 0,
    }

    assert projected["history"][0]["failure_type"] == (
        "validation_failure"
    )

    assert projected["history"][1]["accepted"] is True
    assert projected["history"][1]["failure_type"] is None

    assert projected["final_state"] == {
        "current": 3,
        "target": 3,
        "iteration": 1,
    }

    assert projected["statistics"] == {
        "total_steps": 2,
        "accepted_count": 1,
        "rejected_count": 1,
        "validation_failure_count": 1,
        "semantic_rejection_count": 0,
        "llm_generation_failure_count": 0,
    }

    assert projected["completed"] is True
    assert projected["steps"] == 2
    assert projected["termination_reason"] == "completed"

def test_run_trace_projection_can_be_json_serialized():
    engine = LoopEngine(
        state=LoopState(current=0, target=1),
        max_steps=1,
    )

    engine.llm.generate = lambda prompt: (
        '{"action":"increment","amount":1}'
    )

    initial_state = engine.controller.state
    result = engine.run()

    trace = build_run_trace(
        initial_state=initial_state,
        result=result,
    )

    projected = project_run_trace(trace)

    serialized = json.dumps(
        projected,
        sort_keys=True,
    )

    assert isinstance(serialized, str)
    assert '"completed": true' in serialized
    assert '"termination_reason": "completed"' in serialized
