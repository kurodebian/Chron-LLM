#!/usr/bin/env python3
import glob
import json
import os
import sys
import time
import urllib.error
import urllib.request


def get_win_host_ip():
    try:
        with os.popen("ip route show default | awk '{print $3}'") as stream:
            ip = stream.read().strip()
            if ip:
                return ip
    except Exception:
        pass
    return None


def fetch_v1_models(base_url):
    try:
        req = urllib.request.Request(f"{base_url}/v1/models")
        with urllib.request.urlopen(req, timeout=2.0) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                models = [m.get("id") for m in data.get("data", []) if m.get("id")]
                return models[0] if models else None
    except Exception:
        pass
    return None


def detect_backend():
    env_model = os.getenv("MODEL_NAME")

    env_url = os.getenv("API_URL")
    if env_url:
        return env_url, env_model or "default"

    ollama_host = os.getenv("OLLAMA_HOST")
    if ollama_host:
        base = ollama_host.rstrip("/")
        if not base.startswith("http://") and not base.startswith("https://"):
            base = f"http://{base}"
        api_endpoint = (
            f"{base}/v1/chat/completions"
            if not base.endswith("/v1")
            else f"{base}/chat/completions"
        )
        model = env_model or fetch_v1_models(base) or "default"
        return api_endpoint, model

    win_ip = get_win_host_ip()
    hosts = ["http://localhost", "http://127.0.0.1"]
    if win_ip:
        hosts.append(f"http://{win_ip}")

    for host in hosts:
        base_url = f"{host}:8080"
        try:
            req = urllib.request.Request(f"{base_url}/health")
            with urllib.request.urlopen(req, timeout=2.0) as res:
                if res.status == 200:
                    model = env_model or fetch_v1_models(base_url) or "default"
                    print(
                        f"[Auto-Detect] llama.cpp detected: {base_url} (model: {model})"
                    )
                    return f"{base_url}/v1/chat/completions", model
        except Exception:
            pass

    for host in hosts:
        base_url = f"{host}:11434"
        try:
            req = urllib.request.Request(f"{base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=2.0) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode("utf-8"))
                    models = [
                        m.get("name") for m in data.get("models", []) if m.get("name")
                    ]
                    selected_model = env_model or (models[0] if models else "default")
                    print(
                        f"[Auto-Detect] Ollama detected: {base_url} (model: {selected_model})"
                    )
                    return f"{base_url}/v1/chat/completions", selected_model
        except Exception:
            pass

    for host in hosts:
        for port in [8080, 11434]:
            base_url = f"{host}:{port}"
            model = fetch_v1_models(base_url)
            if model:
                selected_model = env_model or model
                print(
                    f"[Auto-Detect] OpenAI-compatible API: {base_url} (model: {selected_model})"
                )
                return f"{base_url}/v1/chat/completions", selected_model

    default_url = "http://localhost:8080/v1/chat/completions"
    print(f"[Warn] No server detected. Using default: {default_url}")
    return default_url, env_model or "default"


API_URL, MODEL_NAME = detect_backend()

TIMEOUT_SEC = 600
MAX_RETRIES = 3

SYSTEM_PROMPT = """You are a deterministic compiler.
Convert the provided Common Lisp source code into a structured, human-readable Markdown specification.

RULES:
1. Extract: purpose, public API, functions, parameters, return values, types, invariants, and important control flow.
2. Use Markdown headings and lists.
3. Include short code excerpts only when necessary.
4. Do NOT invent functionality not present in the code.
5. Output ONLY the Markdown spec.
"""

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

target_input = sys.argv[1] if len(sys.argv) > 1 else "lisp-src"
SRC_DIR = os.path.abspath(
    os.path.join(BASE_DIR, target_input)
    if not os.path.isabs(target_input)
    else target_input
)

OUT_DIR = os.path.join(SRC_DIR, "md")
os.makedirs(OUT_DIR, exist_ok=True)


def encode_file(filepath, current_idx, total_files):
    filename = os.path.basename(filepath)
    out_path = os.path.join(OUT_DIR, filename.replace(".lisp", ".md"))

    prefix = f"[{current_idx:2d}/{total_files:2d}] {filename:<28} -> "

    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        print(f"{prefix}(SKIP: Already exists)")
        return

    print(f"{prefix}", end="", flush=True)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        "temperature": 0.0,
        "stream": True,
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            start_time = time.time()
            chunks = []

            with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as res:
                for line in res:
                    line_str = line.decode("utf-8").strip()
                    if line_str.startswith("data: ") and line_str != "data: [DONE]":
                        try:
                            chunk_data = json.loads(line_str[6:])
                            delta = chunk_data["choices"][0]["delta"].get("content", "")
                            if delta:
                                chunks.append(delta)
                                print(".", end="", flush=True)
                        except json.JSONDecodeError:
                            pass

            md_spec = "".join(chunks).strip()
            elapsed = time.time() - start_time

            if not md_spec:
                raise ValueError("Received empty content from API")

            tmp_path = out_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f_out:
                f_out.write(md_spec)
            os.replace(tmp_path, out_path)

            print(f" ✓ ({len(md_spec):5d} bytes, {elapsed:.1f}s)")
            return

        except Exception as e:
            if attempt < MAX_RETRIES:
                print(
                    f"\n   [Retry {attempt}/{MAX_RETRIES} after error: {e}] {prefix}",
                    end="",
                    flush=True,
                )
                time.sleep(5 * attempt)
            else:
                print(f"\n ✗ Error: {e} (Failed after {MAX_RETRIES} attempts)")


if __name__ == "__main__":
    lisp_files = sorted(glob.glob(os.path.join(SRC_DIR, "*.lisp")))
    total_files = len(lisp_files)
    print(f"Target directory: {SRC_DIR}")
    print(f"Output directory: {OUT_DIR}")
    print(f"Target API:       {API_URL} (Model: {MODEL_NAME})")
    print(f"Found {total_files} Lisp files.\n")

    for idx, f in enumerate(lisp_files, start=1):
        encode_file(f, idx, total_files)
