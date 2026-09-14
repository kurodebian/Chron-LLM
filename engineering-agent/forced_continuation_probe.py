from openai import OpenAI


client = OpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key="local",
)


tools = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write a file to the target repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                    "content": {
                        "type": "string",
                    },
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
        },
    }
]


messages = [
    {
        "role": "system",
        "content": "You are an engineering agent.",
    },
    {
        "role": "user",
        "content": "Create the requested marker file.",
    },
    {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "probe-read-001",
                "type": "function",
                "function": {
                    "name": "read_file",
                    "arguments": '{"path":"pytest.ini"}',
                },
            }
        ],
    },
    {
        "role": "tool",
        "tool_call_id": "probe-read-001",
        "content": "[pytest]\npythonpath = .\n",
    },
]


response = client.chat.completions.create(
    model="Qwen3.5-9B",
    messages=messages,
    tools=tools,
    tool_choice={
        "type": "function",
        "function": {
            "name": "write_file",
        },
    },
    temperature=0,
    max_tokens=256,
)

message = response.choices[0].message

print("=== FORCED CONTINUATION ===")
print("finish_reason =", response.choices[0].finish_reason)
print("content =", repr(message.content))
print("tool_calls =", message.tool_calls)