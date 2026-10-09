from pathlib import Path

import tools.run_a1a_corpus as runner
import sys

def setup_runner(monkeypatch, tmp_path, entries):
    work = tmp_path / "experiment"
    work.mkdir()
    repo = tmp_path / "Chron-LLM"
    repo.mkdir()

    monkeypatch.chdir(work)
    monkeypatch.setattr(
        runner,
        "load_manifest",
        lambda _path: {
            "repository_root": str(repo),
            "files": [{"path": p} for p in entries],
        },
    )
    monkeypatch.setattr(sys, "argv", ["run_a1a_corpus.py"])

    return work, repo


def artifact_path(document_path):
    return Path("semantic_units") / f"{document_path}.units.json"


def test_valid_existing_artifact_is_reused_without_llm(
    monkeypatch, tmp_path, capsys
):
    _, _ = setup_runner(
        monkeypatch, tmp_path, ["docs/a.md"]
    )

    artifact = artifact_path("docs/a.md")
    artifact.parent.mkdir(parents=True)
    artifact.write_text('{"existing": true}\n', encoding="utf-8")
    original = artifact.read_bytes()

    validated = []

    def validate(path):
        validated.append(Path(path).resolve())

    monkeypatch.setattr(runner, "validate_units_json", validate)

    def forbidden_llm(*args, **kwargs):
        raise AssertionError("LLM must not be called for a valid existing artifact")

    monkeypatch.setattr(runner, "detect_boundaries_llm", forbidden_llm)

    result = runner.main()

    assert result == 0
    assert validated == [artifact.resolve()]
    assert artifact.read_bytes() == original

    output = capsys.readouterr().out
    assert "REUSE" in output


def test_invalid_existing_artifact_is_not_overwritten_and_run_continues(
    monkeypatch, tmp_path, capsys
):
    _, _ = setup_runner(
        monkeypatch, tmp_path, ["docs/a.md", "docs/b.md"]
    )

    artifact = artifact_path("docs/a.md")
    artifact.parent.mkdir(parents=True)
    artifact.write_text("preserve-this-file\n", encoding="utf-8")
    original = artifact.read_bytes()

    def validate(path):
        if Path(path).name == "a.md.units.json":
            raise ValueError("INVALID_EXISTING_ARTIFACT")

    monkeypatch.setattr(runner, "validate_units_json", validate)

    processed = []

    def fake_run_document(repository_root, document_path):
        processed.append(document_path)
        return Path(f"/tmp/{document_path}.units.json")

    monkeypatch.setattr(runner, "run_document", fake_run_document)

    result = runner.main()
    output = capsys.readouterr().out

    assert result != 0
    assert artifact.read_bytes() == original
    assert "docs/a.md" not in processed
    assert "docs/b.md" in processed
    assert "INVALID_EXISTING_ARTIFACT" in output
    assert "RESULT FAIL" in output


def test_document_failure_does_not_stop_later_documents(
    monkeypatch, tmp_path, capsys
):
    _, _ = setup_runner(
        monkeypatch, tmp_path, ["docs/a.md", "docs/b.md"]
    )

    processed = []

    def fake_run_document(repository_root, document_path):
        processed.append(document_path)
        if document_path == "docs/a.md":
            raise ValueError(
                "INVALID_OBSERVATION: whitespace-only span 117-117"
            )
        return Path("/tmp/docs-b.units.json")

    monkeypatch.setattr(runner, "run_document", fake_run_document)

    result = runner.main()
    output = capsys.readouterr().out

    assert result != 0
    assert processed == ["docs/a.md", "docs/b.md"]
    assert "whitespace-only span 117-117" in output
    assert "RESULT FAIL" in output
