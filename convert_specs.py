#!/usr/bin/env python3
import os
import glob
import json
import time
import urllib.request
import urllib.error

# llama-server の OpenAI 互換エンドポイント (デフォルトポート 8080)
API_URL = "http://localhost:8080/v1/chat/completions"

# Radeon 890M + 27B モデルでの Prompt Eval 時間を考慮し 600 秒 (10分) に延長
TIMEOUT_SEC = 600
MAX_RETRIES = 3

SYSTEM_PROMPT = """You are a deterministic spec compiler for an AI code agent.
Convert the provided human-readable Markdown specification into a ultra-dense, token-optimized Formal IR Spec format.

STRICT RULES:
1. EXCLUDE ALL prose, explanations, conversational filler, and markdown fences.
2. Retain ONLY: Types, Operations, State, Pre/Post-conditions, and Invariants (INV).
3. Use strict ASCII syntax: = (assign), -> (transition), : (type/field), | (union), [] (array/list).
4. Output NOTHING except the compiled spec IR.
"""

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "llama-agent")
OUT_DIR = os.path.join(SRC_DIR, "ir")

os.makedirs(OUT_DIR, exist_ok=True)

def encode_file(filepath, current_idx, total_files):
    filename = os.path.basename(filepath)
    out_path = os.path.join(OUT_DIR, filename.replace(".md", ".spec"))
    
    prefix = f"[{current_idx:2d}/{total_files:2d}] {filename:<28} -> "
    
    # すでに正常生成済み（サイズ > 0）の場合は自動スキップ
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        print(f"{prefix}(SKIP: Already exists)")
        return

    print(f"{prefix}", end="", flush=True)
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ],
        "temperature": 0.0,
        "stream": True
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            start_time = time.time()
            chunks = []
            
            with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as res:
                # SSE (Server-Sent Events) を1行ずつリアルタイム受信
                for line in res:
                    line_str = line.decode("utf-8").strip()
                    if line_str.startswith("data: ") and line_str != "data: [DONE]":
                        try:
                            chunk_data = json.loads(line_str[6:])
                            delta = chunk_data["choices"][0]["delta"].get("content", "")
                            if delta:
                                chunks.append(delta)
                                # トークン生成ごとにドットを出力
                                print(".", end="", flush=True)
                        except json.JSONDecodeError:
                            pass
            
            ir_spec = "".join(chunks).strip()
            elapsed = time.time() - start_time
            
            if not ir_spec:
                raise ValueError("Received empty content from API")

            # アトミック書き込み（一時ファイルから置換）
            tmp_path = out_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f_out:
                f_out.write(ir_spec)
            os.replace(tmp_path, out_path)
            
            orig_size = len(content)
            new_size = len(ir_spec)
            ratio = (1 - new_size / orig_size) * 100 if orig_size > 0 else 0
            
            print(f" ✓ ({new_size:5d} bytes, -{ratio:.1f}%, {elapsed:.1f}s)")
            return

        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"\n   [Retry {attempt}/{MAX_RETRIES} after error: {e}] {prefix}", end="", flush=True)
                time.sleep(5 * attempt)
            else:
                print(f"\n ✗ Error: {e} (Failed after {MAX_RETRIES} attempts)")

if __name__ == "__main__":
    md_files = sorted(glob.glob(os.path.join(SRC_DIR, "*.md")))
    total_files = len(md_files)
    print(f"Target directory: {SRC_DIR}")
    print(f"Found {total_files} markdown files.\n")
    
    for idx, f in enumerate(md_files, start=1):
        encode_file(f, idx, total_files)