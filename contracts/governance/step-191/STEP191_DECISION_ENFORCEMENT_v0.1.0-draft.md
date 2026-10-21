# Filing Record（ファイリングメタデータ — ドラフト本文の一部ではない）

FILED: 2026-10-21 (Asia/Tokyo)
FILING: D1 裁定に基づくファイリングフェーズ（../ADJUDICATIONS.md 参照）
FILING_STATUS: FILED_AS_DRAFT_ARTIFACT
NORMATIVE_STATUS: PROPOSED | ADOPTION_STATUS: NOT_ADOPTED | IMPLEMENTATION_STATUS: NOT_VERIFIED
FILING はステータスを変更しない。ARTIFACT_EXISTENCE != NORMATIVE_ADOPTION。
CANONICAL_MUTATION: NONE（ドラフトの記録であり、採択・実装・Freeze ではない）
SOURCE_PROVENANCE: ~/.hermes/pastes/paste_4_142951.txt lines 1-682（正本・全文）
  注: paste_2_134928.txt lines 1022-1043 は STEP-191 英語プレビュー（22行）のみで全文ではない。
SOURCE_SHA256: 0f8e41e81b31fc7c3bd7426cf00c7a8a9e35211ef47e7f88a20af8f40fd483c9
BODY_SHA256: 0f8e41e81b31fc7c3bd7426cf00c7a8a9e35211ef47e7f88a20af8f40fd483c9
AUDIT_EVIDENCE: ~/audit-191/evidence_ledger_191.json (E-191-001..010), ~/audit-191/CLOSURE_REPORT_191.md (A191-E-REAL)
ANALYSIS: ~/design-step191/STEP191_SPEC_ANALYSIS.md, ~/design-step191/STEP191_DESIGN_PROPOSAL_v0.2.md
REPO_BASELINE: Chron-LLM @ b231635452dd6ccd75f9f4ec9fbb40c5de510afa (backup/home-2026-08-12-0219, worktree clean)
<<<FILING-END>>>

STEP-191 — Canonical History Decision Enforcement / Authorization Binding / Commit Admission / Policy Execution Contract
STEP_ID: 191
VERSION: 0.1.0-draft
STATUS: DRAFT_COMPLETE
NORMATIVE_STATUS: PROPOSED
ADOPTION_STATUS: NOT_ADOPTED
IMPLEMENTATION_STATUS: NOT_VERIFIED
TEST_STATUS: NOT_EXECUTED
REPOSITORY_INSPECTION: NOT_PERFORMED
DECISION_BINDING_VALIDATION: NOT_EXECUTED
AUTHORIZATION_VALIDATION: NOT_EXECUTED
FRESHNESS_REVOCATION_VALIDATION: NOT_EXECUTED
POLICY_DETERMINISM_VALIDATION: NOT_EXECUTED
COMMIT_ADMISSION_VALIDATION: NOT_EXECUTED
TOCTOU_VALIDATION: NOT_EXECUTED
IDEMPOTENCY_VALIDATION: NOT_EXECUTED
CANONICAL_MUTATION: NONE
GLOBAL_ACCEPTANCE: NOT_ASSESSED
FREEZE_STATUS: NOT_AUTHORIZED
TIMEZONE: Asia/Tokyo
1. 目的・適用範囲
本契約は、STEP-190 で区別した Proof Verification、Audit Decision、Authorization、Commit Admission、Commit Finality を実行時に混同なく強制するための規範候補を定義する。
対象：
判定と実行要求の厳密な結合。
認可証拠の意味論と適用範囲。
判定の鮮度、期限、失効、リプレイ防止。
決定論的 Policy Evaluation。
Commit Admission の必要条件。
TOCTOU（検査時と使用時の状態乖離）の防止。
Retry、冪等性、結果不明状態の扱い。
拒否・例外・復旧経路の監査可能性。
Canonical History に対する非変更保証。
1.1 非目標
Canonical History の再設計。
STEP-190 の Proof Object や Audit Decision の再定義。
具体的な暗号方式・トークン形式の最終選定。
既存コードの変更、実装、実行試験。
例外による認可要件の暗黙的な緩和。
未確認の Commit を成功または失敗と推定すること。
本ドラフト単独による Freeze、採用、全体受入れ。
2. 規範原則と権限境界
以下を本STEPの基礎制約とする。
VALID_PROOF != AUDIT_DECISION
AUDIT_DECISION != AUTHORIZATION
AUTHORIZATION != COMMIT_ADMISSION
COMMIT_ADMISSION != COMMIT_FINALITY

STALE_DECISION != CURRENT_PERMISSION
REVOKED_AUTHORITY != VALID_AUTHORIZATION
REJECTION => NO_CANONICAL_MUTATION
機構
判定対象
それ自体では保証しないこと
Proof Verification
証拠の妥当性
操作の許可
Audit Decision
指定スコープに対する判定
現在の認可、Commit
Authorization
特定操作の実行権限
Commit の受理・永続化
Commit Admission
Commit 処理開始の必要条件
永続化の成功
Commit Finality
Commit の確定状態
それ以外の操作の許可

権威境界： Policy と Authorization の検証結果を消費する決定論的 Kernel が、Commit Admission を唯一制御する。LLM、Projection、UI、外部 Agent は、単独で認可・Admission・Commit Finality を確定できない。
本契約が提案する追加の規範制約：
UNBOUND_DECISION => NO_ADMISSION
UNBOUND_AUTHORIZATION => NO_ADMISSION
EXPIRED_AUTHORIZATION => NO_ADMISSION
REVOKED_AUTHORITY => NO_ADMISSION
POLICY_INDETERMINATE => NO_ADMISSION
ADMISSION != DURABLE_COMMIT
UNKNOWN_COMMIT_STATUS != COMMIT_FAILURE
3. 用語と規範的意味
Action Request：実行を要求する操作と、その対象・引数・適用スコープを含む要求。
Decision Binding：Audit Decision と Action Request の同一性・適用範囲を検証可能な形で結合すること。
Authorization Evidence：操作を許可する権限、ポリシー評価、委任などを裏付ける検証可能な証拠。
Admission Record：Commit Admission の判定結果と、その判定に用いた入力・バージョンを記録する証跡。
Admission Key：操作の同一性と再試行の扱いを識別するためのキー。
TOCTOU：認可・ポリシー検査時と Commit 時の間で、対象状態や権限が変化する問題。
Commit Finality：Canonical History への変更が、実装で定義された永続化・確定条件を満たした状態。
規範語 MUST、MUST NOT、SHOULD、MAY は採用後の要件候補を示す。現在はすべて提案段階であり、既存システムに適用済みであることを意味しない。
4. Action Binding / Decision Identity
4.1 要求の識別
Action Request は、少なくとも以下を識別可能でなければならない。
action_request:
  request_id: REQUIRED
  action_type: REQUIRED
  subject_ref: REQUIRED
  target_ref: REQUIRED
  scope: REQUIRED
  canonical_history_ref: REQUIRED
  expected_history_position: REQUIRED
  payload_digest: REQUIRED
  requested_by: REQUIRED
  idempotency_key: REQUIRED
各フィールドの具体的な型・正規化・ダイジェスト方式は別途 Schema Contract で固定する。payload_digest は、操作の意味に影響する引数を漏れなく対象としなければならない。
4.2 判定の結合
Audit Decision を Action Request に適用するには、少なくとも以下が一致しなければならない。
action_type
subject_ref
target_ref
scope
canonical_history_ref
対象操作の payload またはその正規化済みダイジェスト
Policy Profile ID と Version
Decision の一意な識別子と評価結果
別操作、別対象、別スコープ、別 Payload に対する判定の流用は禁止する。
Decision の適用範囲が一部しか一致しない場合、暗黙に適用範囲を拡大してはならない。部分一致の扱いは、明示的な Policy Rule として定義され、検証されている場合に限る。
4.3 判定の意味
ALLOW は、判定時点・指定スコープにおける Audit Decision の結果であり、単独では Authorization または Commit Admission を意味しない。
ALLOW_WITH_EXCEPTION は、例外の範囲・権限・期限・理由が別途検証されるまで Admission を許可しない。
DENY、HOLD、NOT_EVALUATED は、通常の Admission に対する許可根拠として使用してはならない。
5. Authorization Evidence / Token Model
5.1 認可証拠の必要属性
認可証拠は、実装方式に応じて少なくとも以下を検証可能にする。
authorization_evidence:
  authorization_id: REQUIRED
  issuer_identity: REQUIRED
  subject_identity: REQUIRED
  action_constraints: REQUIRED
  resource_constraints: REQUIRED
  scope_constraints: REQUIRED
  policy_profile_id: REQUIRED
  policy_profile_version: REQUIRED
  issued_at: REQUIRED
  not_before: REQUIRED
  expires_at: REQUIRED
  revocation_reference: REQUIRED
  request_binding_digest: REQUIRED
  evidence_integrity: REQUIRED
この構造は論理モデルであり、最終 JSON Schema、署名方式、トークンエンコーディングを確定するものではない。
5.2 検証要件
Admission 前に、Kernel は次を検証しなければならない。
発行主体の信頼性。
証拠の完全性と真正性。
主体・操作・対象・スコープの一致。
not_before、expires_at と現在時刻の適合性。
発行主体・委任元・権限の失効状態。
必要な Policy Profile の一致。
Decision と Action Request の結合。
リプレイ防止条件。
必要な依存 Proof の妥当性。
検証に必要な情報が欠落していないこと。
検証不能・不明・矛盾は成功として扱ってはならない。
5.3 最小権限
認可は要求された Action・Target・Scope に必要な範囲に限定する。包括的な権限を、明示的な根拠なく個別操作へ転用してはならない。
認可証拠が正しく署名されていることは、その証拠に記載された権限が現在も有効であることを単独では保証しない。
6. Freshness / Expiry / Revocation / Replay
6.1 鮮度
Admission は、Decision・Authorization・Policy Profile・対象 History の各依存関係が、その Admission 時点で適用可能であることを要求する。
FRESHNESS =
  DECISION_VALID
  AND AUTHORIZATION_CURRENT
  AND POLICY_VERSION_ACCEPTABLE
  AND HISTORY_PRECONDITION_MATCHED
  AND REVOCATION_CHECK_SATISFIED
これは論理的な必要条件を示す式であり、検証済み実装を意味しない。
6.2 有効期限と時計
有効期限の境界条件は明示的に定義しなければならない。
時刻源、時計ずれの許容範囲、単調時計の利用条件を定義しなければならない。
時刻が信頼できない場合、期限検証を省略してはならない。
有効期限の延長や時計ずれの許容は、黙示的に実施してはならない。
6.3 失効
失効情報を確認できない場合の処理は Policy で明示する。失効確認が必須の権限については、失効状態が不明であることを有効と見なしてはならない。
失効の検出後は、影響を受ける未実行要求の Admission を拒否または保留する。すでに確定した Canonical History を、失効だけを理由に書き換えてはならない。
6.4 リプレイ防止
同じ認可証拠や Decision の再提示を、別の操作または別の対象への新たな許可として扱ってはならない。
request_id と idempotency_key の役割を区別する。
Admission の重複判定に必要な識別情報を保持する。
同一キーに異なる Payload が結合された場合は拒否する。
消費済みトークンの再使用規則を明示する。
再試行と新規操作を、履歴上で識別可能にする。
7. Deterministic Policy Execution
7.1 入力の固定
Policy Evaluation の入力には、必要に応じて以下を含める。
正規化済み Action Request
対応する Audit Decision と Proof References
Authorization Evidence
Canonical History の対象位置または版
Policy Profile ID・Version
Trust / Revocation 状態
明示的に許可された時刻入力
Validator / Evaluator のバージョン
7.2 決定論的評価
同一の正規化入力、同一の Policy Profile、同一の明示的評価コンテキストに対して、Policy Evaluator は同一の結果を返さなければならない。
SAME_INPUT
+ SAME_POLICY_VERSION
+ SAME_EVALUATION_CONTEXT
=> SAME_POLICY_RESULT
未固定の環境変数、暗黙の既定値、非決定論的な LLM 出力を、確定的な Admission 根拠として使用してはならない。
外部情報が必要な場合は、情報の取得結果・取得時点・完全性・適用規則を入力として固定する。入力が固定できない場合は、評価結果を INDETERMINATE 相当として扱い、必要な Admission を行わない。
7.3 Policy Version
Policy Profile の変更は、既存 Decision や Authorization に自動適用されない。旧版を使用できる条件、新版への再評価条件、失効時の扱いを明示しなければならない。
Policy Version が不明、未対応、または必要な意味論が解釈できない場合、古い版や弱いルールへの暗黙のダウングレードは禁止する。
8. Commit Admission Preconditions
Commit Admission は、少なくとも以下の条件がすべて成立した場合に限り許可される。
ADMISSION_ALLOWED =
  REQUEST_SCHEMA_VALID
  AND DECISION_BOUND
  AND DECISION_ACCEPTABLE
  AND AUTHORIZATION_VALID
  AND AUTHORIZATION_CURRENT
  AND POLICY_EVALUATION_PASS
  AND PROOF_REQUIREMENTS_SATISFIED
  AND HISTORY_PRECONDITION_MATCHED
  AND TARGET_STATE_PRECONDITION_MATCHED
  AND IDEMPOTENCY_CHECK_PASS
  AND TRUST_REQUIREMENTS_SATISFIED
  AND ATOMIC_BINDING_AVAILABLE
ここで PASS は、必要な条件が検証済みであることを意味する。未評価、未対応、部分的な成功を PASS に変換してはならない。
8.1 Admission の記録
Admission Record は少なくとも以下を記録する。
Admission ID
Action Request ID と正規化済み要求のダイジェスト
Decision ID
Authorization ID または参照
Policy Profile ID・Version
History Precondition
評価結果と失敗理由コード
Evaluator / Validator Version
判定時刻と使用した時刻源
関連する証拠参照
Admission Record は監査証拠であり、それ自体が Canonical History の Commit を意味するものではない。
8.2 拒否時の不変条件
Admission が拒否・保留・未評価となった場合、対象操作による Canonical History の変更は禁止する。拒否監査記録の保存先が Canonical History と異なる場合、その記録の保存を Canonical Mutation と混同してはならない。
拒否記録を Canonical History に記録する設計を採用する場合、その記録操作自体に対する権限・Commit 規則を別途定義する。
9. TOCTOU 防止 / Atomic Binding
9.1 問題定義
Policy Evaluation が成功した後、実際の Commit 前に次のいずれかが変化すると、Admission の根拠と実行対象が一致しなくなる。
Canonical History の現在位置
対象 Entity または Resource の状態
Authorization の失効状態
Policy Profile の適用状態
Action Payload
対象 Scope
必須 Proof の妥当性または有効性
9.2 必須制約
Admission と Commit の間で、操作の意味を変える入力を差し替えてはならない。
Admission 時に検証した要求と Commit 対象の要求は、正規化済み同一性条件を満たさなければならない。
History Precondition が変化した場合、古い Admission を無条件に再利用してはならない。
認可の鮮度を維持できない場合、再評価または拒否を行う。
必須の検査と Commit の間に競合が発生した場合、競合検出と回復の規則を適用する。
LLM や外部 Agent による再解釈を、Admission 済み要求の暗黙の変更として許容してはならない。
9.3 原子性の実現方式
具体的な実装方式は未確定だが、少なくとも次のいずれかにより検査と実行の間の不整合を防止する必要がある。
History Position に対する Compare-and-Swap。
Admission と Commit を結合するトランザクション。
対象状態のバージョン検査を含む直列化可能な Commit 処理。
同等の保証を持つ決定論的競合制御。
これらの方式は代替候補であり、すべてを同時に採用する要件ではない。採用方式の保証範囲と障害時の限界は明文化しなければならない。
10. Retry / Idempotency / Unknown Commit Status
10.1 状態の分離
REQUEST_RECEIVED
  -> POLICY_EVALUATED
  -> ADMISSION_GRANTED
  -> COMMIT_ATTEMPTED
  -> COMMIT_CONFIRMED
   | COMMIT_REJECTED
   | COMMIT_STATUS_UNKNOWN
このライフサイクルは提案状態モデルである。COMMIT_STATUS_UNKNOWN は成功・失敗のいずれでもない。
10.2 冪等性
同じ idempotency_key の再試行は、同じ論理操作に属することを検証しなければならない。
キーと Payload の組合せが同一なら、既存操作の状態を照会してよい。
キーが同一で Payload が異なる場合は拒否する。
既に Commit が確定している場合、再試行によって同一の論理操作を二重適用してはならない。
失敗が確定していない操作を、失敗したものとして新規実行してはならない。
10.3 Commit 状態不明
Commit 処理中のクラッシュ、応答喪失、タイムアウトなどで結果が不明になった場合：
状態を COMMIT_STATUS_UNKNOWN として保持する。
Canonical History または信頼できる Commit Receipt を用いて確定状態を照合する。
同一操作の確定が確認できた場合、既存結果に収束させる。
未確定であることを十分な根拠で確認できた場合のみ、規定された再試行経路へ進む。
照合不能の場合は保留し、重複 Commit を防止する。
TIMEOUT != FAILURE、NO_RESPONSE != NO_COMMIT、RETRY != NEW_OPERATION を維持する。
10.4 Admission の再利用
Admission の再利用は、要求同一性、Policy Version、Authorization の有効性、History Precondition、リプレイ防止状態を再検証した場合に限る。Admission の過去の成功だけを理由に現在の実行を許可してはならない。
11. Denial / Exception / Recovery
11.1 拒否理由
拒否は、可能な限り機械可読な理由コードに分類する。
REQUEST_INVALID
DECISION_UNBOUND
DECISION_DENIED
DECISION_STALE
AUTHORIZATION_INVALID
AUTHORIZATION_EXPIRED
AUTHORITY_REVOKED
POLICY_DENIED
POLICY_INDETERMINATE
PROOF_REQUIREMENT_UNSATISFIED
HISTORY_PRECONDITION_MISMATCH
TARGET_STATE_CONFLICT
REPLAY_DETECTED
IDEMPOTENCY_CONFLICT
ATOMIC_BINDING_UNAVAILABLE
TRUST_STATE_UNKNOWN
COMMIT_STATUS_UNKNOWN
INTERNAL_VALIDATION_FAILURE
これらは候補コードであり、正式な Closed Vocabulary としては未採用である。未知の理由コードを成功扱いしてはならない。
11.2 例外
ALLOW_WITH_EXCEPTION は一般的な拒否回避手段ではない。例外を許可する場合は、少なくとも次を満たさなければならない。
例外を許可する主体が明示されている。
例外の対象 Action・Resource・Scope が限定されている。
理由、期限、根拠、監査参照が記録される。
例外によって満たされない要件が明示される。
Canonical History の整合性や Commit Authority の排他的権限を破壊しない。
未確認の Commit を確定済みに偽装しない。
必須要件の免除が許可されていない場合、その要件を免除しない。
例外が許可されても、満たされていない要件を満たしたことにはならない。
11.3 復旧
復旧は、失敗の種類に応じて以下から選択する。
入力修正後の新規要求。
Decision の再評価。
Authorization の再取得または再検証。
Policy Profile の明示的な再評価。
History Precondition の再取得。
Commit 状態の照合。
権限を持つ主体による明示的な例外処理。
HOLD 状態の維持と人間による裁定。
復旧時に元の失敗記録を消去したり、拒否を成功として再分類したりしてはならない。
12. Audit / Decision Provenance
各 Admission の判断を、後から独立に検証できるようにする。
監査記録には、適用された入力、依存証拠、Decision、Authorization、Policy Profile、Evaluator Version、History Precondition、結果、理由コード、関連する Commit ID または状態不明参照を含める。
監査証跡は次を区別する。
要求の受領
Policy Evaluation の完了
Admission の許可・拒否・保留
Commit の試行
Commit の確定・拒否・状態不明
失効検出
例外の申請・許可・適用
復旧・再評価
監査証跡の完全性と Canonical History の正当性は別々に検証する。監査記録が存在することだけを根拠に、操作が正当に Commit されたと結論づけてはならない。
13. Failure Matrix
障害・不整合
Admission
Canonical Mutation
必須対応
Decision の対象不一致
拒否
禁止
再評価
Authorization 期限切れ
拒否
禁止
再認可
失効状態が不明（確認必須）
拒否または保留
禁止
失効状態の照合
Policy 評価が不確定
保留
禁止
入力・Policy の確定
History Precondition 不一致
拒否
禁止
状態再取得・再評価
同一キー・異なる Payload
拒否
禁止
衝突監査
Admission と Commit の間の競合
中止または再評価
不正な変更は禁止
競合解決
Commit 応答喪失
状態不明
推測による追加変更は禁止
状態照合
監査記録の保存失敗
Policy に従い保留・拒否
要件に反する Commit を禁止
監査経路の復旧
未知の失敗コード
拒否または保留
禁止
明示的な裁定

監査記録の保存失敗時に Commit を許可できるかは、監査の必須性、保存先、原子性保証によって決まる。要件が未定義のまま成功扱いしてはならない。
14. Invariants — STI-191-01..20
全件 PROPOSED / NOT_VERIFIED。
ID
不変条件
STI-191-01
Proof Validity と Audit Decision は別概念である。
STI-191-02
Audit Decision は Authorization を単独で構成しない。
STI-191-03
Authorization は Commit Admission を単独で構成しない。
STI-191-04
Commit Admission は Commit Finality を意味しない。
STI-191-05
Decision は Action・Target・Scope に結合される。
STI-191-06
Payload の意味的変更は既存 Decision の無条件再利用を無効にする。
STI-191-07
期限切れ Authorization では Admission しない。
STI-191-08
失効した権限を有効な認可として扱わない。
STI-191-09
必須の失効確認が不明なら成功としない。
STI-191-10
Policy Evaluation は固定入力・固定版に対して決定論的である。
STI-191-11
未対応 Policy Version への暗黙のダウングレードを禁止する。
STI-191-12
History Precondition の不一致は再検証を要求する。
STI-191-13
TOCTOU 防止の原子性または同等の競合制御を要求する。
STI-191-14
拒否された要求は対象 Canonical History を変更しない。
STI-191-15
同一 Idempotency Key と異なる Payload の組合せを拒否する。
STI-191-16
Retry は既存 Commit の重複適用を生じさせない。
STI-191-17
Commit 状態不明を成功・失敗へ推定変換しない。
STI-191-18
例外は明示的な権限・対象・期限・理由を持つ。
STI-191-19
監査証跡は Admission と Commit Finality を区別する。
STI-191-20
不明・未評価・矛盾を PASS に変換しない。

15. Test Candidates — ST-191-01..20
全件 NOT_EXECUTED。以下は試験候補であり、実行結果ではない。
ID
試験対象
期待結果
ST-191-01
有効 Proof・拒否 Decision
Admission 拒否
ST-191-02
別 Action の Decision 流用
拒否
ST-191-03
別 Target の Authorization 流用
拒否
ST-191-04
Scope 拡大による再利用
拒否
ST-191-05
Admission 前の期限切れ
拒否
ST-191-06
Admission 前の権限失効
拒否
ST-191-07
必須の失効照会が失敗
拒否または保留
ST-191-08
同一入力・同一 Policy Version の再評価
結果一致
ST-191-09
未対応 Policy Version
暗黙のダウングレードなし
ST-191-10
History Position の競合
Admission 無効化または再評価
ST-191-11
Admission 後の Payload 差し替え
Commit 拒否
ST-191-12
TOCTOU 競合の同時発生
不正な Commit を防止
ST-191-13
拒否要求の実行
対象 Canonical History 不変
ST-191-14
同一キー・同一 Payload の Retry
二重適用なし
ST-191-15
同一キー・異なる Payload
拒否
ST-191-16
Commit 成功後の応答喪失
状態照合により既存結果へ収束
ST-191-17
Commit 結果を照合できない
状態不明を維持
ST-191-18
必須要件を満たさない例外要求
拒否
ST-191-19
Admission Record と Commit Receipt の不一致
不整合検出
ST-191-20
未知の判定値・理由コード
成功扱いしない

16. Open Issues — OI-191-01..20
全件 OPEN。設計上の未決事項を明示する。
ID
未決事項
OI-191-01
Action Request の正規化規則
OI-191-02
Payload Digest の対象範囲と方式
OI-191-03
Decision と Authorization の結合フォーマット
OI-191-04
Authorization Token の形式・署名方式
OI-191-05
信頼できる時刻源と時計ずれの許容
OI-191-06
失効照会の一貫性・可用性保証
OI-191-07
Revocation 状態のキャッシュ許容条件
OI-191-08
Policy Version 移行と旧版の扱い
OI-191-09
History Position の競合制御方式
OI-191-10
Admission と Commit の原子性境界
OI-191-11
Admission Key の生成・保持・衝突処理
OI-191-12
Idempotency Record の永続化と保持期間
OI-191-13
Commit 状態不明時の照合プロトコル
OI-191-14
Commit Receipt の信頼性と検証要件
OI-191-15
監査記録と Canonical History の保存関係
OI-191-16
監査保存障害時の Admission 方針
OI-191-17
例外許可権限と委任の規則
OI-191-18
Decision・Authorization の失効伝播範囲
OI-191-19
失敗理由コードの Closed Vocabulary
OI-191-20
既存 STEP 群との統合・優先順位・競合規則

17. Acceptance Gates — AG-191-01..20
全件 NOT_ASSESSED。各 Gate の PASS は証拠を伴う検証後にのみ宣言できる。
ID
受入条件
AG-191-01
Action Request Schema が固定されている
AG-191-02
Decision Binding 規則が機械検証可能である
AG-191-03
Authorization Evidence の契約が固定されている
AG-191-04
期限と時刻境界の規則が固定されている
AG-191-05
失効確認の必須条件が定義されている
AG-191-06
リプレイ防止規則が定義されている
AG-191-07
Policy Evaluation の決定論性が検証されている
AG-191-08
Policy Version の互換性・移行規則が定義されている
AG-191-09
Commit Admission の全必要条件が閉じている
AG-191-10
History Precondition の検証が実装・試験されている
AG-191-11
TOCTOU 防止方式と保証範囲が検証されている
AG-191-12
Admission Record の Schema と意味論が固定されている
AG-191-13
拒否時の Canonical Mutation 不在が試験されている
AG-191-14
Idempotency と重複防止が試験されている
AG-191-15
Commit 状態不明からの復旧が試験されている
AG-191-16
例外経路が権限・スコープ制約を満たす
AG-191-17
監査証跡の完全性・検証可能性が確認されている
AG-191-18
ST-191-01..20 の実行結果と証拠が保存されている
AG-191-19
依存 STEP との矛盾・重複・未解決依存が裁定されている
AG-191-20
正式な採用判断と Freeze 承認が独立に記録されている

18. Proposed Artifact Tree
以下は作成候補であり、実際のファイル作成を意味しない。
contracts/step-191/
├── canonical_history_decision_enforcement_contract.md
├── schemas/
│   ├── action_request.schema.json
│   ├── authorization_evidence.schema.json
│   ├── admission_record.schema.json
│   └── admission_result.schema.json
├── policy/
│   ├── policy_execution_contract.md
│   ├── decision_binding_rules.yaml
│   └── failure_reason_codes.yaml
├── lifecycle/
│   ├── admission_state_machine.yaml
│   ├── retry_idempotency_contract.md
│   └── commit_status_reconciliation.md
├── validation/
│   ├── validator_contract.md
│   └── invariants.yaml
├── tests/
│   ├── test_matrix.yaml
│   └── acceptance_gates.yaml
└── evidence/
    └── README.md
19. Dependency Matrix
依存対象
必要な保証
現状
STEP-182〜189
先行契約との整合
未検証
STEP-190
Proof・Decision・Audit の意味論
未検証
Canonical History / WAL
正規履歴と位置識別
未検証
Commit Authority
排他的 Commit 権限
未検証
Policy Registry
Policy Version の識別・固定
未検証
Trust / Key Lifecycle
発行者検証・失効
未検証
Proof / Verification Layer
証拠の検証可能性
未検証
Audit / Evidence Store
判断・操作の監査証跡
未検証
Replay / Projection
派生状態と正規履歴の分離
未検証
Schema / Validator Layer
入力・出力の構造検証
未検証

依存先の存在、実装状況、既存仕様との整合は確認していない。依存の未解決は、STEP-191 の受入れを阻害し得る。
20. Adjudication / Status
STEP_ID: 191
DRAFT_COMPLETENESS: COMPLETE
NORMATIVE_ADOPTION: NOT_ADOPTED
REPOSITORY_INSPECTION: NOT_PERFORMED
SCHEMA_VALIDATION: NOT_EXECUTED
POLICY_DETERMINISM_TEST: NOT_EXECUTED
TOCTOU_TEST: NOT_EXECUTED
RETRY_IDEMPOTENCY_TEST: NOT_EXECUTED
FAILURE_RECOVERY_TEST: NOT_EXECUTED
INVARIANT_VERIFICATION: NOT_VERIFIED
OPEN_ISSUES: 20
ACCEPTANCE_GATES: 20
ACCEPTANCE_STATUS: NOT_ASSESSED
CANONICAL_MUTATION: NONE
GLOBAL_ACCEPTANCE: NOT_ASSESSED
FREEZE_AUTHORIZATION: NOT_AUTHORIZED
裁定
本STEPの設計上の中心は、判定を得たこと、認可を得たこと、Commit Admission を通過したこと、Commit が確定したことを、それぞれ独立した検証可能な事実として扱うことである。
特に、Admission と Commit の間の TOCTOU、再試行による二重適用、Commit 結果不明時の推測確定は、単なるログ記録では解決しない。排他的な Commit Authority、永続的な操作識別、競合制御、状態照合の契約が必要となる。
このドラフトは設計提案として完成しているが、実装・試験・採用・Freeze は完了していない。
21. 次の STEP
STEP-192 — Commit Admission Atomicity / Transaction Binding / Durable Commit Receipt / Recovery Reconciliation Contract
予定範囲：
Admission と Commit のトランザクション境界。
Commit Intent と操作識別子の固定。
WAL への記録順序と永続化保証。
Commit Receipt の生成・検証・一意性。
Crash Point ごとの復旧規則。
Commit 済み・未 Commit・判定不能の識別。
Idempotency Record と Canonical History の整合。
部分書込み・応答喪失・再起動後の照合。
Commit の線形化点と確定性。
監査証跡と Canonical History の整合性。
引き続き、設計ドラフトと実装・検証・採用・Freeze を明確に分離する。
