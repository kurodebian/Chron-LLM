import os
import sys
import json
import re
import argparse
from pathlib import Path
import urllib.request

# ローカルLLM API設定
API_URL = os.environ.get("LLM_API_URL", "http://localhost:11434/v1/chat/completions")
MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "qwen2.5-coder:32b")

SYSTEM_PROMPT = """あなたは Chron-LLM の仕様体系（PHASE A〜F）とモジュール体系を完全に理解したシステムアーキテクトです。

与えられた .spec / .md の内容を読み取り、以下の観点で分類・重複検出を行ってください。

必ず以下の JSON のみを返してください（余計な解説テキストやMarkdownの囲みは一切不要です）：

{
  "target_file": "...",
  "module": "graph-runtime | runtime | world | memory | registry | observability | llama-agent | tests | docs | unknown",
  "phase": "A | B | C | D | E | F | none",
  "version": "R1 | R2.0 | R2.1 | R2.2 | R2.3 | Delta3 | unknown",
  "core_concepts": ["..."],
  "summary": "...",
  "redundancy_level": "HIGH | MEDIUM | LOW",
  "relationship": "duplicate | partial-duplicate | parent | child | independent",
  "suggested_action": "KEEP | MERGE | DEPRECATE | SPLIT"
}
"""


def scan_target_files(target_dir=".", extensions=(".spec", ".md")):
    """指定ディレクトリ配下の解析対象ファイルを収集"""
    target_path = Path(target_dir)
    files = []

    if target_path.is_file():
        return [str(target_path)]

    for path in target_path.rglob("*"):
        if path.is_file() and path.suffix in extensions:
            # バックアップや一時ファイルを除外
            path_str = str(path)
            if (
                "local-backup" in path_str
                or path.suffix == ".bak"
                or path.name.startswith(".")
            ):
                continue
            files.append(path_str)

    return sorted(files)


def clean_json_response(raw_text):
    """LLMがMarkdownコードブロック等を含めた場合にJSON部分のみを抽出"""
    raw_text = raw_text.strip()
    # ```json ... ``` の囲みを除去
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    if match:
        return match.group(1)

    # 直接 JSON オブジェクトを探す
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start != -1 and end != -1:
        return raw_text[start : end + 1]

    return raw_text


def analyze_file(filepath):
    """ファイル単体をローカルLLMに投げて結果を取得"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 読み込み失敗: {filepath} ({e})")
        return None

    # コンテキスト節約のため長大ファイルは先頭・末尾をサンプリング
    if len(content) > 8000:
        content = content[:4000] + "\n\n... [TRUNCATED] ...\n\n" + content[-4000:]

    user_prompt = f"ファイルパス: {filepath}\n\n--- 仕様内容 ---\n{content}"

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            raw_content = res_data["choices"][0]["message"]["content"]
            cleaned_json = clean_json_response(raw_content)

            result = json.loads(cleaned_json)
            result["target_file"] = filepath  # パスを正規化
            return result
    except Exception as e:
        print(f"⚠️ 解析エラー [{filepath}]: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Chron-LLM Spec Classifier & Deduplicator"
    )
    parser.add_argument(
        "--dir", default="docs/ir", help="解析対象ディレクトリ (デフォルト: docs/ir)"
    )
    parser.add_argument(
        "--out", default="spec_analysis_report.json", help="出力JSONファイル名"
    )
    args = parser.parse_args()

    files = scan_target_files(args.dir)
    print(f"🚀 スキャン開始: {args.dir} (対象: {len(files)} ファイル)")
    print(f"🤖 使用モデル: {MODEL_NAME} @ {API_URL}\n")

    results = []
    for i, filepath in enumerate(files, 1):
        print(f"[{i}/{len(files)}] 解析中: {filepath} ... ", end="", flush=True)
        res = analyze_file(filepath)
        if res:
            results.append(res)
            print(
                f"✅ [{res.get('module', 'N/A')}] Phase {res.get('phase', 'N/A')} - Action: {res.get('suggested_action', 'N/A')}"
            )
        else:
            print("❌ スキップ")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 完了! 解析結果を {args.out} に保存しました。")


if __name__ == "__main__":
    main()
