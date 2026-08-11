#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import time
import urllib.request
from urllib.error import HTTPError


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


def detect_backend(cli_model=None, cli_url=None):
    """起動中の Ollama サーバーおよび利用可能なモデルを自動検出する"""
    env_url = os.environ.get("LLM_API_URL")
    env_model = os.environ.get("LLM_MODEL_NAME")

    # 指定URLの決定
    target_url = cli_url or env_url

    win_ip = get_win_host_ip()
    hosts = ["http://localhost", "http://127.0.0.1"]
    if win_ip:
        hosts.append(f"http://{win_ip}")

    # Ollama (:11434) の自動検出
    for host in hosts:
        base_url = f"{host}:11434"
        try:
            req = urllib.request.Request(f"{base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=2.0) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode("utf-8"))
                    all_models = [
                        m.get("name") for m in data.get("models", []) if m.get("name")
                    ]

                    # embed 用モデルを除外した生成用モデルリスト
                    chat_models = [m for m in all_models if "embed" not in m.lower()]

                    # モデル決定優先順位: CLI引数 -> 環境変数 -> チャット用モデル先頭 -> 全モデル先頭 -> デフォルト
                    selected_model = (
                        cli_model
                        or env_model
                        or (
                            chat_models[0]
                            if chat_models
                            else (all_models[0] if all_models else "fusion711:27b")
                        )
                    )

                    final_url = target_url or f"{base_url}/v1/chat/completions"
                    return final_url, selected_model
        except Exception:
            pass

    # 検出失敗時のフォールバック
    default_host = f"http://{win_ip}:11434" if win_ip else "http://localhost:11434"
    return (
        target_url or f"{default_host}/v1/chat/completions",
        cli_model or env_model or "fusion711:27b",
    )


# LLM重複判定プロンプト（判定エンジン）
PAIR_ANALYSIS_SYSTEM_PROMPT = """あなたは Chron-LLM のアーキテクチャおよび仕様体系（PHASE A〜F、Delta3 Kernel）を熟知したエキスパートエンジニアです。

提示された2つの仕様ファイル（Doc A と Doc B）の内容を比較精査し、意味論的重複、構造的類似、親子関係、および統合の方向性を厳密に判定してください。

必ず以下の JSON フォーマットのみで返答してください（解説テキストやMarkdown装飾は含めないでください）：

{
  "pair_summary": "2つの文書の共通点と相違点の簡潔な要約",
  "relationship": "EXACT_DUPLICATE | PARTIAL_OVERLAP | PARENT_CHILD | SUPERSEDED | INDEPENDENT",
  "phase_alignment": {
    "doc_a_phase": "A | B | C | D | E | F | NONE",
    "doc_b_phase": "A | B | C | D | E | F | NONE",
    "is_same_phase": true
  },
  "recommended_action": "MERGE_B_INTO_A | MERGE_A_INTO_B | KEEP_BOTH | DEPRECATE_OBSOLETE | KEEP_A_DELETE_B",
  "integration_rationale": "推奨するアクションの技術的理由および Delta3 Kernel への統合方針"
}
"""


def read_file_content(filepath, max_chars=4000):
    """ファイルのテキストを読み込み、長大ファイルは前後を抽出"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if len(content) > max_chars * 2:
            return (
                content[:max_chars]
                + "\n\n... [TRUNCATED] ...\n\n"
                + content[-max_chars:]
            )
        return content
    except Exception as e:
        print(f"\n⚠️ ファイル読み込み失敗 [{filepath}]: {e}")
        return None


def clean_json_response(raw_text):
    """LLMレスポンスから純粋なJSON文字列を取り出す（Thinking出力やMarkdown対策）"""
    raw_text = raw_text.strip()

    # 1. <think>...</think> タグ（Reasoningモデルの思考過程）を除去
    raw_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()

    # 2. ```json ... ``` ブロックの抽出
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    if match:
        return match.group(1)

    # 3. ブロック記法がない場合は最初と最後の波括弧を探す
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start != -1 and end != -1 and start < end:
        return raw_text[start : end + 1]

    return raw_text


def analyze_pair_with_llm(
    file_a, file_b, similarity_score, api_url, model_name, max_retries=2
):
    """2つのファイルをLLMに食わせて重複度・統合関係を解析 (リトライ・エラーハンドリング強化)"""
    content_a = read_file_content(file_a)
    content_b = read_file_content(file_b)

    if not content_a or not content_b:
        return None

    user_prompt = f"""--- DOCUMENT A ---
File: {file_a}
Content:
{content_a}

--- DOCUMENT B ---
File: {file_b}
Content:
{content_b}

Vector Similarity Score: {similarity_score}
上記の Document A と Document B を比較分析し、指定の JSON 形式で判定を出力してください。"""

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": PAIR_ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},  # Ollama / OpenAI互換 JSON構造強制
    }

    req_data = json.dumps(payload).encode("utf-8")

    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(
                api_url,
                data=req_data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=600) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                raw_content = res_data["choices"][0]["message"]["content"]
                cleaned_json = clean_json_response(raw_content)

                result = json.loads(cleaned_json)
                result["file_a"] = file_a
                result["file_b"] = file_b
                result["similarity_score"] = similarity_score
                return result

        except HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            print(
                f"\n⚠️ HTTPエラー ({e.code}) [試行 {attempt}/{max_retries}]: {err_body}"
            )
        except json.JSONDecodeError as e:
            print(f"\n⚠️ JSONパース失敗 [試行 {attempt}/{max_retries}]: {e}")
        except Exception as e:
            print(f"\n⚠️ 通信/対話解析エラー [試行 {attempt}/{max_retries}]: {e}")

        if attempt < max_retries:
            time.sleep(2)  # 再試行前の待機

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Chron-LLM Spec Pair Comparison & Deduplication Engine"
    )
    parser.add_argument(
        "--map",
        default="spec_similarity_map.json",
        help="generate_similarity_map.py の出力JSON",
    )
    parser.add_argument(
        "--out",
        default="spec_deduplication_report.json",
        help="判定結果の出力JSON",
    )
    parser.add_argument(
        "--top", type=int, default=0, help="処理するペア数の上限 (0 = 全件)"
    )
    parser.add_argument(
        "--model",
        default=None,
        help="使用するLLMモデル名 (例: fusion711:27b)",
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Ollama チャット API エンドポイント URL",
    )
    args = parser.parse_args()

    # バックエンドおよびモデルの決定
    api_url, model_name = detect_backend(cli_model=args.model, cli_url=args.url)

    if not os.path.exists(args.map):
        print(
            f"❌ エラー: 類似度マップ '{args.map}' が見つかりません。"
            " 先に generate_similarity_map.py を実行してください。"
        )
        sys.exit(1)

    with open(args.map, "r", encoding="utf-8") as f:
        map_data = json.load(f)

    pairs = map_data.get("pairs", [])
    if args.top > 0:
        pairs = pairs[: args.top]

    print(f"🚀 重複判定パイプライン開始 (対象: {len(pairs)} ペア)")
    print(f"🤖 使用モデル: {model_name} @ {api_url}\n")

    report_results = []
    for i, pair in enumerate(pairs, 1):
        f1, f2 = pair["file_a"], pair["file_b"]
        sim = pair["similarity"]
        print(
            f"[{i}/{len(pairs)}] 比較中 ({sim:.2f}): {os.path.basename(f1)} ↔"
            f" {os.path.basename(f2)} ... ",
            end="",
            flush=True,
        )

        res = analyze_pair_with_llm(f1, f2, sim, api_url, model_name)
        if res:
            report_results.append(res)
            action = res.get("recommended_action", "N/A")
            rel = res.get("relationship", "N/A")
            print(f"✅ [{rel}] → 推奨: {action}")
        else:
            print("❌ スキップ")

        # 途中で中断・クラッシュしても結果が残るようループごとにファイル書き出し (チェックポイント)
        output_data = {
            "processed_pairs": len(report_results),
            "results": report_results,
        }
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 判定完了! 解析結果を '{args.out}' に保存しました。")


if __name__ == "__main__":
    main()
