# 実装ロードマップ — md_sheets 仕様書の因果を用いた分類・整理

STATUS: PROPOSED (plan draft; 採択・Freeze ではない)
ASOF: 2026-10-27 (Asia/Tokyo)
目的（最終目的と一致）: Chron-LLM 仕様書コーパス（md_sheets 127章）を、
因果（causal edges）とローカルLLM（Strata / qwen3.8-flash-next, 172.18.0.1:8080）を用いて
分類・整理し、章間の因果依存グラフと状態台帳を成果物として生成する。

## 0. 現状スナップショット（実測済み）

### ベースライン（このターンで緑を確認）
- chron-llm-causal: pytest 166 passed（マージ conflict 4箇所 + T8 contract 整合を修復済み）
- specification-organizer-experiment: pytest 259 passed
- 未解決だった test_delta1_delta2_traceability.py の収集不能は解消

### 実装検証済み資産（lineage）
| 資産 | 対応仕様ファミリ | 備考 |
|---|---|---|
| build_chapters_index.py + chapters_index.md | STEP-50 系（棚卸し）/ STEP-31 | md_sheets 127章の決定論的インデックス |
| DM-2 extraction pipeline (dm2_extraction.py, validate_dm2.py, grammars/dm2-3) | STEP-52 系（意味抽出） | corpus_manifest 49ファイル = spec_sheet 側のみ |
| A-1a segmentation (a1_segment.py, a1_boundary.gbnf) + audit.sh | STEP-51 系（分類前の単位画定） | 29 documents → semantic_units |
| chron-llm-causal Δ1/Δ2 + traceability + master graph | STEP-53 系（因果エッジ） | 対象コーパスは causal core spec 側 |
| jev_local.py | STEP-8 系（LLM ループ） | ~0.13s/ラベル |
| contracts/governance/step-192/validation | STEP-19/23 系（commit 原子性） | 契約レベル採択のみ、実装 NOT_VERIFIED |

### ギャップ（仕様のまま未実装）
- STEP-53 系の md_sheets コーパスへの適用 = DM-3（causal extraction）: DM-2 契約が
  「downstream: DM-3」とのみ参照、実装なし ← 最上流の欠落
- STEP-54 系（セマンティックグラフ検証・矛盾/閉包監査）: master graph 統合は部分実装
- md_sheets 127章の章レベル意味抽出・因果グラフは 0 件（ID→コード参照スキャン 0 hits）

## 1. 順序だてた実装手順（巨大ファイル対策込み）

前提規律: 各 Phase は evidence を残す。ARTIFACT_EXISTENCE != NORMATIVE_ADOPTION /
MISSING_EVIDENCE != PASS / VERIFICATION_IS_NOT_AUTHORIZATION。

### P0 — md_sheets コーパス Freeze（A-0d 相当）[1 step]
- 3ファイル（1-74.md, 75-99.md, 100-124.md）+ chapters_index.md + 台帳 JSON の
  SHA-256 digest manifest を ledger/ に生成（corpus_manifest 方式流用）
- 検証: 再ハッシュ一致。Freeze は記録であり承認ではない。

### P1 — 章レベル単位画定（決定論的。LLM 不要）[1 step]
- chapters_index.md の H1 境界で 127 単位へ deterministic slice（既に ledger に line_start/end 済）
- 境界検証: 章間が原ファイルの欠損なし重複なし再構成になること（byte-exact concatenation テスト）
- A-1a の LLM 境界判定は使わない: md_sheets は規範的 H1 構造を持つため境界は规范由来。
  裁定不能ヘッダ（範囲見出し「STEP-31–96」等）は UNRESOLVED として保全（推測しない）

### P2 — 章レベル意味抽出（DM-2 系譜の md_sheets 適用）[127章×チャンク逐次]
- 単位=章（最大 42KB ≪ n_ctx 65536）。1 次関数で章→semantic claims 抽出、GBNF 拘束、
  validate_dm2 同等の決定論的検証 + evidence provenance + unknown-preserving
- 巨大ファイルは read しない: ledger の line range で章のみ読む（順序だてた読み込みの担保）
- 成果物: ledger/units/<STEP>.units.json + extraction report。章ごとに append、
  テストはサニティ章（小: STEP-1a, 大: STEP-120）で回帰固定
- ゲート: 抽出スキーマ検証 100%、unresolved は list 保全、LLM 出力は raw evidence 付き

### P3 — 因果エッジ抽出 DM-3（新規契約ドラフト + 実装）[本命ギャップ]
- STEP-53（Claim Relationship / Dependency / Causal Edge Proposal）契約を md_sheets 向けに
  プロファイル化: edge 型は depends-on / precedes / refines / contradicts / validates-of
- 実装は chron-llm-causal Δ1 の方法論再利用（抽出→正規化→検証→台帳）、TDD で先にテスト
- 検証: Δ0 相当の不変条件（エッジ両端が frozen unit に存在、重複禁止、
  source evidence 必須、UNRESOLVED 保全）
- ゲート: negative tests（dangling edge, duplicate, evidence-less が reject されること）

### P4 — セマンティックグラフ検証（STEP-54 系譜）
- 非巡回確認・強連結成分・矛盾ペア検出・閉包監査（欠損エッジ候補の UNRESOLVED 列挙）
- master graph 統合（causal_master_graph.json と同一の台帳形）
- 章間クラスタ（ledger の 16 cluster）と因果グラフの相互検証: クラスタ横断エッジの密度を
  「分類の妥当性」の決定論的証拠にする

### P5 — 分類・整理マップ生成（最終成果物）
- 整理物: (a) 章因果グラフ JSON + 可視化 (b) クラスタ×実装状態マトリクス（ledger 拡張）
  (c) 依存順トポロジカルソート = 「未実装仕様の最適実装順序」候補リスト
- LLM は分類語彙の提案・章要約にのみ使用し、グラフ構造は決定論的検証済みのものだけ採用
- 全成果物に provenance（unit id, evidence ref, validator version, digest）

## 2. リスクと決定が要る点
- 検出済（2026-10-27 実測）: chron-llm-causal のテスト実行が data/audit/phase6/7 成果物を
  書き戻す副作用あり（test_phase6/7 → kernel 経由）。再生成結果自体は PYTHONHASHSEED 非依存で
  安定だが、frozen コミット済み成果物と edge type 2件（refines↔depends_on）が差分する
  = 現ツリーのコードから凍結成果物が再現不能（artifact-vs-code drift）。
  裁定 Needed: (a) 再生成+再フリーズ (b) 生成版の特定 (c) 凍結維持+既知乖離の記録。
  いずれも tests からの data/audit 書き込みは read-only 化が必須（P0 ハーディング）。
- LLM 抽出の品質: Strata モデルの GBNF 追従は spec_sheet 側で実証済みだが、
  md_sheets の日本語散文混在章（STEP-1a〜19 系）は未試走 → P2 で小規模試走ゲートを置く
- STEP-40（Event Ordering / Causality / Deterministic Replay）はこのコーパス内の
  「因果契約」そのもの: 分類結果の参照実装として P3/P4 で特別扱い推奨
- 成果物の置き場: 本 roadmap・ledger は specification-organizer-experiment/ 内（実験系譜に一致）。
  監査系成果物は従来どおり repo 外（~/audit-*）との線引きを維持
- contracts/governance の STEP-187..218 は本コーパス（1..124）と別系列。統合分類は
  後続決定（別ドメインとして namespace 分離する案が D-CCX-01 前例と整合）
