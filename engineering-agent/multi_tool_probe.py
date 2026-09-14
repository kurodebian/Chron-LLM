import json

from openai import OpenAI

from tools import read_file, write_file


client = OpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key="local",
)

tools = [
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
]

messages = [
    {
        "role": "system",
        "content": (
            "You are an engineering agent. "
            "Use repository evidence obtained through tools. "
            "When the requested task is complete, stop."
        ),
    },
    {
        "role": "user",
        "content": (
            "Read pytest.ini from the repository. "
            "After reading it, create agent_probe_marker.txt "
            "with exactly this content:\n"
            "ENGINEERING_AGENT_WRITE_PASS"
        ),
    },
]


for turn in range(4):
    print(f"\n=== TURN {turn + 1} ===")

    if turn == 0:
        tool_choice = "auto"
    else:
        tool_choice = {
            "type": "function",
            "function": {
                "name": "write_file",
            },
        }

    turn_tools = tools if turn == 0 else [tools[1]]

    response = client.chat.completions.create(
        model="Qwen3.5-9B",
        messages=messages,
        tools=turn_tools,
        tool_choice=tool_choice,
        temperature=0,
        max_tokens=512,
    )

    message = response.choices[0].message

    print("finish_reason =", response.choices[0].finish_reason)
    print("content =", repr(message.content))
    print("tool_calls =", message.tool_calls)

    if not message.tool_calls:
        print("=== NO TOOL CALL ===")
        break

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
        name = call.function.name
        arguments = json.loads(call.function.arguments)

        print("EXECUTE:", name, arguments)

        if name == "read_file":
            result = read_file(arguments["path"])

        elif name == "write_file":
            result = write_file(
                arguments["path"],
                arguments["content"],
            )

        else:
            raise RuntimeError(f"unsupported tool: {name}")

        print("RESULT:", repr(result))

        messages.append(
            {
                "role": "tool",
                "tool_call_id": call.id,
                "content": result,
            }
        )