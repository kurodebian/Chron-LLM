import os
import json
import urllib.request
import subprocess


def http_ok(url):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=1) as res:
            return res.status == 200
    except:
        return False


def get_windows_ip():
    try:
        out = subprocess.check_output(["ipconfig.exe"]).decode("utf-8", errors="ignore")
        for line in out.splitlines():
            if "IPv4 Address" in line or "IPv4 アドレス" in line:
                return line.split(":")[1].strip()
    except:
        pass
    return None


def detect_inference_api():
    # 1. Ollama (WSL2)
    for host in ["http://localhost:11434", "http://127.0.0.1:11434"]:
        if http_ok(f"{host}/api/generate"):
            return f"{host}/api/generate"

    # 2. llama.cpp (WSL2)
    for host in ["http://localhost:8080", "http://127.0.0.1:8080"]:
        if http_ok(f"{host}/v1/chat/completions"):
            return f"{host}/v1/chat/completions"

    # 3. Ollama (Windows host)
    win_ip = get_windows_ip()
    if win_ip:
        host = f"http://{win_ip}:11434"
        if http_ok(f"{host}/api/generate"):
            return f"{host}/api/generate"

    raise RuntimeError("No inference backend found")


# -------------------------
# 実行部（表示用）
# -------------------------
if __name__ == "__main__":
    print("🔍 Detecting inference backend...")

    try:
        url = detect_inference_api()
        print(f"✅ Inference backend detected: {url}")
    except Exception as e:
        print(f"❌ Detection failed: {e}")
