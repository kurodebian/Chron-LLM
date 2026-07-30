#!/usr/bin/env bash
set -e

MAP_FILE="spec_similarity_map.json"
MODEL="fusion711:27b"
OUT_DIR="pair_results"

# Windows ホストの IP を取得（WSL2 → Windows）
WIN_IP=$(ip route show default | awk '{print $3}')
OLLAMA_URL="http://${WIN_IP}:11434/v1/chat/completions"

echo "🚀 Starting pair-by-pair processing (WSL2)"
echo "🤖 Model: $MODEL"
echo "🌐 Ollama URL: $OLLAMA_URL"
echo ""

# 出力ディレクトリ作成
mkdir -p "$OUT_DIR"

# 類似度マップ読み込み
TOTAL=$(jq '.pairs | length' "$MAP_FILE")
echo "📄 Total pairs: $TOTAL"
echo ""

TMP_MAP="tmp_pair.json"
# 終了時に一時ファイルを自動削除
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

    echo "[$((i+1))/$TOTAL] Processing ($SIM): $FILE_A ↔ $FILE_B ..."

    # 一時マップを作成（1ペアだけ）
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
