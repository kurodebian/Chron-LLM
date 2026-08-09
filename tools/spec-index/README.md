# tools/spec-index (Phase 1: Physical Fact Indexer & Linter)

`tools/spec-index` は、Chron-LLM リポジトリ内の `.spec` ファイル群（ACTIVE 79件等）を
**意味的な判断（Canonical判定/廃止判定/改名判定等）を一切加えず**、
純粋な物理的・構造的ファクト（物理ファイル情報、SHA256、モジュール宣言、依存関係、ヘッダータグ等）として抽出・検証するための前処理基盤ツールキットです。

## 🔒 設計原則と安全性の保証

1. **FACT-ONLY 原則**: 意味的正規化・Canonical判定・改名提案は行いません（GPT-5.6裁定ステップ専用）。
2. **SHA256 物理完全性**: 物理ファイル単位で SHA-256 を記録し、内容変更時の `STALE_FACT_RECORD` 検出を保証します。
3. **0バイトファイル無欠落**: 0バイト仕様書も `"content_state": "EMPTY"` として完全記録します。

## 🚀 使い方

```bash
# 物理ファクトの抽出
python3 tools/spec-index/preprocess.py --root . --output-dir spec-index

# 構造的ファクトの検証
python3 tools/spec-index/lint.py --index spec-index/facts.jsonl