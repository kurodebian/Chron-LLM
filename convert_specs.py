#!/usr/bin/env python3
import glob
import json
import os
import sys
import time
import urllib.error
import urllib.request


def get_win_host_ip():
  """WSL2 環境から Windows ホストの IP アドレスを取得する"""
  try:
    with os.popen("ip route show default | awk '{print $3}'") as stream:
      ip = stream.read().strip()
      if ip:
        return ip
  except Exception:
    pass
  return None


def fetch_v1_models(base_url):
  """/v1/models からモデル名を取得する"""
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
  """起動中の LLM サーバー (llama-server または Ollama) を自動検出する"""
  env_model = os.getenv("MODEL_NAME")

  # 1. API_URL が明示されている場合
  env_url = os.getenv("API_URL")
  if env_url:
    return env_url, env_model or "default"

  # 2. OLLAMA_HOST が明示されている場合
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

  # ----------------------------------------------------
  # 判定 A: llama.cpp (llama-server) のチェック (:8080)
  # ----------------------------------------------------
  for host in hosts:
    base_url = f"{host}:8080"
    try:
      req = urllib.request.Request(f"{base_url}/health")
      with urllib.request.urlopen(req, timeout=2.0) as res:
        if res.status == 200:
          model = env_model or fetch_v1_models(base_url) or "default"
          print(
              f"[Auto-Detect] llama.cpp (llama-server) 検出: {base_url} (モデル:"
              f" {model})"
          )
          return f"{base_url}/v1/chat/completions", model
    except Exception:
      pass

  # ----------------------------------------------------
  # 判定 B: Ollama のチェック (:11434)
  # ----------------------------------------------------
  for host in hosts:
    base_url = f"{host}:11434"
    try:
      # Ollama 固有のエンドポイント /api/tags で確認
      req = urllib.request.Request(f"{base_url}/api/tags")
      with urllib.request.urlopen(req, timeout=2.0) as res:
        if res.status == 200:
          data = json.loads(res.read().decode("utf-8"))
          models = [
              m.get("name") for m in data.get("models", []) if m.get("name")
          ]
          selected_model = env_model or (models[0] if models else "default")
          print(
              f"[Auto-Detect] Ollama 検出: {base_url} (モデル:"
              f" {selected_model})"
          )
          return f"{base_url}/v1/chat/completions", selected_model
    except Exception:
      pass

  # ----------------------------------------------------
  # 判定 C: その他の OpenAI 互換サーバー (/v1/models)
  # ----------------------------------------------------
  for host in hosts:
    for port in [8080, 11434]:
      base_url = f"{host}:{port}"
      model = fetch_v1_models(base_url)
      if model:
        selected_model = env_model or model
        print(
            f"[Auto-Detect] OpenAI互換 API 検出: {base_url} (モデル:"
            f" {selected_model})"
        )
        return f"{base_url}/v1/chat/completions", selected_model

  # どちらも検出できない場合のデフォルト
  default_url = "http://localhost:8080/v1/chat/completions"
  print(
      "[Warn] サーバーが自動検出できませんでした。デフォルト"
      f" ({default_url}) で試行します。"
  )
  return default_url, env_model or "default"


# バックエンドの自動検出
API_URL, MODEL_NAME = detect_backend()

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

# 第一引数でターゲットディレクトリを指定可能（未指定時は llama-agent）
target_input = sys.argv[1] if len(sys.argv) > 1 else "llama-agent"
SRC_DIR = os.path.abspath(
    os.path.join(BASE_DIR, target_input)
    if not os.path.isabs(target_input)
    else target_input
)

# 対象フォルダ自体が "ir" で終わる場合は直下に、それ以外は ir サブフォルダを作成
if os.path.basename(SRC_DIR.rstrip("/\\")) == "ir":
  OUT_DIR = SRC_DIR
else:
  OUT_DIR = os.path.join(SRC_DIR, "ir")

os.makedirs(OUT_DIR, exist_ok=True)


def encode_file(filepath, current_idx, total_files):
  filename = os.path.basename(filepath)
  out_path = os.path.join(OUT_DIR, filename.replace(".md", ".spec"))

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

      ir_spec = "".join(chunks).strip()
      elapsed = time.time() - start_time

      if not ir_spec:
        raise ValueError("Received empty content from API")

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
        print(
            f"\n   [Retry {attempt}/{MAX_RETRIES} after error: {e}] {prefix}",
            end="",
            flush=True,
        )
        time.sleep(5 * attempt)
      else:
        print(f"\n ✗ Error: {e} (Failed after {MAX_RETRIES} attempts)")


if __name__ == "__main__":
  md_files = sorted(glob.glob(os.path.join(SRC_DIR, "*.md")))
  total_files = len(md_files)
  print(f"Target directory: {SRC_DIR}")
  print(f"Output directory: {OUT_DIR}")
  print(f"Target API:       {API_URL} (Model: {MODEL_NAME})")
  print(f"Found {total_files} markdown files.\n")

  for idx, f in enumerate(md_files, start=1):
    encode_file(f, idx, total_files)