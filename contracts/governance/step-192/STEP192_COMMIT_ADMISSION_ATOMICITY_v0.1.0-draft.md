# Filing Record（ファイリングメタデータ — ドラフト本文の一部ではない）

FILED: 2026-10-21 (Asia/Tokyo)
FILING: D4 HOLD 解除（同日）に基づく STEP-192 ドラフト着手（../ADJUDICATIONS.md 参照）
FILING_STATUS: FILED_AS_DRAFT_ARTIFACT → REVISED_BY_ADOPTION (v0.2.0-draft, 2026-10-23)
REVISION_RECORD: v0.1.0-draft 2026-10-21 初回 filing; v0.2.0-draft 2026-10-23 — D13 採択裁定の適用条件に基づく正式改訂（D7〜D12 語義のドラフト本文反映、検証ステータス更新）。v0.1.0 の filing 履歴は本記録で保持。
SOURCE_PROVENANCE: 本セッションで新規作成。予定範囲の正本は step-191 filing §21
  （paste_4_142951.txt L668-682、sha 0f8e41e8… の一部）。裁定 D2/D3/D5/D6 を適用。
ORIGIN: Hermes agent draft (user-directed kickoff, 2026-10-21)
CANONICAL_MUTATION: NONE（ドラフトの記録であり、採択・実装・Freeze ではない）
<<<FILING-END>>>

# STEP-192 — Commit Admission Atomicity / Transaction Binding / Durable Commit Receipt / Recovery Reconciliation Contract

STEP_ID: 192
VERSION: 0.2.0-draft
STATUS: DRAFT_COMPLETE
NORMATIVE_STATUS: ADOPTED_CONTRACT_LEVEL（D13 裁定 2026-10-23。留保: 凍結層拡張契約は未採択 — CausalContext SSOT 監査 MUST 継続、実装ゲートは独立、凍結層 read-only 維持）
ADOPTION_STATUS: ADOPTED_CONTRACT_LEVEL（D13 裁定 2026-10-23）
IMPLEMENTATION_STATUS: NOT_VERIFIED（モデル検証 PASS は実装検証ではない — VERIFICATION_IS_NOT_AUTHORIZATION）
TEST_STATUS: EXECUTED_MODEL_LEVEL（pytest 139 passed / sweep evidence — 本番実装ゲートは未実施）
REPOSITORY_INSPECTION: PERFORMED_MODEL_LEVEL（L1 参照モデル contracts/governance/step-192/validation/ に対する検査実施。本番実装の検査は未実施）
COMMIT_ATOMICITY_VALIDATION: EXECUTED_MODEL_LEVEL（INV-01/INV-06 全保持）
COMMIT_RECEIPT_VALIDATION: EXECUTED_MODEL_LEVEL（INV-02 全保持）
CRASH_RECOVERY_VALIDATION: EXECUTED_MODEL_LEVEL（§7 CP1..CP6 網羅・INV-04 全保持）
IDEMPOTENCY_RECONCILIATION_VALIDATION: EXECUTED_MODEL_LEVEL（INV-03/INV-04 全保持）
LINEARIZATION_VALIDATION: EXECUTED_MODEL_LEVEL（証拠: results_digest 94ab2a5a66cd1ba3e332ddc4ed494379829b4eb027bac0e34c342fbee6003fd1、tier1 網羅 1602 ケース + tier2 fuzz 300 ケース violations_total=0、受理ゲート AG-192-05a/b/c 充足。正本: contracts/governance/step-192/validation/）
DEPENDS_ON: STEP-190 / STEP-191（ドラフト・NOT_ADOPTED）, 凍結層 v2.8.0-C（read-only 前提）
ADJUDICATIONS_APPLIED: D2（契約レベルスキーマのみ。凍結層不変更）, D3（half-open [a,b)・gapless 連結）,
  D5（認可済み governance event は正準チェーン）, D6（拒否・監査記録は Canonical History 外）,
  D7（Receipt 再生成の最小永続化情報）, D8（INDETERMINATE 区間規則）, D9（孤児 Intent 転送）,
  D10（監査ストア契約 I1..I6）, D11（直列化可能性検証 V1..V6）, D12（位置ベース revocation）,
  D13（採択裁定・検証結果の公式反映）
TIMEZONE: Asia/Tokyo

本書は分析・設計ドラフトであり、採択・実装・受理の証明ではない。
すべての MUST は正式採択まで拘束力を持たない。
（v0.2.0-draft 改訂注記: D13 採択裁定により STEP-192 契約は契約レベルで採択済み。
  凍結層拡張契約の採択は別途 CausalContext SSOT 監査（D12 X4）を前提とし、
  実装・受理・Freeze は依然として未確立。モデルレベル検証の PASS は
  実装検証の PASS でも受理（ACCEPTANCE）でもない。）

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

### 10.1 検証手法と受理ゲート（D11 適用 — D13 採択裁定時に本文へ反映）

二層検証（D11 V4）:
- Tier 1 網羅モデル検査: 限定状態空間の全枚挙 — ops 1..3 × crash point
  CP1..CP6（CP4 は survives/lost の二分岐）× audit 失敗 ops の部分集合 ×
  再起動 0..2。計 1602 ケース。
- Tier 2 property fuzz: 固定 corpus seed（既定 19205）で生成 300 ケース。
  回帰コーパスとして複数 seed（0/1/12345/19205）で再実行可能。

不変条件（D11 V3）:
- INV-01: commit 済み正準 prefix の gapless 連結（position 連続・prev_hash 連鎖）
- INV-02: Receipt 一意性と決定論的再生成のバイト一致（§6/§7 CP5）
- INV-03: 復旧状態の再起動回数・時刻非依存（上の決定論保証）
- INV-04: 孤児 Intent パイプライン（保持→解決→転送）と転送の監査冪等性（D9 G1..G4）
- INV-05: NO_SILENT_DISCARD 1:1（退避区間と DISCARDED_INTERVAL 監査記録の対応、D10 I4）
- INV-06: 永続化 happens-before が正準順序で保持される（§5）
- INV-07: 監査障害は復旧分類を変えない（S4 / §11）
- INV-08: 監査書込み失敗 → Admission HOLD、commit 済み Finality は無傷（D10 I5）

ハーネス規律（D11 V6）:
- INV-H1: sweep 集計は PYTHONHASHSEED・反復順序に依存しない（順序非依存の
  集約 + results_digest による照合）。

受理ゲート（D11）:
- AG-192-05a: Tier 1 網羅の完了と INV-01..08 の全保持
- AG-192-05b: Tier 2 fuzz の完了と INV-H1 の証明
- AG-192-05c: 回帰コーパスの固定 seed 再実行の証跡保持

実施結果（D13 記録、正本 contracts/governance/step-192/validation/）:
- Tier 1: 1602 ケース violations_total=0 / Tier 2: 300 ケース violations_total=0
- results_digest: 94ab2a5a66cd1ba3e332ddc4ed494379829b4eb027bac0e34c342fbee6003fd1
  （PYTHONHASHSEED 0/1/7/12345 で一致）
- 反例が発見された場合はモデルを静かに修正せず、必ずガバナンス裁定へ回付する。
- VERIFICATION_IS_NOT_AUTHORIZATION / TEST_PASS != ACCEPTANCE /
  ACCEPTANCE != GLOBAL_ACCEPTANCE: モデルレベル検証の PASS は実装検証でも受理でもない。

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

監査ストア契約（D10 I1..I5 — D13 採択裁定時に本文へ反映する適用条件に従い反映）:
- I1 完全性: 監査ストア MUST は Canonical History と独立な追記専用ハッシュチェーン
  （AuditEventID・監査列番号 s（正準 sequence の流用禁止）・prev-audit-hash・
  内容 sha256 commitment）。gap / prev-hash 不一致は AUDIT_INTEGRITY_FAULT として
  監査列自体に記録し照合を起動する。監査チェーンの破損は正準列の妥当性を
  無効化しない（§11 分離検証）。外部タイムスタンピング・正準 checkpoint commit は
  強化オプションとして留保（本契約では MUST ではない）。
- I2 保持下限（証拠依存）: 障害記録（RECEIPT_REISSUE_FAULT・INVALID_COMMIT・
  AUDIT_INTEGRITY_FAULT・照合イベント・DISCARDED_INTERVAL）は対応する正準区間が
  検証可能である限り保持。孤児 Intent 転送レコード（D9 G3）は該当 OperationID の
  試行系譜が照合可能である限り保持。wall-clock による保持期限・GC は禁止。
- I3 容量圧迫（二段アーカイブ）: ライブ監査ストア + 監査アーカイブ。圧迫トリガーは
  監査列番号の構造的条件（時刻で定義しない）。転送は閉合済みセグメントのみ・冪等。
  転送時にアーカイブ側で prev-audit-hash 連鎖の再検証 MUST、除去は再検証成功後にのみ
  （verify-then-remove）。
- I4 DISCARDED_INTERVAL（フォールバック表現）: reason code・破棄区間の論理記述・
  破棄バイト列の逐語保存（framing メタデータ付き）・sha256 commitment・承認した
  照合イベントへの参照・破棄時点のチェーン状態の写し。破棄バイト列自体が監査
  チェーンに参加し後日再検証可能。NO_SILENT_DISCARD: 失われたバイトは
  DISCARDED_INTERVAL レコードと 1:1 対応（INV-05）。自動復帰は行わない。
- I5 監査保存障害: 監査記録は Admission に対して MUST、Commit Finality に対しては
  NOT MUST。監査書込み失敗 → 新しい Admission Decision は HOLD（commit 済み Finality
  は無傷 — INV-08）。欠落は AUDIT_GAP として追記記録し照合で補充。保存関係は物理分離 +
  参照単方向（監査→正準のみ、履歴の純度 D6）。2 フェーズコミットは導入しない。
  順序規則: admission-before-intent / receipt-after-record。
  復旧再実行に対する監査追記の論理レコード単位冪等性（同一 event_type +
  operation_id + 正準 content の二重追記禁止）は I1 の追記専用性から導かれる
  ハーネス実装規則として確立した（D11 検証で確認、D9 G3 冪等転送の鏡像）。

## 12. 凍結層との関係

- 本契約は凍結層 v2.8.0-C への変更を要求しない（D2: DEFERRED_TO_CONTRACT_LEVEL）。
  OperationID / Intent / Receipt / Idempotency Record は契約レベルのスキーマ定義である。
- 凍結層に時刻・期限・失効の足場が存在しない（T-191-B）ため、
  intent_expiry 等の時間境界は D5 の凍結層拡張採択まで契約レベルの宣言にとどまり、
  実行時強制は凍結層拡張の採択を待つ。
- 権限 revocation は位置ベースで意味づけられる（D12 X1）: revocation は
  governance event として正準チェーンに位置づけられ、その位置以降の Admission
  判定（AuthorityRegistry.valid）にのみ影響する。NO_RETROACTIVE_INVALIDATION（D12 X2）:
  revocation は失効時点より前の commit 済み操作・Receipt の正当性を遡って無効化しない。
  intent_expiry 接続（OI-192-06）の契約レベル解決は D12 により確立済みであり、
  凍結層拡張（AuthorityRegistry の拡張）の採択は別途 CausalContext SSOT 監査 MUST
  （D12 X4）を前提とする。凍結層拡張契約は本採択（D13）の対象ではない。

## 13. Open Issues

すべて解決済み（D13 採択裁定時点で OI-192-01..06 の全クローズを確認。正本は
../ADJUDICATIONS.md の D9 / D8 / D7 / D10 / D11 / D12 各裁定）:

- OI-192-01: 孤児 Intent（CP2）の保持期間と除去規則 — RESOLVED（D9: reconcile
  トリガー転送、wall-clock GC 禁止）。
- OI-192-02: Receipt 決定論的再生成に必要な永続化情報の最小集合 — RESOLVED（D7）。
- OI-192-03: INDETERMINATE 末尾区間の裁定（切り戻し vs 修復） — RESOLVED（D8）。
- OI-192-04: 監査ログのスキーマ・保持・完全性契約（OI-191-15/16 統合） —
  RESOLVED（D10 I1..I5、§11 反映済み）。
- OI-192-05: 直列化可能性の検証方法 — RESOLVED（D11 V1..V6 二層検証。実施完了、
  §10.1 に結果記録）。
- OI-192-06: intent_expiry と D5 凍結層拡張（AuthorityRegistry.valid）の接続 —
  RESOLVED（D12 位置ベース revocation + NO_RETROACTIVE_INVALIDATION、§12 反映済み）。
  凍結層拡張契約の採択は CausalContext SSOT 監査 MUST（D12 X4）が前提証拠として
  継続。Lean 形式化は強化オプションとして留保（D11）。

## 14. 非目標

- 実装・受理（acceptance）・Freeze は本契約の範囲外（採択とモデルレベル検証は
  D13 により契約レベルで確立済み。実装・受理・Freeze は未確立のまま）。
- 凍結層のスキーマ変更は範囲外（凍結層 read-only 維持）。
- 分散ノード間の合意プロトコル（STEP-187 領域）は範囲外。本契約は単一
  正準追記経路を前提とする。

## 15. 状態結論

STEP-192 status: ADOPTED_CONTRACT_LEVEL（v0.2.0-draft、D13 裁定 2026-10-23）。
OI-192-01..06 すべて解決済み（§13）。直列化可能性検証はモデルレベルで実施完了し
受理ゲート AG-192-05a/b/c 充足（§10.1、正本 contracts/governance/step-192/validation/）。
Implementation、acceptance、Freeze は未確立。凍結層拡張契約は未採択
（CausalContext SSOT 監査 MUST 継続）。実装ゲートは独立であり、
モデルレベル検証の PASS は実装検証の PASS でも受理でもない
（VERIFICATION_IS_NOT_AUTHORIZATION / TEST_PASS != ACCEPTANCE /
ACCEPTANCE != GLOBAL_ACCEPTANCE）。
依存ドラフト（190/191）が NOT_ADOPTED である事実は本ドラフトの採択可能性を
自動的に支持しない。上流ドラフトは証拠なしには production guarantee として
扱われてはならない（STEP-190/191 より継承）。
