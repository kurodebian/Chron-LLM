import os
import json
import urllib.request

def http_ok(url):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=1) as res:
            return res.status == 200
    except:
        return False

def detect_embedding_api():
    # 1. OLLAMA_HOST が指定されている場合
    ollama_host = os.getenv("OLLAMA_HOST")
    if ollama_host:
        base = ollama_host.rstrip("/")
        url = f"{base}/api/embeddings"
        return url, "nomic-embed-text"

    # 2. Ollama の /api/tags が生きているか
    for host in ["http://localhost:11434", "http://127.0.0.1:11434"]:
        if http_ok(f"{host}/api/tags"):
            return f"{host}/api/embeddings", "nomic-embed-text"

    # 3. llama.cpp の /v1/embeddings が生きているか
    for host in ["http://localhost:8081", "http://127.0.0.1:8081"]:
        if http_ok(f"{host}/v1/embeddings"):
            return f"{host}/v1/embeddings", os.getenv("LLAMA_EMBED_MODEL")

    raise RuntimeError("No embedding backend found")

def detect_inference_api():
    # 1. Ollama の /api/generate
    for host in ["http://localhost:11434", "http://127.0.0.1:11434"]:
        if http_ok(f"{host}/api/generate"):
            return f"{host}/api/generate"

    # 2. llama.cpp の /v1/chat/completions
    for host in ["http://localhost:8080", "http://127.0.0.1:8080"]:
        if http_ok(f"{host}/v1/chat/completions"):
            return f"{host}/v1/chat/completions"

    raise RuntimeError("No inference backend found")

