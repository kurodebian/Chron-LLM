#!/usr/bin/env python3
import sys
import os
import json
import urllib.request

API_URL = "http://localhost:8080/v1/chat/completions"

SYSTEM_PROMPT = """You are a deterministic spec compiler for an AI code agent.
Convert the provided human-readable Markdown specification into a ultra-dense, token-optimized Formal IR Spec format.

STRICT COMPILATION RULES:
1. EXCLUDE ALL prose, explanations, conversational filler, and markdown fences.
2. Retain ALL information with ZERO loss: Types, Operations, States, Pre/Post-conditions, Sequence, Invariants (INV), Constraints, and Non-responsibilities.
3. Use strict ASCII syntax: = (assign), -> (transition), : (type/field), | (union), [] (array/list).
4. Output NOTHING except the compiled spec IR.
"""

if len(sys.argv) < 2:
    print("Usage: python3 convert_single_spec.py <path_to_markdown_file>")
    sys.exit(1)

filepath = sys.argv[1]
if not os.path.exists(filepath):
    print(f"Error: File '{filepath}' not found.")
    sys.exit(1)

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

payload = {
    "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": content}
    ],
    "temperature": 0.0
}

req = urllib.request.Request(
    API_URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

print(f"Converting '{filepath}' via Qwen3.5-35B ...")
try:
    with urllib.request.urlopen(req) as res:
        result = json.loads(res.read().decode("utf-8"))
        ir_spec = result["choices"][0]["message"]["content"].strip()
        
        out_path = filepath.replace(".md", ".spec")
        with open(out_path, "w", encoding="utf-8") as f_out:
            f_out.write(ir_spec)
            
        print(f"✓ Converted successfully -> {out_path}")
        print("\n=== GENERATED SPEC (IR) ===\n")
        print(ir_spec)
        print("\n===========================\n")
        print(f"Stats: {len(content)} bytes -> {len(ir_spec)} bytes (-{(1 - len(ir_spec)/len(content))*100:.1f}%)")
except Exception as e:
        print(f"✗ Error: {e}")
