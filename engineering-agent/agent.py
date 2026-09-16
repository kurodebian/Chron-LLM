import hashlib
import json
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from tools import read_file, run_command, write_file


@dataclass(frozen=True)
class AgentResult:
    completed: bool
    turns: int
    final_message: str


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read a file from the target repository. "
                "Repository files are readable, but repository state must be "
                "treated as authoritative evidence."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write a file inside the sandbox directory only. "
                "Files outside sandbox/ cannot be modified."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": (
                "Run an allowed repository command. "
                "The command executes from the repository root. "
                "Use repository-relative paths such as sandbox/task.py."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                },
                "required": ["command"],
                "additionalProperties": False,
            },
        },
    },
]


TOOL_EXECUTORS = {
    "read_file": lambda args: read_file(args["path"]),
    "write_file": lambda args: write_file(
        args["path"],
        args["content"],
    ),
    "run_command": lambda args: run_command(args["command"]),
}


class EngineeringAgent:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080/v1",
        model: str = "Qwen3.5-9B",
        max_turns: int = 20,
    ):
        self.client = OpenAI(
            base_url=base_url,
            api_key="local",
        )
        self.model = model
        self.max_turns = max_turns

    def _execute_tool(
        self,
        name: str,
        arguments: str,
        protected_test_baseline: dict[str, str] | None = None,
    ) -> str:
        data = json.loads(arguments)

        if name == "write_file":
            return write_file(
                data["path"],
                data["content"],
                protected_paths=set(
                    protected_test_baseline or {}
                ),
            )

        executor = TOOL_EXECUTORS.get(name)
        if executor is None:
            raise RuntimeError(f"unsupported tool: {name}")

        return executor(data)

    def _capture_protected_test_baseline(self) -> dict[str, str]:
        """
        Capture the trusted baseline of existing sandbox tests.

        The baseline is captured once before the agent is allowed
        to modify the sandbox and is retained in controller memory.
        """
        result = run_command(
            'find sandbox -type f \\( -name "test_*.py" -o -name "*_test.py" \\)'
        )

        if "exit_code=0" not in result:
            raise RuntimeError(
                "failed to discover protected test files"
            )

        paths = []

        stdout_marker = "stdout:\n"
        stderr_marker = "\nstderr:\n"

        if stdout_marker in result:
            stdout = result.split(stdout_marker, 1)[1]
            if stderr_marker in stdout:
                stdout = stdout.split(stderr_marker, 1)[0]

            paths = [
                line.strip()
                for line in stdout.splitlines()
                if line.strip()
            ]

        baseline = {}

        for path in paths:
            content = read_file(path)
            digest = hashlib.sha256(
                content.encode("utf-8")
            ).hexdigest()
            baseline[path] = digest

        return baseline

    def _check_protected_test_integrity(
        self,
        baseline: dict[str, str],
    ) -> tuple[bool, str]:
        """
        Verify that protected baseline tests were not modified,
        deleted, or replaced.
        """
        result = run_command(
            'find sandbox -type f \\( -name "test_*.py" -o -name "*_test.py" \\)'
        )

        if "exit_code=0" not in result:
            return False, (
                "REGRESSION_SAFETY_FAIL\n"
                "Unable to enumerate protected tests.\n"
                f"{result}"
            )

        stdout_marker = "stdout:\n"
        stderr_marker = "\nstderr:\n"

        stdout = ""
        if stdout_marker in result:
            stdout = result.split(stdout_marker, 1)[1]
            if stderr_marker in stdout:
                stdout = stdout.split(stderr_marker, 1)[0]

        current_paths = {
            line.strip()
            for line in stdout.splitlines()
            if line.strip()
        }

        baseline_paths = set(baseline)

        deleted = sorted(
            baseline_paths - current_paths
        )

        unexpected_replacements = sorted(
            current_paths - baseline_paths
        )

        modified = []

        for path in sorted(
            baseline_paths & current_paths
        ):
            content = read_file(path)
            digest = hashlib.sha256(
                content.encode("utf-8")
            ).hexdigest()

            if digest != baseline[path]:
                modified.append(path)

        if deleted or modified or unexpected_replacements:
            return False, (
                "REGRESSION_SAFETY_FAIL\n"
                "Protected test baseline integrity violation.\n"
                f"deleted={deleted}\n"
                f"modified={modified}\n"
                f"unexpected_test_files={unexpected_replacements}\n"
            )

        return True, (
            "REGRESSION_SAFETY_PASS\n"
            "Protected test baseline is unchanged.\n"
        )

    def _quality_gate(
        self,
        protected_test_baseline: dict[str, str],
    ) -> tuple[bool, str]:
        """
        External quality gate.

        Completion requires both:
        - protected baseline integrity
        - actual passing pytest execution

        The LLM's final message is never authoritative.
        """

        integrity_passed, integrity_result = (
            self._check_protected_test_integrity(
                protected_test_baseline
            )
        )

        if not integrity_passed:
            return False, integrity_result

        try:
            result = run_command(
                "python -m pytest sandbox/ -v"
            )
        except Exception as exc:
            return (
                False,
                (
                    "QUALITY_GATE_ERROR\n"
                    f"error_type={type(exc).__name__}\n"
                    f"error={exc}"
                ),
            )

        if "exit_code=0" not in result:
            return False, (
                "QUALITY_GATE_FAIL\n"
                "pytest did not exit successfully.\n"
                f"{result}"
            )

        if "collected 0 items" in result:
            return False, (
                "QUALITY_GATE_FAIL\n"
                "pytest collected zero tests.\n"
                f"{result}"
            )

        if "passed" not in result:
            return False, (
                "QUALITY_GATE_FAIL\n"
                "pytest did not report a passing test result.\n"
                f"{result}"
            )

        return True, (
            "QUALITY_GATE_PASS\n"
            "Protected baseline integrity verified.\n"
            "pytest completed successfully with passing tests.\n"
            f"{result}"
        )

    def run(self, objective: str) -> AgentResult:
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "You are an autonomous repository engineering agent.\n"
                    "\n"
                    "Your responsibility is to achieve the user's engineering "
                    "objective by inspecting repository evidence, understanding "
                    "the current implementation, determining gaps, designing "
                    "changes, implementing them, and verifying the result.\n"
                    "\n"
                    "You decide the implementation sequence autonomously. "
                    "Do not ask the human to prescribe individual coding steps "
                    "unless a genuine external decision is required.\n"
                    "\n"
                    "Use repository tools for evidence. Do not claim that a "
                    "change or verification occurred unless the corresponding "
                    "tool operation actually succeeded.\n"
                    "\n"
                    "The repository state is authoritative. LLM output itself "
                    "is not repository truth.\n"
                    "\n"
                    "You may inspect repository files, but write operations "
                    "are restricted to the sandbox directory.\n"
                    "\n"
                    "When the objective and quality requirements are actually "
                    "satisfied, stop and report completion."
                ),
            },
            {
                "role": "user",
                "content": objective,
            },
        ]

        protected_test_baseline = (
            self._capture_protected_test_baseline()
        )

        for turn in range(1, self.max_turns + 1):
            available_tools = TOOLS

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=available_tools,
                tool_choice="auto",
                temperature=0,
                max_tokens=1024,
            )

            message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            print(f"\n=== TURN {turn} ===")
            print("finish_reason =", finish_reason)
            print("content =", repr(message.content))
            print("tool_calls =", message.tool_calls)

            if message.tool_calls:
                assistant_tool_calls = []

                for call in message.tool_calls:
                    assistant_tool_calls.append(
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments,
                            },
                        }
                    )

                messages.append(
                    {
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": assistant_tool_calls,
                    }
                )

                for call in message.tool_calls:
                    print(
                        "EXECUTE:",
                        call.function.name,
                        call.function.arguments,
                    )

                    try:
                        result = self._execute_tool(
                            call.function.name,
                            call.function.arguments,
                            protected_test_baseline,
                        )
                    except Exception as exc:
                        result = (
                            "TOOL_EXECUTION_ERROR\n"
                            f"error_type={type(exc).__name__}\n"
                            f"error={exc}\n"
                            "The tool call failed. Diagnose the error and retry "
                            "with a corrected tool call if the objective still "
                            "requires it."
                        )

                    print("RESULT:", repr(result))

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": result,
                        }
                    )

                continue

            content = message.content or ""

            quality_passed, quality_result = (
                self._quality_gate(
                    protected_test_baseline
                )
            )

            print("=== EXTERNAL QUALITY GATE ===")
            print("passed =", quality_passed)
            print("result =", repr(quality_result))

            if quality_passed:
                return AgentResult(
                    completed=True,
                    turns=turn,
                    final_message=content,
                )

            messages.append(
                {
                    "role": "user",
                    "content": (
                        "The external quality gate has not passed.\n"
                        f"{quality_result}\n"
                        "Do not claim completion. Continue the engineering "
                        "task, diagnose the remaining issue, make any "
                        "necessary changes, and re-test."
                    ),
                }
            )

            continue

        return AgentResult(
            completed=False,
            turns=self.max_turns,
            final_message="maximum agent turns reached",
        )
