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
            "description": "Read a file from the target repository.",
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
            "description": "Write a file to the target repository.",
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
                "Run an allowed repository test command. "
                "The command executes inside the sandbox."
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

    def _execute_tool(self, name: str, arguments: str) -> str:
        data = json.loads(arguments)

        executor = TOOL_EXECUTORS.get(name)
        if executor is None:
            raise RuntimeError(f"unsupported tool: {name}")

        return executor(data)

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
                    "When the objective and quality requirements are actually "
                    "satisfied, stop and report completion."
                ),
            },
            {
                "role": "user",
                "content": objective,
            },
        ]


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

                    result = self._execute_tool(
                        call.function.name,
                        call.function.arguments,
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

            if content.strip():
                return AgentResult(
                    completed=True,
                    turns=turn,
                    final_message=content,
                )

            print("=== EMPTY ASSISTANT RESPONSE ===")

            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Continue the engineering task. "
                        "Do not stop with an empty response. "
                        "Use repository tools when further work is required."
                    ),
                }
            )

            last_tool_name = None

        return AgentResult(
            completed=False,
            turns=self.max_turns,
            final_message="maximum agent turns reached",
        )
