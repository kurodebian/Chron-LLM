#!/usr/bin/env bash
set -e

MAP_FILE="spec_similarity_map.json"
OUT_DIR="pair_results"

# Windows ホストの IP を取得（WSL2 → Windows）
WIN_IP=$(ip route show default | awk '{print $3}')

# HTTPレスポンスコードを取得する軽量なヘルパー関数
check_http() {
    curl -s -o /dev/null -w "%{http_code}" --max-time 1 "$1" 2>/dev/null || echo "000"
}

echo "🔍 Detecting active LLM backend..."

# 1. llama-server (8080) のチェック
if [ "$(check_http "http://localhost:8080/v1/models")" -eq 200 ] || [ "$(check_http "http://localhost:8080/")" -eq 200 ]; then
    echo "✅ Detected: llama.cpp (llama-server) on localhost:8080"
    OLLAMA_URL="http://localhost:8080/v1/chat/completions"
    MODEL="fusion711:27b"

# 2. Ollama (WSL2 ローカル: 11434) のチェック
elif [ "$(check_http "http://localhost:11434/api/tags")" -eq 200 ]; then
    echo "✅ Detected: Ollama on localhost:11434"
    OLLAMA_URL="http://localhost:11434/v1/chat/completions"
    MODEL="fusion711:27b"

# 3. Ollama (Windows ホスト: 11434) のチェック
elif [ -n "$WIN_IP" ] && [ "$(check_http "http://${WIN_IP}:11434/api/tags")" -eq 200 ]; then
    echo "✅ Detected: Ollama on Windows host (${WIN_IP}:11434)"
    OLLAMA_URL="http://${WIN_IP}:11434/v1/chat/completions"
    MODEL="fusion711:27b"

# 4. どちらも検出できなかった場合のフォールバック
else
    echo "⚠️ Warning: No active backend detected. Defaulting to Windows Ollama."
    OLLAMA_URL="http://${WIN_IP:-localhost}:11434/v1/chat/completions"
    MODEL="fusion711:27b"
fi

echo ""
echo "🚀 Starting pair-by-pair processing"
echo "🤖 Model: $MODEL"
echo "🌐 LLM URL: $OLLAMA_URL"
echo ""

# 出力ディレクトリ作成
mkdir -p "$OUT_DIR"

# 類似度マップ読み込み
TOTAL=$(jq '.pairs | length' "$MAP_FILE")
echo "📄 Total pairs: $TOTAL"
echo ""

TMP_MAP="tmp_pair.json"
trap 'rm -f "$TMP_MAP"' EXIT

# 1ペアずつ処理
for ((i=0; i<TOTAL; i++)); do
    OUT_FILE="${OUT_DIR}/pair_$((i+1)).json"

    # 既に結果ファイルが存在する場合はスキップ（レジューム機能）
    if [ -s "$OUT_FILE" ]; then
        echo "[$((i+1))/$TOTAL] ⏩ Skip (Already exists): $OUT_FILE"
        continue
    fi

    # jq でペアを抽出
    FILE_A=$(jq -r ".pairs[$i].file_a" "$MAP_FILE")
    FILE_B=$(jq -r ".pairs[$i].file_b" "$MAP_FILE")
    SIM=$(jq -r ".pairs[$i].similarity" "$MAP_FILE")

    # ファイルが削除済みの場合はスキップ
    if [ ! -f "$FILE_A" ] || [ ! -f "$FILE_B" ]; then
        echo "[$((i+1))/$TOTAL] ⚠️ Skip (File missing/deleted): $FILE_A or $FILE_B"
        continue
    fi

    echo "[$((i+1))/$TOTAL] Processing ($SIM): $FILE_A ↔ $FILE_B ..."

    # 一時マップを作成
    jq -n \
      --arg fa "$FILE_A" \
      --arg fb "$FILE_B" \
      --arg sim "$SIM" \
      '{pairs: [{file_a: $fa, file_b: $fb, similarity: ($sim|tonumber)}]}' \
      > "$TMP_MAP"

    # compare を実行
    python3 compare_similarity_pairs.py \
        --map "$TMP_MAP" \
        --out "$OUT_FILE" \
        --model "$MODEL" \
        --url "$OLLAMA_URL" \
        --top 1

    echo "   → Saved: $OUT_FILE"
    echo ""
done

echo "🎉 All pairs processed!"
echo "📁 Results stored in: $OUT_DIR"