from pathlib import Path
import shlex
import subprocess


REPO_ROOT = Path.home() / "Chron-LLM" / "loop-engine"
SANDBOX_ROOT = REPO_ROOT / "sandbox"


def _resolve_repo_path(path: str) -> Path:
    candidate = Path(path)

    if candidate.is_absolute():
        raise ValueError("absolute paths are not allowed")

    resolved = (REPO_ROOT / candidate).resolve()

    try:
        resolved.relative_to(REPO_ROOT.resolve())
    except ValueError:
        raise ValueError("path escapes repository root")

    return resolved


def _resolve_sandbox_path(path: str) -> Path:
    candidate = Path(path)

    if candidate.is_absolute():
        raise ValueError("absolute paths are not allowed")

    resolved = (REPO_ROOT / candidate).resolve()

    try:
        resolved.relative_to(SANDBOX_ROOT.resolve())
    except ValueError:
        raise ValueError("path must stay inside sandbox")

    return resolved


def read_file(path: str) -> str:
    resolved = _resolve_repo_path(path)

    if not resolved.is_file():
        raise FileNotFoundError(path)

    return resolved.read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
    resolved = _resolve_sandbox_path(path)

    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(encoding="utf-8", data=content)

    return f"wrote {path}"


def _normalize_command(args: list[str]) -> list[str]:
    """
    Normalize supported command forms.

    Supported:
        pytest ...
        python -m pytest ...

    The command is normalized without invoking a shell.
    """

    if not args:
        raise ValueError("empty command")

    if (
        len(args) >= 3
        and args[0] == "python"
        and args[1] == "-m"
        and args[2] == "pytest"
    ):
        return ["pytest", *args[3:]]

    return args


def _normalize_find(args: list[str]) -> list[str]:
    """
    Add repository-noise exclusions to a repository-wide find.

    This prevents generated environments and caches such as .venv,
    .git and __pycache__ from flooding the LLM context.

    The model's requested search semantics are otherwise preserved.
    """

    if not args or args[0] != "find":
        return args

    excluded_dirs = {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
    }

    # If the agent already supplied explicit exclusions, leave the
    # command untouched rather than modifying its search semantics.
    if any(
        "prune" == arg
        for arg in args
    ):
        return args

    if len(args) < 2:
        return args

    search_root = args[1]

    if search_root not in {".", "./"}:
        return args

    # Preserve the original find expression while adding exclusions.
    expression = args[2:]

    prefix = ["find", search_root]

    for directory in sorted(excluded_dirs):
        prefix.extend(
            [
                "-path",
                f"./{directory}",
                "-prune",
                "-o",
            ]
        )

    if expression:
        return [
            *prefix,
            *expression,
        ]

    return [
        *prefix,
        "-print",
    ]


def _validate_command(args: list[str]) -> None:
    if not args:
        raise ValueError("empty command")

    allowed_commands = {
        "find",
        "ls",
        "cat",
        "head",
        "pytest",
    }

    if args[0] not in allowed_commands:
        raise ValueError(
            f"command is not allowed: {args[0]}"
        )


def run_command(command: str) -> str:
    if not command.strip():
        raise ValueError("command is empty")

    # We intentionally do NOT invoke a shell.
    #
    # Only the explicitly supported "&&" sequencing operator
    # and "|" pipeline operator are interpreted.
    sequence_parts = [
        part.strip()
        for part in command.split("&&")
    ]

    if any(not part for part in sequence_parts):
        raise ValueError("invalid command sequence")

    current_cwd = REPO_ROOT
    stdin_data = None
    final_result = None

    for sequence_part in sequence_parts:
        pipeline_parts = [
            part.strip()
            for part in sequence_part.split("|")
        ]

        if any(not part for part in pipeline_parts):
            raise ValueError("invalid pipeline")

        for part in pipeline_parts:
            args = shlex.split(part)

            if not args:
                raise ValueError("empty command")

            # --------------------------------------------------------
            # cd
            #
            # Only directories inside sandbox/ may be selected.
            # --------------------------------------------------------
            if args[0] == "cd":
                if len(args) != 2:
                    raise ValueError(
                        "cd requires exactly one directory"
                    )

                target = Path(args[1])

                if target.is_absolute():
                    raise ValueError(
                        "absolute paths are not allowed"
                    )

                resolved = (REPO_ROOT / target).resolve()

                try:
                    resolved.relative_to(
                        SANDBOX_ROOT.resolve()
                    )
                except ValueError:
                    raise ValueError(
                        "cd target must stay inside sandbox"
                    )

                if not resolved.is_dir():
                    raise ValueError(
                        f"cd target is not a directory: {args[1]}"
                    )

                current_cwd = resolved
                continue

            # --------------------------------------------------------
            # Normalize command.
            # --------------------------------------------------------
            args = _normalize_command(args)

            if args[0] == "find":
                args = _normalize_find(args)

            # --------------------------------------------------------
            # Validate executable.
            # --------------------------------------------------------
            _validate_command(args)

            # --------------------------------------------------------
            # Execute without shell.
            # --------------------------------------------------------
            result = subprocess.run(
                args,
                cwd=current_cwd,
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=60,
            )

            final_result = result

            if result.returncode != 0:
                return (
                    f"exit_code={result.returncode}\n"
                    f"stdout:\n{result.stdout}\n"
                    f"stderr:\n{result.stderr}"
                )

            stdin_data = result.stdout

    if final_result is None:
        return (
            "exit_code=0\n"
            "stdout:\n\n"
            "stderr:\n"
        )

    return (
        f"exit_code={final_result.returncode}\n"
        f"stdout:\n{final_result.stdout}\n"
        f"stderr:\n{final_result.stderr}"
    )
