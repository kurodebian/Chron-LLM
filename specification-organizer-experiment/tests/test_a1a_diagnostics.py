import hashlib
import json
from pathlib import Path

import pytest

import tools.a1_segment as segment
import tools.run_a1a_corpus as runner
from tools.llm_backend import LLMObservation


def expected_diagnostic_path(document_path):
    document_id = hashlib.sha256(
        document_path.encode("utf-8")
    ).hexdigest()
    return (
        Path("diagnostics")
        / "a1_segment"
        / f"{document_id}.json"
    )


def fake_observation(raw_output):
    return LLMObservation(
        raw_output=raw_output,
        metadata={
            "model_path": "test-model.gguf",
            "runtime_revision": "test-revision",
            "raw_output_sha256": hashlib.sha256(
                raw_output.encode("utf-8")
            ).hexdigest(),
        },
    )


def test_extraction_failure_preserves_raw_output(
    monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)

    document_path = "docs/extraction-failure.md"
    raw_output = "CLI envelope without a boundaries JSON object"

    monkeypatch.setattr(
        segment,
        "call_llm",
        lambda prompt, config: fake_observation(raw_output),
    )

    with pytest.raises(
        ValueError,
        match="A-1a boundary JSON object not found",
    ):
        segment.detect_boundaries_llm(
            document_path,
            ["source line\n"],
        )

    diagnostic = expected_diagnostic_path(document_path)
    assert diagnostic.is_file()

    record = json.loads(diagnostic.read_text(encoding="utf-8"))
    assert record["document_path"] == document_path
    assert record["raw_output"] == raw_output
    assert record["metadata"]["runtime_revision"] == "test-revision"
    assert record["extraction_status"] == "failed"
    assert record["validation_status"] == "not_run"

    assert not (
        Path("semantic_units")
        / f"{document_path}.units.json"
    ).exists()


def test_validation_failure_preserves_raw_output_and_writes_no_artifact(
    monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)

    repository_root = tmp_path / "Chron-LLM"
    repository_root.mkdir()

    source = repository_root / "docs" / "whitespace.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        "heading\n\n   \ncontent\n",
        encoding="utf-8",
    )

    document_path = "docs/whitespace.md"
    raw_output = json.dumps({
        "boundaries": [
            {"line_start": 1, "line_end": 1},
            {"line_start": 3, "line_end": 3},
            {"line_start": 4, "line_end": 4},
        ]
    })

    monkeypatch.setattr(
        segment,
        "call_llm",
        lambda prompt, config: fake_observation(raw_output),
    )

    with pytest.raises(
        ValueError,
        match="whitespace-only span",
    ):
        runner.run_document(repository_root, document_path)

    diagnostic = expected_diagnostic_path(document_path)
    assert diagnostic.is_file()

    record = json.loads(diagnostic.read_text(encoding="utf-8"))
    assert record["raw_output"] == raw_output
    assert record["extraction_status"] == "success"
    assert record["validation_status"] == "failed"
    assert "whitespace-only span" in record["error"]

    assert not (
        Path("semantic_units")
        / f"{document_path}.units.json"
    ).exists()


def test_diagnostics_are_separate_from_canonical_artifacts(
    monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)

    first = expected_diagnostic_path("docs/a.md")
    second = expected_diagnostic_path("docs/b.md")

    assert first.parent == Path("diagnostics/a1_segment")
    assert first != second
    assert not str(first).startswith("semantic_units/")


def test_extraction_does_not_mutate_raw_output(
    monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)

    document_path = "docs/valid.md"
    raw_output = (
        'CLI prefix\n'
        '{"boundaries":[{"line_start":1,"line_end":1}]}\n'
        'CLI suffix\n'
    )
    original = raw_output

    monkeypatch.setattr(
        segment,
        "call_llm",
        lambda prompt, config: fake_observation(raw_output),
    )

    result = segment.detect_boundaries_llm(
        document_path,
        ["source line\n"],
    )

    assert raw_output == original
    assert result == {
        "boundaries": [
            {"line_start": 1, "line_end": 1}
        ]
    }

    diagnostic = expected_diagnostic_path(document_path)
    assert diagnostic.is_file()

    record = json.loads(diagnostic.read_text(encoding="utf-8"))
    assert record["raw_output"] == original
    assert record["extraction_status"] == "success"


def test_backend_failure_preserves_diagnostic_and_writes_no_artifact(
    monkeypatch, tmp_path
):
    from tools.llm_backend import LLMBackendError

    monkeypatch.chdir(tmp_path)

    document_path = "docs/backend-failure.md"
    raw_output = '{"boundaries": [{"line_start": 1'
    stderr = "simulated backend failure"
    metadata = {
        "model_path": "test-model.gguf",
        "execution_result": {
            "returncode": 7,
            "stdout_chars": len(raw_output),
        },
    }

    def fail_backend(prompt, config):
        raise LLMBackendError(
            "LLM_BACKEND_FAILURE: returncode=7",
            returncode=7,
            raw_output=raw_output,
            stderr=stderr,
            metadata=metadata,
        )

    monkeypatch.setattr(segment, "call_llm", fail_backend)

    with pytest.raises(
        LLMBackendError,
        match="LLM_BACKEND_FAILURE: returncode=7",
    ):
        segment.detect_boundaries_llm(
            document_path,
            ["source line\n"],
        )

    diagnostic = expected_diagnostic_path(document_path)
    assert diagnostic.is_file()

    record = json.loads(diagnostic.read_text(encoding="utf-8"))
    assert record["raw_output"] == raw_output
    assert record["backend_stderr"] == stderr
    assert record["backend_returncode"] == 7
    assert record["metadata"] == metadata
    assert record["extraction_status"] == "failed"
    assert record["validation_status"] == "not_run"

    assert not (
        Path("semantic_units")
        / f"{document_path}.units.json"
    ).exists()


def test_call_llm_preserves_nonzero_process_result(
    monkeypatch, tmp_path
):
    from types import SimpleNamespace
    import tools.llm_backend as backend

    model_path = tmp_path / "test-model.gguf"
    model_path.write_bytes(b"test model")

    raw_output = '{"boundaries": ['
    stderr = "simulated CLI error"

    monkeypatch.setattr(
        backend.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=7,
            stdout=raw_output,
            stderr=stderr,
        ),
    )

    config = backend.LLMConfig(
        command=("fake-llama-cli",),
        model_path=str(model_path),
        n_predict=4096,
    )

    with pytest.raises(backend.LLMBackendError) as caught:
        backend.call_llm("test prompt", config)

    error = caught.value
    assert error.returncode == 7
    assert error.raw_output == raw_output
    assert error.stderr == stderr
    assert error.metadata["execution_result"]["returncode"] == 7
    assert error.metadata["execution_result"]["stdout_chars"] == len(
        raw_output
    )
    assert error.metadata["execution_result"]["stderr_sha256"] == (
        hashlib.sha256(stderr.encode("utf-8")).hexdigest()
    )


def test_call_llm_success_preserves_stderr_and_redacts_prompt(
    monkeypatch, tmp_path
):
    from types import SimpleNamespace
    import tools.llm_backend as backend

    model_path = tmp_path / "test-model.gguf"
    model_path.write_bytes(b"test model")

    prompt = "PRIVATE_PROMPT_SENTINEL"
    stdout = '{"boundaries":[{"line_start":1,"line_end":1}]}'
    stderr = "simulated informational stderr"

    def fake_run(args, **kwargs):
        if args[-1] == "--version":
            return SimpleNamespace(
                returncode=0,
                stdout="fake llama version",
                stderr="",
            )
        return SimpleNamespace(
            returncode=0,
            stdout=stdout,
            stderr=stderr,
        )

    monkeypatch.setattr(backend.subprocess, "run", fake_run)
    backend.runtime_identity.cache_clear()

    config = backend.LLMConfig(
        command=("fake-llama-cli",),
        model_path=str(model_path),
        n_predict=4096,
    )

    observation = backend.call_llm(prompt, config)

    assert observation.raw_output == stdout
    assert observation.stderr == stderr
    assert observation.metadata["execution_result"]["returncode"] == 0
    assert observation.metadata["execution_result"]["stderr_sha256"] == (
        hashlib.sha256(stderr.encode("utf-8")).hexdigest()
    )

    recorded_command = observation.metadata["command_redacted"]
    assert prompt not in recorded_command
    assert "<PROMPT_REDACTED>" in recorded_command
    assert observation.metadata["prompt_sha256"] == (
        hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    )


def test_runtime_identity_probe_failure_does_not_raise(
    monkeypatch, tmp_path
):
    import tools.llm_backend as backend

    executable = tmp_path / "fake-llama-cli"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)

    def fail_version_probe(*args, **kwargs):
        raise TimeoutError("simulated version probe timeout")

    monkeypatch.setattr(backend.subprocess, "run", fail_version_probe)
    backend.runtime_identity.cache_clear()

    identity = backend.runtime_identity(str(executable))

    assert identity["resolved_executable"] == str(executable.resolve())
    assert identity["version_probe_error"].startswith("TimeoutError:")
