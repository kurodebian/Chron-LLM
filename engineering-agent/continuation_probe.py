from openai import OpenAI


client = OpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key="local",
)


messages = [
    {
        "role": "system",
        "content": (
            "You are an engineering agent. "
            "Respond concisely."
        ),
    },
    {
        "role": "user",
        "content": (
            "Reply with exactly the text: "
            "CONTINUATION_PASS"
        ),
    },
]


response = client.chat.completions.create(
    model="Qwen3.5-9B",
    messages=messages,
    temperature=0,
    max_tokens=64,
)

message = response.choices[0].message

print("=== NORMAL COMPLETION ===")
print("finish_reason =", response.choices[0].finish_reason)
print("content =", repr(message.content))
print("tool_calls =", message.tool_calls)