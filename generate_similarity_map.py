import os
import json
import math
from pathlib import Path
import urllib.request
import urllib.error

SIMILARITY_THRESHOLD = 0.75  # LLM精査に回す類似度閾値

# スキャンから除外するディレクトリ
EXCLUDE_DIRS = {".venv", "venv", "node_modules", ".git", "__pycache__", "local-backup", "build"}

def test_embed_endpoint(url, payload):
    """実際に Embeddings API を叩いて 501 (Not Implemented) でないかテスト"""
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as res:
            return res.status == 200
    except urllib.error.HTTPError as e:
        # 400 (Bad Request) 等ならエンドポイント自体は機能している
        if e.code in [400, 422]:
            return True
        return False
    except Exception:
        return False

def detect_backend():
    """職場（Ollama）と自宅（llama.cpp）の環境を自動検出"""
    # 1. 環境変数 OLLAMA_HOST がある場合
    ollama_host = os.getenv("OLLAMA_HOST")
    ollama_model = os.getenv("OLLAMA_MODEL", "nomic-embed-text")

    if ollama_host:
        base = ollama_host.rstrip("/")
        url = f"{base}/api/embeddings"
        if test_embed_endpoint(url, {"model": ollama_model, "prompt": "test"}):
            return {
                "type": "ollama",
                "embed_url": url,
                "model": ollama_model,
                "env_name": f"職場 (OLLAMA_HOST: {ollama_host})"
            }

    # 2. Ollama ローカル確認 (11434)
    for host in ["http://localhost:11434", "http://127.0.0.1:11434"]:
        url = f"{host}/api/embeddings"
        if test_embed_endpoint(url, {"model": ollama_model, "prompt": "test"}):
            return {
                "type": "ollama",
                "embed_url": url,
                "model": ollama_model,
                "env_name": "職場 (Ollama Local)"
            }

    # 3. llama.cpp 確認 (8081 を優先し、次に 8080 を確認)
    llama_model = os.getenv("LLAMA_EMBED_MODEL", "Fusion711")
    for host in ["http://localhost:8081", "http://127.0.0.1:8081", "http://localhost:8080", "http://127.0.0.1:8080"]:
        url = f"{host}/v1/embeddings"
        if test_embed_endpoint(url, {"model": llama_model, "input": "test"}):
            return {
                "type": "llamacpp",
                "embed_url": url,
                "model": llama_model,
                "env_name": f"自宅 (llama.cpp: {host})"
            }

    raise RuntimeError(
        "❌ 有効な Embedding バックエンドが見つかりません。\n"
        "   - Ollama が起動しているか確認してください。\n"
        "   - llama.cpp をお使いの場合は `--embedding` オプション付きで起動しているか確認してください。"
    )

def scan_target_files(root_dir="."):
    """リポジトリ内の .spec および ir/ 配下のファイルを収集（仮想環境等を除外）"""
    target_files = []
    for path in Path(root_dir).rglob("*"):
        # 除外ディレクトリに含まれているパスは無視
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue

        if path.is_file() and (path.suffix == ".spec" or "ir" in path.parts):
            if path.suffix == ".bak":
                continue
            target_files.append(str(path))
    return sorted(target_files)

def get_embedding(backend, text, filepath=""):
    """バックエンド仕様に合わせて Embedding ベクトルを取得"""
    # 512/8192 トークン制限を超えないよう、先頭 1500 文字（仕様書の要約・構造としては十分）に制限
    safe_text = text[:1500]

    if backend["type"] == "ollama":
        payload = {
            "model": backend["model"],
            "prompt": safe_text
        }
    else:  # llamacpp
        payload = {
            "model": backend["model"],
            "input": safe_text
        }

    req = urllib.request.Request(
        backend["embed_url"],
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode("utf-8"))

            if "embedding" in res:  # Ollama 形式
                return res["embedding"]
            elif "data" in res and len(res["data"]) > 0 and "embedding" in res["data"][0]:  # llama.cpp (OpenAI) 形式
                return res["data"][0]["embedding"]

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
            vec = get_embedding(backend, content)
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
                candidate_pairs.append({
                    "file_a": f1,
                    "file_b": f2,
                    "similarity": round(sim, 4)
                })

    candidate_pairs.sort(key=lambda x: x["similarity"], reverse=True)

    # 5. 結果の保存
    output_data = {
        "environment": backend["env_name"],
        "model_used": backend["model"],
        "total_files_scanned": len(files),
        "total_candidate_pairs": len(candidate_pairs),
        "threshold": SIMILARITY_THRESHOLD,
        "pairs": candidate_pairs
    }

    output_path = "spec_similarity_map.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完了: {len(candidate_pairs)} 組の重複・類似候補ペアを検出しました。")
    print(f"📄 結果ファイル: {output_path}")

if __name__ == "__main__":
    main()