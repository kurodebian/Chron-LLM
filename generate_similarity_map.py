import os
import json
import math
import subprocess
from pathlib import Path
import urllib.request
import urllib.error

SIMILARITY_THRESHOLD = 0.75  # LLM精査に回す類似度閾値

# スキャンから除外するディレクトリ
EXCLUDE_DIRS = {
    ".venv",
    "venv",
    "node_modules",
    ".git",
    "__pycache__",
    "local-backup",
    "build",
}

# デフォルトの埋め込みモデル名
DEFAULT_OLLAMA_MODEL = "hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:Q8_0"


def test_embed_endpoint(url, payload):
    """Embeddings API を叩いて疎通確認"""
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as res:
            return res.status == 200
    except urllib.error.HTTPError as e:
        if e.code in [400, 422]:
            return True
        return False
    except Exception:
        return False


def get_wsl_host_ip():
    """WSL2から見たWindowsホストのIPアドレスを確実に取得"""
    # 1. ip route からデフォルトゲートウェイのIPを取得 (WSL2で最も確実)
    try:
        out = subprocess.check_output("ip route show default", shell=True, text=True)
        tokens = out.split()
        if "via" in tokens:
            return tokens[tokens.index("via") + 1]
        elif len(tokens) >= 3:
            return tokens[2]
    except Exception:
        pass

    # 2. フォールバック: /etc/resolv.conf
    try:
        with open("/etc/resolv.conf", "r") as f:
            for line in f:
                if line.startswith("nameserver"):
                    ip = line.split()[1]
                    if ip != "127.0.0.53":  # systemd-resolved などのスタブIPを除外
                        return ip
    except Exception:
        pass

    return None


def detect_backend():
    """職場（Ollama）と自宅（llama.cpp）の環境を自動検出"""
    ollama_model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    llama_model = os.getenv("LLAMA_EMBED_MODEL", "Fusion711")

    # 接続テスト対象のホストリスト候補構築
    raw_hosts = []

    # 環境変数 OLLAMA_HOST が設定されていれば優先取得＆表記整形
    env_ollama_host = os.getenv("OLLAMA_HOST")
    if env_ollama_host:
        host = env_ollama_host.rstrip("/")
        if not host.startswith("http://") and not host.startswith("https://"):
            host = f"http://{host}"
        if ":" not in host.split("//")[1]:
            host = f"{host}:11434"
        raw_hosts.append(host)

    # WSL2ホストIPを取得して追加
    wsl_host_ip = get_wsl_host_ip()
    if wsl_host_ip:
        raw_hosts.append(f"http://{wsl_host_ip}:11434")

    # ローカルホストの候補
    raw_hosts.extend(["http://localhost:11434", "http://127.0.0.1:11434"])

    # 順序を保ったまま重複を除去
    hosts = list(dict.fromkeys(raw_hosts))

    # 1. Ollama の確認 (OpenAI 互換エンドポイント /v1/embeddings を使用)
    for host in hosts:
        url = f"{host}/v1/embeddings"
        if test_embed_endpoint(url, {"model": ollama_model, "input": "test"}):
            return {
                "embed_url": url,
                "model": ollama_model,
                "env_name": f"Ollama ({host})",
            }

    # 2. llama.cpp の確認 (8081 を優先し、次に 8080 を確認)
    llama_hosts = [
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]
    if wsl_host_ip:
        llama_hosts.extend([f"http://{wsl_host_ip}:8081", f"http://{wsl_host_ip}:8080"])
    llama_hosts = list(dict.fromkeys(llama_hosts))

    for host in llama_hosts:
        url = f"{host}/v1/embeddings"
        if test_embed_endpoint(url, {"model": llama_model, "input": "test"}):
            return {
                "embed_url": url,
                "model": llama_model,
                "env_name": f"llama.cpp ({host})",
            }

    raise RuntimeError(
        "❌ 有効な Embedding バックエンドが見つかりません。\n"
        "   - Ollama が起動しているか確認してください。\n"
        "   - WSL2から接続する場合は、Windows側のOllamaで OLLAMA_HOST=0.0.0.0 の設定が必要な場合があります。"
    )


def scan_target_files(root_dir="."):
    """リポジトリ内の .spec および ir/ 配下のファイルを収集"""
    target_files = []
    for path in Path(root_dir).rglob("*"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue

        if path.is_file() and (path.suffix == ".spec" or "ir" in path.parts):
            if path.suffix == ".bak":
                continue
            target_files.append(str(path))
    return sorted(target_files)


def get_embedding(backend, text, filepath=""):
    """/v1/embeddings 形式で Embedding ベクトルを取得"""
    safe_text = text[:1500]

    payload = {"model": backend["model"], "input": safe_text}

    req = urllib.request.Request(
        backend["embed_url"],
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode("utf-8"))
            if "data" in res and len(res["data"]) > 0 and "embedding" in res["data"][0]:
                return res["data"][0]["embedding"]
            return None

    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8", errors="ignore")
        print(f"HTTP Error {e.code} [{filepath}]: {error_msg}")
        return None
    except Exception as e:
        print(f"Embedding error [{filepath}]: {e}")
        return None


def cosine_similarity(v1, v2):
    """コサイン類似度の計算"""
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)


def main():
    # 1. バックエンド自動判定
    try:
        backend = detect_backend()
        print(f"⚙️  バックエンド検出: {backend['env_name']}")
        print(f"🎯 使用モデル: {backend['model']}")
    except RuntimeError as e:
        print(e)
        return

    # 2. ファイルスキャン
    files = scan_target_files()
    print(f"📁 スキャン対象: {len(files)} ファイル")

    # 3. ベクトルデータの生成
    embeddings = {}
    for i, filepath in enumerate(files, 1):
        print(f"[{i}/{len(files)}] ベクトル化中: {filepath}")
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            vec = get_embedding(backend, content, filepath)
            if vec:
                embeddings[filepath] = vec
        except Exception as e:
            print(f"Skip {filepath}: {e}")

    # 4. 類似度ペアの抽出
    print("\n🔍 類似度判定マトリクスを計算中...")
    file_list = list(embeddings.keys())
    candidate_pairs = []

    for i in range(len(file_list)):
        for j in range(i + 1, len(file_list)):
            f1, f2 = file_list[i], file_list[j]
            sim = cosine_similarity(embeddings[f1], embeddings[f2])

            if sim >= SIMILARITY_THRESHOLD:
                candidate_pairs.append(
                    {"file_a": f1, "file_b": f2, "similarity": round(sim, 4)}
                )

    candidate_pairs.sort(key=lambda x: x["similarity"], reverse=True)

    # 5. 結果の保存
    output_data = {
        "environment": backend["env_name"],
        "model_used": backend["model"],
        "total_files_scanned": len(files),
        "total_candidate_pairs": len(candidate_pairs),
        "threshold": SIMILARITY_THRESHOLD,
        "pairs": candidate_pairs,
    }

    output_path = "spec_similarity_map.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完了: {len(candidate_pairs)} 組の重複・類似候補ペアを検出しました。")
    print(f"📄 結果ファイル: {output_path}")


if __name__ == "__main__":
    main()
