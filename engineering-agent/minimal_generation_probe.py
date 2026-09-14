from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key="local",
)

tests = [
    ("A", "Say exactly: HELLO"),
    ("B", "Return exactly one JSON object: {\"ok\": true}"),
    ("C", "What is 2 + 2? Answer with only the number."),
]

for name, prompt in tests:
    print(f"\n=== TEST {name} ===")

    response = client.chat.completions.create(
        model="Qwen3.5-9B",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
        max_tokens=256,
    )

    choice = response.choices[0]

    print("finish_reason =", choice.finish_reason)
    print("content =", repr(choice.message.content))
    print("tool_calls =", choice.message.tool_calls)