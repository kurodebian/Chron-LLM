#!/usr/bin/env python3
# tools/llm_backend.py

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import json
import subprocess
from typing import Any


@dataclass(frozen=True)
class LLMConfig:
    """
    LLM execution configuration.

    This layer knows how the model is executed.
    It does NOT know anything about A-1a semantic segmentation.
    """

    command: tuple[str, ...]
    model_path: str

    temperature: float = 0.0
    top_k: int | None = None
    top_p: float | None = None
    seed: int | None = 0

    n_predict: int | None = None
    single_turn: bool = False

    # Prism Bonsai CLI execution controls.
    simple_io: bool = False
    display_prompt: bool = True
    machine_output: bool = False
    show_timings: bool = True
    reasoning: str | None = None

    runtime_revision: str | None = None
    grammar_path: str | None = None


@dataclass(frozen=True)
class LLMObservation:
    """
    Raw LLM execution result.

    The output is intentionally kept separate from
    A-1a normalization.
    """

    raw_output: str
    metadata: dict[str, Any]


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def build_command(
    config: LLMConfig,
    prompt: str,
) -> list[str]:

    command = list(config.command)

    if config.simple_io:
        command.append("--simple-io")

    if not config.display_prompt:
        command.append("--no-display-prompt")

    if config.machine_output:
        command.append("--machine-output")

    if not config.show_timings:
        command.append("--no-show-timings")

    if config.reasoning is not None:
        command.extend([
            "--reasoning",
            config.reasoning,
        ])

    command.extend([
        "-m",
        config.model_path,
        "--temp",
        str(config.temperature),
    ])

    if config.top_k is not None:
        command.extend([
            "--top-k",
            str(config.top_k),
        ])

    if config.top_p is not None:
        command.extend([
            "--top-p",
            str(config.top_p),
        ])

    if config.seed is not None:
        command.extend([
            "--seed",
            str(config.seed),
        ])

    if config.single_turn:
        command.append("-st")

    if config.n_predict is not None:
        command.extend([
            "-n",
            str(config.n_predict),
        ])

    if config.grammar_path is not None:
        command.extend([
            "--grammar-file",
            config.grammar_path,
        ])

    command.extend([
        "-p",
        prompt,
    ])

    return command


def call_llm(
    prompt: str,
    config: LLMConfig,
) -> LLMObservation:
    """
    Execute the configured LLM backend.

    This function:
      - executes the configured backend
      - captures raw stdout
      - captures execution metadata

    This function MUST NOT:
      - parse A-1a JSON
      - repair output
      - normalize boundaries
      - assign semantic meaning
      - generate source_text
    """

    command = build_command(
        config=config,
        prompt=prompt,
    )

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    if completed.returncode != 0:
        raise RuntimeError(
            "LLM_BACKEND_FAILURE: "
            f"returncode={completed.returncode}\n"
            f"stderr={completed.stderr}"
        )

    metadata = {
        "model_path": config.model_path,
        "model_sha256": sha256_file(config.model_path),
        "runtime_revision": config.runtime_revision,
        "prompt_sha256": sha256_text(prompt),
        "sampling_parameters": {
            "temperature": config.temperature,
            "top_k": config.top_k,
            "top_p": config.top_p,
            "seed": config.seed,
        },
        "execution_parameters": {
            "n_predict": config.n_predict,
            "single_turn": config.single_turn,
            "simple_io": config.simple_io,
            "display_prompt": config.display_prompt,
            "machine_output": config.machine_output,
            "show_timings": config.show_timings,
            "reasoning": config.reasoning,
        },
        "grammar_path": config.grammar_path,
        "raw_output_sha256": sha256_text(
            completed.stdout
        ),
    }

    return LLMObservation(
        raw_output=completed.stdout,
        metadata=metadata,
    )


def observation_to_dict(
    observation: LLMObservation,
) -> dict[str, Any]:
    return asdict(observation)
