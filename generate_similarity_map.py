import os
import json
import math
from pathlib import Path
import urllib.request

# --- 修正箇所 ---
# 環境変数 OLLAMA_HOST からベースURLを取得（末尾のスラッシュを除去）
OLLAMA_BASE = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
EMBED_API_URL = f"{OLLAMA_BASE}/api/embeddings"
EMBED_MODEL = "nomic-embed-text"

SIMILARITY_THRESHOLD = 0.75  # LLM精査に回す類似度閾値

def scan_target_files(root_dir="."):
    """リポジトリ内の .spec および ir/ 配下のファイルを収集"""
    target_files = []
    for path in Path(root_dir).rglob("*"):
        if path.is_file() and (path.suffix == ".spec" or "ir" in path.parts):
            # バックアップや除外対象
            if "local-backup" in str(path) or path.suffix == ".bak":
                continue
            target_files.append(str(path))
    return sorted(target_files)

def get_embedding(text):
    """ローカルAPIからEmbeddingベクトルを取得"""
    payload = {
        "model": EMBED_MODEL,
        "prompt": text[:4000]  # 長大テキストは前半部をサンプリング
    }
    req = urllib.request.Request(
        EMBED_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode("utf-8"))
            return res.get("embedding")
    except Exception as e:
        print(f"Embedding error: {e}")
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
    files = scan_target_files()
    print(f"📁 スキャン対象: {len(files)} ファイル")

    # 1. ベクトルデータの生成
    embeddings = {}
    for i, filepath in enumerate(files, 1):
        print(f"[{i}/{len(files)}] ベクトル化中: {filepath}")
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            vec = get_embedding(content)
            if vec:
                embeddings[filepath] = vec
        except Exception as e:
            print(f"Skip {filepath}: {e}")

    # 2. 類似度ペアの抽出
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

    # 類似度の高い順にソート
    candidate_pairs.sort(key=lambda x: x["similarity"], reverse=True)

    # 3. 結果の保存
    output_data = {
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
