# Filing Record（ファイリングメタデータ — ドラフト本文の一部ではない）

FILED: 2026-10-21 (Asia/Tokyo)
FILING: D4 HOLD 解除（同日）に基づく STEP-192 ドラフト着手（../ADJUDICATIONS.md 参照）
FILING_STATUS: FILED_AS_DRAFT_ARTIFACT
SOURCE_PROVENANCE: 本セッションで新規作成。予定範囲の正本は step-191 filing §21
  （paste_4_142951.txt L668-682、sha 0f8e41e8… の一部）。裁定 D2/D3/D5/D6 を適用。
ORIGIN: Hermes agent draft (user-directed kickoff, 2026-10-21)
CANONICAL_MUTATION: NONE（ドラフトの記録であり、採択・実装・Freeze ではない）
<<<FILING-END>>>

# STEP-192 — Commit Admission Atomicity / Transaction Binding / Durable Commit Receipt / Recovery Reconciliation Contract

STEP_ID: 192
VERSION: 0.1.0-draft
STATUS: DRAFT_COMPLETE
NORMATIVE_STATUS: PROPOSED
ADOPTION_STATUS: NOT_ADOPTED
IMPLEMENTATION_STATUS: NOT_VERIFIED
TEST_STATUS: NOT_EXECUTED
REPOSITORY_INSPECTION: NOT_PERFORMED
COMMIT_ATOMICITY_VALIDATION: NOT_EXECUTED
COMMIT_RECEIPT_VALIDATION: NOT_EXECUTED
CRASH_RECOVERY_VALIDATION: NOT_EXECUTED
IDEMPOTENCY_RECONCILIATION_VALIDATION: NOT_EXECUTED
LINEARIZATION_VALIDATION: NOT_EXECUTED
DEPENDS_ON: STEP-190 / STEP-191（ドラフト・NOT_ADOPTED）, 凍結層 v2.8.0-C（read-only 前提）
ADJUDICATIONS_APPLIED: D2（契約レベルスキーマのみ。凍結層不変更）, D3（half-open [a,b)・gapless 連結）,
  D5（認可済み governance event は正準チェーン）, D6（拒否・監査記録は Canonical History 外）
TIMEZONE: Asia/Tokyo

本書は分析・設計ドラフトであり、採択・実装・受理の証明ではない。
すべての MUST は正式採択まで拘束力を持たない。

## 1. 目的

STEP-191 は監査決定（Audit Decision）と Commit Admission の境界を定義した。
STEP-192 は、Admission が認可された操作が Canonical History に commit される
トランザクション境界そのものを契約化する: 意図の固定、書込み順序、
永続化証明（Commit Receipt）、クラッシュからの復旧照合、線形化点。

## 2. 核心の区別（本契約の公理）

COMMIT_ADMISSION != COMMIT_FINALITY
COMMIT_INTENT != COMMIT_RESULT
RECEIPT_ISSUED != HISTORY_COMMITTED
NO_RECEIPT != NOT_COMMITTED
INDETERMINATE != FAILED
REJECTION => NO_CANONICAL_MUTATION（STEP-191 より継承）
STALE_DECISION != CURRENT_PERMISSION（STEP-191 より継承）

## 3. トランザクション境界

Commit トランザクションは次の順序を持つ:
  Admission Decision → Commit Intent 固定 → 正準書込み → 永続化確認 →
  Commit Receipt 発行 → Finality 宣言
境界は half-open 区間で建模する（D3 採用）:
  [admission, commit_point) 区間では操作は正準履歴の一部ではない。
  commit_point 以降、操作は gapless sequence の要素として確定済みである。
Admission 失効（期限・revocation）は [admission, commit_point) 内で発生しうる:
  commit_point 到達前に authority が失効した場合、commit してはならない
  （STALE_DECISION != CURRENT_PERMISSION の実行時版）。

## 4. Commit Intent と操作識別子の固定

- 各 commit 操作 MUST は一意な OperationID を持つ。OperationID は Commit Intent
  固定時点で決定論的に固定され、以後変更されない。
- Commit Intent MUST は次を含む: OperationID、対象操作の正準表現（ハッシュ）、
  適用された Admission Decision / Authorization の参照（STEP-191 の
  AuthorityRef・CausalID と対応）、意図の時刻境界 [intent_begin, intent_expiry)。
- 同一 OperationID の Intent が 2 つ存在してはならない（一意性）。
- Intent 固定は正準書込みより前に完了していなければならない。

## 5. WAL への記録順序と永続化保証

- 正準書込み MUST は Write-Ahead の順序を守る: Intent レコードが正準イベント
  レコードより先に永続化されなければならない。
- 永続化順序は gapless な整数列 [n, n+1) で表される（D3）。列に隙間がある場合、
  履歴 MUST は RECONCILIATION_REQUIRED 状態となり、次の commit を受け付けない。
- 永続化確認（fsync 相当）が完了するまで Finality を宣言してはならない。
- 凍結層が単一の正準追記経路を持つ事実（T-191-D）を前提とし、本契約は
  追記経路を増やさない。

## 6. Commit Receipt

- 永続化確認の完了ごとに Commit Receipt MUST が生成される。
- Receipt MUST は次をバインドする: OperationID、正準イベントの識別子と位置 n、
  永続化確認の証明、発行時刻。
- Receipt の一意性: 同一 OperationID に対して有効な Receipt は高々 1 つ。
  同一 OperationID の異なる Receipt が 2 つ観測された場合、それは障害であり、
  照合（§9）なしにどちらかを選んでってはならない。
- Receipt 検証 MUST は決定論的であること（同一入力 → 同一判定）。
- RECEIPT_ISSUED != HISTORY_COMMITTED: Receipt は検証を経て Finality に接続される。

## 7. Crash Point ごとの復旧規則

クラッシュポイントを順序上の位置で分類する:
  CP1: Intent 固定前 → 操作は NOT_COMMITTED。副作用なし。再試行は新 Intent。
  CP2: Intent 永続化後・正準書込み前 → NOT_COMMITTED（Intent は孤児）。
       孤児 Intent MUST は RECONCILIATION で処理され、正準履歴に現れない。
  CP3: 正準書込み途中 → 部分書込み。§9 の照合規則に従う。履歴は
       RECONCILIATION_REQUIRED となるまで commit を受け付けない。
  CP4: 正準書込み後・永続化確認前 → 判定不能（INDETERMINATE）。§8。
  CP5: 永続化確認後・Receipt 発行前 → 履歴は commit 済み。Receipt を
       再生成可能でなければならない（決定論的再生成）。
  CP6: Receipt 発行後・Finality 宣言前 → commit 済み・Receipt 有効。
       Finality 宣言を再開時に行える。

## 8. Commit 済み・未 Commit・判定不能の識別

復旧後の判定は 3 値とする:
  COMMITTED: 正準列の gapless 範囲 [0, n) に完全に含まれ、永続化確認済み。
  NOT_COMMITTED: 正準列に現れず、孤児 Intent のみ（CP1/CP2）。
  INDETERMINATE: 正準列の末尾範囲 [m, N) が部分書込み・応答喪失により
       完了か不完全か永続化証拠だけでは決定できない。
INDETERMINATE に対する規則:
  - INDETERMINATE を FAILED でも COMMITTED でもないものとして扱う（§2 公理）。
  - INDETERMINATE 区間が解決されるまで、同じ OperationID の再試行 MUST は
    拒否される（重複 commit 防止）。
  - 解決は §9 の照合によってのみ行われる。

## 9. Idempotency Record と Canonical History の整合、部分書込み・応答喪失・再起動後の照合

- 各 commit 試行 MUST は Idempotency Record（OperationID → 試行状態）を持つ。
  再起動後、Idempotency Record と正準列の突合 MUST が決定論的に実行される:
  - OperationID が正準列に完全存在 → COMMITTED。Receipt 再生成・再発行禁止。
  - OperationID が正準列に皆無 → NOT_COMMITTED。再試行可（同一 OperationID 可）。
  - OperationID が部分的に現れる → INDETERMINATE。照合規則: 正準列の末尾から
    gapless 連結を検証し、連結が途切れる位置 k 以降を RECONCILIATION 対象とする。
    途切れた区間 [k, N) の扱い（切り戻し / 修復）は採択時に別途裁定する
    （OI-192-03）。
- 応答喪失（client 応答なし）は commit の成否を変えない: 履歴の状態のみが
  成否を定義する（NO_RECEIPT != NOT_COMMITTED）。

## 10. Commit の線形化点と確定性

- 各 commit 済み操作の線形化点は永続化確認点である。
- 正準列の順序は線形化順序と一致しなければならない（gapless 連結 = 全順序）。
- 決定論保証: 同一の正準列と同一の照合規則から、再起動回数・時刻に依存しない
  同一の復旧状態が導かれなければならない。
- 並行 commit 試行がある場合、線形化点は直列化可能でなければならない
  （直列化可能性の検証は STEP-192 の採択済み検証項目 OI-192-05）。

## 11. 監査証跡と Canonical History の整合（D5/D6 適用）

- 拒否された Admission 試行・権限外試行の記録 MUST は Canonical History 外に
  保存される（D6）。正準列は拒否を含まない。
- 認可済み governance event（失効・revocation・例外認可 — D5 候補A）は
  正準 Commit Authority を経て正準列に commit される。これらは拒否記録ではない。
- 整合規則: 監査ログの Admission 決定と正準列の commit には対応関係が
  存在しなければならない。正準列に commit された操作で、監査ログに対応する
  認可決定がないものは INVALID_COMMIT として照合対象とする。
  監査ログ側の欠落は正準列の妥当性を無効化しない（履歴の純度維持）が、
  監査完全性の欠陥として記録される。

## 12. 凍結層との関係

- 本契約は凍結層 v2.8.0-C への変更を要求しない（D2: DEFERRED_TO_CONTRACT_LEVEL）。
  OperationID / Intent / Receipt / Idempotency Record は契約レベルのスキーマ定義である。
- 凍結層に時刻・期限・失効の足場が存在しない（T-191-B）ため、
  intent_expiry 等の時間境界は D5 の凍結層拡張採択まで契約レベルの宣言にとどまり、
  実行時強制は凍結層拡張の採択を待つ。

## 13. Open Issues

- OI-192-01: 孤児 Intent（CP2）の保持期間と除去規則。
- OI-192-02: Receipt 決定論的再生成に必要な永続化情報の最小集合。
- OI-192-03: INDETERMINATE 末尾区間の裁定（切り戻し vs 修復）— 独立裁定必要。
- OI-192-04: 監査ログ（D6 外部ストレージ）のスキーマ・保持・完全性契約
  （STEP-191 OI-191-15/16 と統合）。
- OI-192-05: 直列化可能性の検証方法（モデル検査 / テスト設計）。
- OI-192-06: intent_expiry と D5 凍結層拡張（AuthorityRegistry.valid）の接続。

## 14. 非目標

- 実装・テスト・採択・Freeze は本ドラフトの範囲外。
- 凍結層のスキーマ変更は範囲外。
- 分散ノード間の合意プロトコル（STEP-187 領域）は範囲外。本契約は単一
  正準追記経路を前提とする。

## 15. 状態結論

STEP-192 status: draft complete（v0.1.0）。
Adoption、implementation、validation、acceptance、Freeze は未確立。
依存ドラフト（190/191）が NOT_ADOPTED である事実は本ドラフトの採択可能性を
自動的に支持しない。上流ドラフトは証拠なしには production guarantee として
扱われてはならない（STEP-190/191 より継承）。
