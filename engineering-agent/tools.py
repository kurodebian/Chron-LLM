from pathlib import Path
import subprocess
import shlex


REPO_ROOT = Path.home() / "Chron-LLM" / "loop-engine"
SANDBOX_ROOT = REPO_ROOT / "sandbox"


def _resolve_repo_path(path: str) -> Path:
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
    resolved = _resolve_repo_path(path)

    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(content, encoding="utf-8")

    return f"wrote {path}"


def run_command(command: str) -> str:
    if not command.strip():
        raise ValueError("command is empty")

    parts = shlex.split(command)

    if not parts:
        raise ValueError("command is empty")

    allowed_commands = {"find", "ls", "cat", "pytest"}

    if parts[0] not in allowed_commands:
        raise ValueError(
            f"command is not allowed: {parts[0]}"
        )

    # Shell execution is deliberately disabled.
    # This prevents arbitrary shell commands, redirection,
    # command substitution, and chained commands.
    forbidden_tokens = {
        ";",
        "&&",
        "||",
        "|",
        ">",
        ">>",
        "<",
        "$(",
        "`",
    }

    if any(token in forbidden_tokens for token in parts):
        raise ValueError("shell operators are not allowed")

    result = subprocess.run(
        parts,
        cwd=SANDBOX_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )

    output = (
        f"exit_code={result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    return output