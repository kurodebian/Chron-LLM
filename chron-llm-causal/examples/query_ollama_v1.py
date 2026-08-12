"""
examples/query_ollama.py
------------------------
WSL2 環境から Windows 上の Ollama API へ接続し、
Causal GraphRAG コンテキストを注入して因果補正付き回答を取得するスクリプト
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from causal_kernel.kernel.rag_interface import CausalRAGInterface

# 保持モデルからデフォルトを指定（環境変数 OLLAMA_MODEL で変更可能）
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:14b")


def resolve_ollama_base_url() -> str:
    """
    WSL2 から Windows 上の Ollama へアクセスするためのベース URL を決定する。
    1. 環境変数 OLLAMA_HOST が設定されていればそれを優先
    2. http://localhost:11434 を試行
    3. 失敗した場合、/etc/resolv.conf から Windows ホスト IP を取得して試行
    """
    env_host = os.environ.get("OLLAMA_HOST")
    if env_host:
        if not env_host.startswith("http"):
            env_host = f"http://{env_host}"
        return env_host.rstrip("/")

    # 1. localhost テスト
    localhost_url = "http://localhost:11434"
    try:
        req = urllib.request.Request(f"{localhost_url}/api/version", method="GET")
        with urllib.request.urlopen(req, timeout=1.5):
            return localhost_url
    except Exception:
        pass

    # 2. WSL2 の nameserver (Windows ホスト IP) 取得テスト
    resolv_path = Path("/etc/resolv.conf")
    if resolv_path.exists():
        with open(resolv_path, "r") as f:
            for line in f:
                if line.startswith("nameserver"):
                    win_ip = line.split()[1].strip()
                    win_url = f"http://{win_ip}:11434"
                    try:
                        req = urllib.request.Request(f"{win_url}/api/version", method="GET")
                        with urllib.request.urlopen(req, timeout=1.5):
                            return win_url
                    except Exception:
                        pass

    # デフォルトフォールバック
    return localhost_url


def query_ollama(prompt: str, system_prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Ollama API (/api/generate) を呼び出す"""
    base_url = resolve_ollama_base_url()
    endpoint = f"{base_url}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            return res_json.get("response", "")
    except urllib.error.URLError as e:
        print(f"\n[Error] Ollama API ({endpoint}) への接続に失敗しました: {e}")
        print("\n--- WSL2 ↔ Windows 接続ガイド ---")
        print("1. Windows 側で Ollama が起動しているか確認してください。")
        print("2. Windows の システム環境変数 に以下を設定して Ollama を再起動してください:")
        print("   OLLAMA_HOST = 0.0.0.0")
        print("   OLLAMA_ORIGINS = *")
        print(f"3. 指定モデル '{model}' が `ollama list` に存在するか確認してください。")
        sys.exit(1)


def main():
    json_path = Path("data/graphs/causal_master_graph_v2.json")
    if not json_path.exists():
        print(f"[Error] Graph JSON not found at: {json_path}")
        sys.exit(1)

    # 1. Causal GraphRAG インターフェースの初期化
    rag = CausalRAGInterface(json_path)

    # 2. 検索キーワードと質問の設定
    keyword = "Commit"
    user_query = "Commit 処理における不変条件 (INV) や依存関係、処理シーケンスについて因果グラフに基づいて分かりやすく解説してください。"

    print(f"=== 1. Causal Graph Context 抽出 (Keyword: '{keyword}') ===")
    causal_context = rag.generate_context_prompt(keyword)
    print(causal_context)

    # 3. プロンプト構築
    system_prompt = (
        "あなたはシステムアーキテクチャおよび因果関係の分析を行う専門家AIです。"
        "提供された【因果グラフコンテキスト】で示されている不変条件 (INV)、操作 (OP)、"
        "状態 (State)、および依存関係 (depends_on 等) の構造を厳格に尊重して質問に回答してください。"
        "グラフに存在しない要素や推測を含む場合は、グラフの記述と明確に区別して説明してください。"
    )

    full_prompt = (
        f"【因果グラフコンテキスト】\n{causal_context}\n\n"
        f"【質問】\n{user_query}"
    )

    base_url = resolve_ollama_base_url()
    print(f"\n=== 2. Ollama への問い合わせ送信 (Endpoint: {base_url}, Model: {DEFAULT_MODEL}) ===")
    print("応答を生成中...")

    # 4. API 呼び出し
    answer = query_ollama(prompt=full_prompt, system_prompt=system_prompt, model=DEFAULT_MODEL)

    print("\n=== 3. Ollama 応答 (因果補正済み) ===")
    print(answer)


if __name__ == "__main__":
    main()