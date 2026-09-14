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
            "description": "Write a file in the target repository.",
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
            "Do not invent repository contents. "
            "You may modify files only when explicitly requested."
        ),
    },
    {
        "role": "user",
        "content": (
            "Inspect loop.py using read_file. "
            "Then create a new repository file named "
            "agent_probe_marker.txt containing exactly:\n"
            "ENGINEERING_AGENT_WRITE_PASS"
        ),
    },
]


# === TURN 1: read_file selection ===
response1 = client.chat.completions.create(
    model="Qwen3.5-9B",
    messages=messages,
    tools=tools,
    tool_choice="auto",
    temperature=0,
    max_tokens=512,
)

message1 = response1.choices[0].message

print("=== TURN 1 LLM ===")
print(message1.content or "")
print("finish_reason =", response1.choices[0].finish_reason)
print("tool_calls =", message1.tool_calls)

# Tool call required
if not message1.tool_calls:
    print("ERROR: TURN 1 produced no tool call")
    exit(1)

# Execute read_file
call1 = message1.tool_calls[0]
args1 = json.loads(call1.function.arguments)

print("=== EXECUTE read_file ===")
print(args1)

result1 = read_file(args1["path"])
print("=== read_file RESULT ===")
print(result1)

# Append tool result
messages.append(
    {
        "role": "assistant",
        "content": message1.content or "",
        "tool_calls": [
            {
                "id": call1.id,
                "type": "function",
                "function": {
                    "name": call1.function.name,
                    "arguments": call1.function.arguments,
                },
            }
        ],
    }
)

messages.append(
    {
        "role": "tool",
        "tool_call_id": call1.id,
        "content": result1,
    }
)


# === TURN 2: DIAGNOSTIC ===
response2 = client.chat.completions.create(
    model="Qwen3.5-9B",
    messages=messages,
    tools=tools,
    tool_choice="auto",
    temperature=0,
    max_tokens=512,
)

message2 = response2.choices[0].message

print()
print("=== SECOND RESPONSE DEBUG ===")
print("finish_reason =", response2.choices[0].finish_reason)
print("content =", repr(message2.content))
print("tool_calls =", message2.tool_calls)
print("usage =", response2.usage)

if message2.tool_calls:
    print("=== SECOND TOOL CALLS ===")
    for call in message2.tool_calls:
        print("tool =", call.function.name)
        print("arguments =", call.function.arguments)
else:
    print("NO SECOND TOOL CALL")
