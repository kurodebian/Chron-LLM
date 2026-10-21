# Governance Ledger — contracts/governance/

Purpose: STEP 系列ガバナンス契約ドラフト（会話ドラフト）を、未採択のまま追跡可能な
リポジトリ内アーティファクトとして記録する台帳。Filing は記録行為であり、
採択・実装・受理・Freeze ではない。

STATUS: LEDGER_ACTIVE / ALL_FILED_ITEMS_NOT_ADOPTED
ASOF: 2026-10-21 (Asia/Tokyo)
REPO_BASELINE_AT_FILING: b231635452dd6ccd75f9f4ec9fbb40c5de510afa (backup/home-2026-08-12-0219)

## 状態語彙（すべての filing に適用）

- NORMATIVE_STATUS: PROPOSED — 規範語（MUST 等）は正式採択まで拘束力を持たない。
- ADOPTION_STATUS: NOT_ADOPTED
- IMPLEMENTATION_STATUS: NOT_VERIFIED / TEST_STATUS: NOT_EXECUTED
- FREEZE_STATUS: NOT_AUTHORIZED / GLOBAL_ACCEPTANCE: NOT_ASSESSED
- 公理: ARTIFACT_EXISTENCE != NORMATIVE_ADOPTION / CLOSURE_REPORT != CLOSURE_PROOF

## Filing 規約

各 filing ファイルは先頭に `# Filing Record` メタデータブロックを持ち、
`<<<FILING-END>>>` の後に対象ドラフト全文が逐語（verbatim）で続く。
本文は SOURCE の SHA-256 とバイト一致で検証済み（BODY_SHA256 として記録）。
本文は変更しない。変更が必要な場合は新バージョンドラフトとして別途 filing する。

## 目録（digest manifest）

| path | source | body sha256 |
|---|---|---|
| step-190/STEP190_CANONICAL_HISTORY_PROOF_PROTOCOL_v0.1.0-draft.md | paste_2_134928.txt L1-1043 (sha dbd87460…) | dbd8746028c9cf448eb9782ac83a65746a50abc26a0778fbda4b4a46dbe9ff54 |
| step-191/STEP191_DECISION_ENFORCEMENT_v0.1.0-draft.md | paste_4_142951.txt L1-682 (正本) | 0f8e41e81b31fc7c3bd7426cf00c7a8a9e35211ef47e7f88a20af8f40fd483c9 |
| step-218/NCCI-218_CANONICAL_GOVERNANCE_CLOSURE_v0.1.0-draft.md | paste_2_152201.txt L1-603 | 2ec5dee77ef4386bb620d6ab8464d3bd52d92e767a7ceb08b4b899b8b8e7a475 |

注: STEP-191 について paste_2_134928.txt L1022-1043 は英語プレビュー（22行）のみ。
正本は paste_4_142951.txt（682行、§21 に STEP-192 予定範囲のプレビューを含む）。

## 監査証跡（リポジトリ外、read-only audit の生証拠）

- STEP-190: ~/audit-190/ (A190-E-REAL, E-190-001..010) + ~/design-step190/
- STEP-191: ~/audit-191/ (A191-E-REAL, E-191-001..010) + ~/design-step191/
- STEP-218: ~/audit-218/ (A218-E-REAL, E-218-001..010) + ~/design-step218/

## 未 filing の系列（2026-10-21 時点）

- STEP-187/188/189: 全文は ~/.hermes/state.db（セッション）にのみ存在。リポジトリ・paste に全文なし。Filing には全文の確定が前提条件。
- STEP-192: ドラフト本体なし（STEP-191 §21 の予定範囲プレビューのみ）。D4 裁定により HOLD。
