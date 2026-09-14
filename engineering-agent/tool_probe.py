from openai import OpenAI


client = OpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key="local",
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file inside the target repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Repository-relative file path.",
                    }
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    }
]

response = client.chat.completions.create(
    model="Qwen3.5-9B",
    messages=[
        {
            "role": "system",
            "content": (
                "You are an engineering agent. "
                "When repository information is required, use the available tool."
            ),
        },
        {
            "role": "user",
            "content": (
                "Inspect the repository and determine whether "
                "loop.py exists. Use the read_file tool."
            ),
        },
    ],
    tools=tools,
    tool_choice="auto",
    temperature=0,
    max_tokens=256,
    extra_body={
        "chat_template_kwargs": {
            "enable_thinking": False
        }
    },
)

message = response.choices[0].message

print("=== CONTENT ===")
print(message.content)

print("=== TOOL CALLS ===")
print(message.tool_calls)
