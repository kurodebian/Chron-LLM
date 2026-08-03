#!/usr/bin/env python3
import os
import glob
import argparse
import subprocess
import json
import urllib.request
import urllib.error

# --- 環境設定 ---
CTX_DIR = "component_contexts"
OUT_DIR = "results"

# 自宅環境用 (WSL2上のllama.cpp)
LLAMA_BIN = "../llama.cpp/build/bin/llama-cli"
LLAMA_MODEL = "../models/Qwen3.6-35B-A3B-MTP/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"

# 職場環境用 (Windows側のOllama API)
OLLAMA_URL = "http://172.18.0.1:11434/api/generate"
OLLAMA_MODEL = "hf.co/unsloth/Qwen3.6-35B-A3B-MTP-GGUF:UD-Q4_K_M"
# --------------

def run_llama_cpp(prompt_text):
    cmd = [
        LLAMA_BIN,
        "-m", LLAMA_MODEL,
        "-c", "32768",
        "--temp", "0.1",
        "--seed", "42",
        "-p", prompt_text
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def run_ollama(prompt_text):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt_text,
        "stream": False,
        "system": "",  # Ollama独自のシステムプロンプトを無効化
        "options": {
            "temperature": 0.1,
            "seed": 42,
            "num_ctx": 32768,
            "num_predict": 4096  # 途中で途切れないよう最大出力トークン数を確保
        }
    }
    req = urllib.request.Request(
        OLLAMA_URL, 
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("response", "")
    except urllib.error.URLError as e:
        return f"[Error] Ollama接続エラー: {e}"

def parse_thinking_and_result(output_text):
    """思考プロセスと結果を分離するパーサー（拡張版）"""
    thinking = ""
    result = output_text

    # パターン1: <think> ... </think> タグがある場合
    if "<think>" in output_text and "</think>" in output_text:
        parts = output_text.split("</think>", 1)
        thinking = parts[0].replace("<think>", "").strip()
        result = parts[1].strip()
    
    # パターン2: "Thinking Process:" または "Here's a thinking process:" から始まる場合
    elif output_text.strip().startswith("Thinking Process:") or output_text.strip().startswith("Here's a thinking process:"):
        lines = output_text.splitlines()
        thinking_lines = []
        result_lines = []
        is_thinking = True
        
        for line in lines:
            if is_thinking:
                thinking_lines.append(line)
                # 思考プロセスの箇条書きが終わり、実際の分析やセクションに移る目印
                if "Optimal" in line or "Architectur" in line or "###" in line or "---" in line or "1. Execute" in line:
                    is_thinking = False
                    result_lines.append(line)
            else:
                result_lines.append(line)
        
        if not is_thinking:
            thinking = "\n".join(thinking_lines).replace("Here's a thinking process:", "").replace("Thinking Process:", "").strip()
            result = "\n".join(result_lines).strip()

    return thinking, result

def main():
    parser = argparse.ArgumentParser(description="LLM Batch/Targeted Processor")
    parser.add_argument("--mode", choices=["llama", "ollama"], default="ollama", 
                        help="実行環境の選択 (default: ollama)")
    parser.add_argument("-t", "--target", type=int, nargs="+",
                        help="実行するファイルの番号を指定 (例: -t 9)")
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    
    files_to_run = []
    if args.target:
        for num in args.target:
            filename = f"component-{num:03d}.json"
            filepath = os.path.join(CTX_DIR, filename)
            if os.path.exists(filepath):
                files_to_run.append(filepath)
            else:
                print(f"[Warning] ファイルが見つかりません: {filepath}")
    else:
        files_to_run = sorted(glob.glob(os.path.join(CTX_DIR, "component-*.json")))
    
    if not files_to_run:
        print("実行対象のファイルがありません。処理を終了します。")
        return

    active_model = LLAMA_MODEL if args.mode == "llama" else OLLAMA_MODEL

    print(f"環境: {args.mode.upper()}")
    print(f"モデル: {active_model}")
    print(f"対象: {len(files_to_run)} 件のファイルを処理します...\n")

    for filepath in files_to_run:
        filename = os.path.basename(filepath)
        print(f"=======================================")
        print(f"🚀 Running: {filename}")
        print(f"=======================================")

        with open(filepath, 'r', encoding='utf-8') as f:
            json_content = f.read()

        prompt_text = f"""以下の仕様書コンポーネントデータを分析し、各アーティファクトの関係性（MERGEやKEEP_BOTHなど）に基づいた最適なマージ計画、アーキテクチャ上の整合性、および具体的な改善提案を構造化して出力してください。

### 入力データ:
{json_content}
"""

        if args.mode == "llama":
            output = run_llama_cpp(prompt_text)
        else:
            output = run_ollama(prompt_text)

        thinking, result = parse_thinking_and_result(output)

        if thinking:
            print("--- 🧠 思考プロセス (抜粋) ---")
            print(thinking[:150] + ("...\n" if len(thinking) > 150 else "\n"))
        
        print("--- ✨ 最終結果 (プレビュー) ---")
        print(result[:300] + ("...\n" if len(result) > 300 else "\n"))

        out_filename = f"out_{filename.replace('.json', '.txt')}"
        out_filepath = os.path.join(OUT_DIR, out_filename)
        with open(out_filepath, 'w', encoding='utf-8') as f:
            f.write(result)
            
        print(f"💾 Saved to: {out_filepath}\n")

if __name__ == "__main__":
    main()