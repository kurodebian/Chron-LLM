# Filing Record（ファイリングメタデータ — ドラフト本文の一部ではない）

FILED: 2026-10-21 (Asia/Tokyo)
FILING: D1 裁定に基づくファイリングフェーズ（../ADJUDICATIONS.md 参照）
FILING_STATUS: FILED_AS_DRAFT_ARTIFACT
NORMATIVE_STATUS: PROPOSED | ADOPTION_STATUS: NOT_ADOPTED
FILING はステータスを変更しない。ARTIFACT_EXISTENCE != NORMATIVE_ADOPTION。
CANONICAL_MUTATION: NONE（ドラフトの記録であり、採択・実装・Freeze ではない）
SOURCE_PROVENANCE: ~/.hermes/pastes/paste_2_152201.txt lines 1-603（NCCI-218 全文）
SOURCE_SHA256: 2ec5dee77ef4386bb620d6ab8464d3bd52d92e767a7ceb08b4b899b8b8e7a475
BODY_SHA256: 2ec5dee77ef4386bb620d6ab8464d3bd52d92e767a7ceb08b4b899b8b8e7a475
AUDIT_EVIDENCE: ~/audit-218/evidence_ledger_218.json (E-218-001..010), ~/audit-218/CLOSURE_REPORT_218.md (A218-E-REAL)
ANALYSIS: ~/design-step218/STEP218_SPEC_ANALYSIS.md, ~/design-step218/STEP218_DESIGN_PROPOSAL_v0.2.md
REPO_BASELINE: Chron-LLM @ b231635452dd6ccd75f9f4ec9fbb40c5de510afa (backup/home-2026-08-12-0219, worktree clean)
<<<FILING-END>>>

# STEP-218 — 規範契約の閉包・依存関係・競合裁定契約

```
STEP_ID: 218
CONTRACT_ID: NCCI-218
TITLE: "Canonical History Governance Normative Closure / Cross-STEP Contract Inventory / Dependency Closure / Conflict Adjudication Contract"
VERSION: 0.1.0-draft
ASOF: 2026-10-18
TIMEZONE: Asia/Tokyo

DRAFT_STATUS: DRAFT_COMPLETE
NORMATIVE_STATUS: PROPOSED
ADOPTION_STATUS: NOT_ADOPTED
IMPLEMENTATION_STATUS: NOT_VERIFIED
REPOSITORY_INSPECTION: NOT_PERFORMED

CONTRACT_INVENTORY_VALIDATION: NOT_EXECUTED
DEPENDENCY_GRAPH_VALIDATION: NOT_EXECUTED
NORMATIVE_CONFLICT_VALIDATION: NOT_EXECUTED
OPEN_ISSUE_CLOSURE_VALIDATION: NOT_EXECUTED
CROSS_STEP_VALIDATION: NOT_EXECUTED

GLOBAL_ACCEPTANCE_READINESS: NOT_ASSESSED
ACCEPTANCE_STATUS: NOT_ASSESSED
CANONICAL_MUTATION: NONE
FREEZE_STATUS: NOT_AUTHORIZED
```

## 1. 目的

STEP-190〜STEP-217 の契約群を、個々の文書の集合としてではなく、依存関係・規範権限・証拠・状態遷移・受入条件を持つ一つの検証対象として監査可能にする。

本契約の目的は、新たな契約を無制限に追加することではない。既存契約の実体と相互関係を調査し、次のいずれかを証拠に基づいて判定することである。

1. 契約インベントリが不完全である。
2. 依存関係または規範上の競合が未解決である。
3. 規範上の欠落があり、追加契約が必要である。
4. 規範上の閉包が確認され、リポジトリ監査・実装検証へ移行できる。
5. 証拠不足により判定できない。

STEP番号が進んだこと、文書の草案が完成したこと、あるいは契約数が増えたことは、閉包の証明にならない。

## 2. 適用範囲

対象範囲は STEP-190〜STEP-217 と、本契約 STEP-218 である。

監査対象には、少なくとも次を含める。

- 契約ファイルとそのバージョン・ダイジェスト
- 採択状態および実装状態
- 入力・出力・依存契約
- 規範用語、状態、スキーマ、エラー分類
- 権限解決、ポリシー選択、Decision、Commit の境界
- 不変条件、テスト仕様、未解決事項、受入ゲート
- 証拠の出所、完全性、検証履歴
- STEP-200 が定める全体保証・受入・Freeze の前提条件

### 2.1 非目的

- 未確認のファイル・契約・テスト結果を実在するものとして扱わない。
- 契約草案を暗黙に規範採択しない。
- 監査中に既存ファイルや Canonical History を変更しない。
- 不明な規範をコードで補完しない。
- 未解決事項を単純な件数や多数決で解決しない。
- 本契約だけで Global Acceptance または Freeze を宣言しない。
- STEP-219 以降を自動的に生成しない。

## 3. 依存関係

| 契約群          | 監査対象となる主な責務                               |
| ------------ | ----------------------------------------- |
| STEP-190〜195 | 証拠、検証、Commit、WAL、完全性、インシデント復旧             |
| STEP-196〜198 | 規範登録、初期化、完全性、再現性                          |
| STEP-199〜201 | 検証証拠、全体保証、是正、再検証                          |
| STEP-202〜205 | キュー、障害復旧、決定性、DR                           |
| STEP-206〜209 | レプリケーション、分岐裁定、再照合、長期保証                    |
| STEP-210〜213 | ポリシー変更、実行時適用、可観測性                         |
| STEP-214〜216 | インシデント裁定、復旧調整、復旧保証                        |
| STEP-217     | Acceptance Grant、Decision Finality、再評価・取消 |
| STEP-218     | インベントリ、依存閉包、競合裁定、移行可否判定                   |

この表は監査対象を分類するための暫定的な整理であり、各契約の実ファイル・正式な依存宣言を確認した結果ではない。正式な依存関係はリポジトリ調査で確定する。

## 4. 規範公理

以下を本契約の不変条件とする。

```
INVENTORY != AUTHORITATIVE_REGISTRY
ARTIFACT_EXISTENCE != NORMATIVE_ADOPTION
DIGEST_MATCH != SEMANTIC_VALIDITY
SCHEMA_PASS != NORMATIVE_CONFORMANCE
TEST_PLAN != TEST_EXECUTION
TEST_PASS != ACCEPTANCE
ACCEPTANCE != GLOBAL_ACCEPTANCE
GLOBAL_ACCEPTANCE != FREEZE

DECLARED_DEPENDENCY != VERIFIED_DEPENDENCY
DEPENDENCY_ORDER != NORMATIVE_PRECEDENCE
LATEST_VERSION != AUTOMATIC_AUTHORITY
MAJORITY_AGREEMENT != CONFLICT_ADJUDICATION
MISSING_EVIDENCE != PASS
UNKNOWN_STATUS != VALID_STATUS
UNRESOLVED_MATERIAL_CONFLICT => AFFECTED_GATE_BLOCKED

CONTRACT_CLOSURE != IMPLEMENTATION_COMPLETION
IMPLEMENTATION_COMPLETION != ACCEPTANCE
ACCEPTANCE_GRANT != CANONICAL_COMMIT
REASSESSMENT != RETROACTIVE_MUTATION
AUDIT != REPAIR
CLOSURE_REPORT != CLOSURE_PROOF
```

## 5. 用語定義

- `Contract Inventory`: 確認可能な契約アーティファクトとその属性を列挙した監査対象一覧。
- `Normative Registry`: 採択権限、バージョン、適用範囲、優先規則を根拠付きで解決する登録情報。
- `Source of Authority`: 規範の採択・変更・競合裁定を認められた権限の根拠。
- `Dependency Edge`: 契約間の依存関係。型、方向、根拠、検証状態を持つ。
- `Normative Conflict`: 同じ対象・適用範囲について、同時に満たせない規範、定義、状態遷移、権限または受入条件。
- `Material Conflict`: 解決しない限り、適合性、権限、Canonical Integrity、受入可否のいずれかを判定できない競合。
- `Closure Report`: インベントリ、依存関係、競合、未解決事項、証拠、判定を集約した報告書。
- `Closure Readiness`: 必須監査項目が根拠付きで判定され、次の工程へ移行できる状態。プロジェクト全体の完了を意味しない。

定義の不一致が発見された場合、本契約の定義を自動的に既存契約へ遡及適用してはならない。競合として記録し、権限に基づく裁定を要求する。

## 6. 契約インベントリのデータモデル

各契約エントリは、取得できる範囲で次のフィールドを持つ。

```
contract_entry:
  step_id: REQUIRED
  contract_id: REQUIRED_IF_DECLARED
  title: REQUIRED_IF_DECLARED
  version: REQUIRED_IF_DECLARED
  artifact_path: REQUIRED_IF_FOUND
  artifact_digest: REQUIRED_IF_READABLE
  draft_status: REQUIRED_IF_DECLARED
  normative_status: REQUIRED_IF_VERIFIED
  adoption_evidence: OPTIONAL
  implementation_status: REQUIRED_IF_VERIFIED
  dependencies: []
  inputs: []
  outputs: []
  normative_terms: []
  state_machines: []
  schemas: []
  invariants: []
  tests:
    specified: []
    executed: []
    results: []
  open_issues: []
  acceptance_gates: []
  evidence_refs: []
  last_verified_revision: UNKNOWN
  verification_timestamp: UNKNOWN
  unknown_fields: []
```

規則：

1. フィールド値は実ファイル、権限あるレジストリ、または検証可能な証拠から取得する。
2. 未取得・未確認の値は `UNKNOWN` または明示的な未確認状態とする。
3. ファイル名、ディレクトリ名、STEP番号から採択状態や規範権限を推定しない。
4. ハッシュ値は対象バイト列の同一性を示すものであり、内容の正しさ・完全性・採択を単独で証明しない。
5. 記載が存在しないことと、規範上その要件が存在しないことを同一視しない。
6. 宣言された依存関係と、監査により確認された依存関係を区別する。
7. インベントリの各値は、出所・取得方法・検証状態を追跡可能にする。

## 7. 状態と権限の解決

監査では、少なくとも次の区分を分離する。

| 区分     | 判定対象                     | 単独では証明しないもの      |
| ------ | ------------------------ | ---------------- |
| 存在     | アーティファクトを取得できるか          | 採択、正当性           |
| 同一性    | 対象ダイジェストが一致するか           | 意味的妥当性           |
| 構文適合   | スキーマ等に適合するか              | 規範適合             |
| 規範採択   | 権限ある採択根拠があるか             | 実装適合             |
| 実装検証   | 対象実装が契約を満たすか             | 全体受入             |
| 受入     | 権限ある受入判定があるか             | Freeze           |
| Freeze | Freeze条件が満たされ、権限ある裁定があるか | 将来の不変性や外部副作用の不存在 |

`PROPOSED`、`NOT_ADOPTED`、`NOT_VERIFIED` などの値は、その契約で定義された意味に従って解釈する。状態語が異なる場合、名称だけで同等性を仮定せず、状態対応表と根拠を作成する。

## 8. 依存グラフ監査

依存辺は、少なくとも次の種類に分類する。

```
NORMATIVE
DATA
AUTHORITY
EVIDENCE
RUNTIME
TEST
ACCEPTANCE
```

各辺には以下を持たせる。

```
dependency_edge:
  source_contract: REQUIRED
  target_contract: REQUIRED
  dependency_type: REQUIRED
  source_evidence: REQUIRED
  declared_or_observed: REQUIRED
  verification_status: REQUIRED
  affected_gates: []
  unresolved_reason: OPTIONAL
```

### 8.1 検証規則

- 依存先の存在、バージョン、採択状態、対象範囲を確認する。
- 存在しない依存先や解決不能な参照を記録する。
- 依存グラフの循環を検出し、辺の意味と循環の影響を分類する。
- 循環が存在するだけで直ちに欠陥と断定しない。ただし、評価順序や相互前提を解決できない場合は該当ゲートをブロックする。
- DAG であることだけで依存閉包の正しさを証明しない。
- グラフのトポロジカル順序を規範の優先順位として使用しない。
- 依存関係が欠落している場合、監査者が黙って追加せず、候補辺と根拠を分けて記録する。

## 9. Cross-STEP 規範整合性マトリクス

各契約について、少なくとも次の観点を比較する。

| 比較軸  | 確認内容                                          |
| ---- | --------------------------------------------- |
| 用語   | 同じ用語が同じ意味・範囲で使われているか                          |
| 状態   | 状態名、遷移、終端性、再開条件が矛盾しないか                        |
| スキーマ | 必須項目、識別子、バージョン、欠落時の処理が整合するか                   |
| 権限   | 提案・承認・採択・実行・Commit の権限が混同されていないか              |
| ポリシー | バージョン、適用範囲、競合解決規則が明示されているか                    |
| 時間   | 有効期間、失効、期限、時刻源、順序が整合するか                       |
| 完全性  | ダイジェスト、署名、鍵、信頼根、失効の意味が整合するか                   |
| エラー  | `FAIL`、`INDETERMINATE`、`UNKNOWN`、拒否が混同されていないか |
| 再実行  | 冪等性、重複、再試行、未知の副作用への対応が整合するか                   |
| 証拠   | 参照、保持、検証、失効、監査追跡が整合するか                        |
| 受入   | 局所受入、全体受入、Commit、Freeze の条件が分離されているか          |
| 復旧   | ロールバック、補償、再照合、履歴改変禁止が整合するか                    |

結果は `PASS`、`FAIL`、`INDETERMINATE`、`NOT_APPLICABLE` のいずれかで記録し、適用根拠と証拠参照を必須とする。監査未実施を `PASS` としてはならない。

## 10. 規範競合のライフサイクル

競合処理は次の順序に従う。

```
DETECT
  → REGISTER
  → DEFINE_SCOPE
  → ASSESS_IMPACT
  → IDENTIFY_AUTHORITY
  → ADJUDICATE
  → PROPOSE_NORMATIVE_CHANGE
  → VALIDATE_CHANGE
  → REVALIDATE_DEPENDENTS
  → RECORD_DISPOSITION
```

### 10.1 競合登録レコード

```
conflict:
  conflict_id: REQUIRED
  affected_contracts: REQUIRED
  conflicting_clauses: REQUIRED
  conflict_type: REQUIRED
  applicability_scope: REQUIRED
  impact_assessment: REQUIRED
  authority_basis: REQUIRED
  adjudication_status: REQUIRED
  decision_evidence: []
  proposed_resolution: OPTIONAL
  dependent_revalidation: []
  residual_risk: UNKNOWN
```

### 10.2 裁定規則

1. 「新しい方」「詳細な方」「多数の契約に記載された方」を自動的に優先しない。
2. 規範上の優先順位は、権限ある採択済みの規則から解決する。
3. 優先規則が存在しない、またはその権限が確認できない場合は `INDETERMINATE` とする。
4. Material Conflict が未解決の場合、影響を受けるゲートは `BLOCKED` とする。
5. 競合解消案は提案として記録し、採択済みの規範と混同しない。
6. 変更が採択された場合、依存先・参照元・テスト・証拠・受入ゲートへの影響を再検証する。
7. 監査報告への記載だけで、競合が解決したとはみなさない。
8. 過去の Decision や Canonical History を、競合解消を理由として遡及改変しない。

## 11. 未解決事項の分類と閉包判定

未解決事項は、件数だけでなく、影響範囲と依存関係によって評価する。

| 分類                  | 例                 | 基本的な扱い                        |
| ------------------- | ----------------- | ----------------------------- |
| 規範権限                | 採択者・優先規則が不明       | 該当する規範判定をブロック                 |
| Canonical Integrity | 履歴の欠損・改変可能性が未解決   | 影響する整合性ゲートをブロック               |
| 必須不変条件              | 必須不変条件の充足が未証明     | 該当受入ゲートをブロック                  |
| 証拠                  | 根拠・ダイジェスト・検証記録が欠落 | `INDETERMINATE` または `BLOCKED` |
| スキーマ                | 必須項目やバージョン解決が不明   | 影響する適合性検証をブロック                |
| 依存関係                | 依存先や影響範囲が不明       | 依存閉包を未確定とする                   |
| 実装                  | 契約に対応する実装が未確認     | 実装適合を未検証とする                   |
| 運用条件                | RTO/RPO 等の必要値が未確定 | 関連する運用受入を未判定とする               |

優先度、重大度、許容リスク、閾値は、権限あるポリシーに定義がある場合にのみ使用する。定義がなければ数値を創作せず、`UNKNOWN` とする。

未解決事項の閉包は、次を区別して記録する。

- `RESOLVED`: 根拠付きで解決済み
- `ACCEPTED_WITH_AUTHORITY`: 権限ある手続きで残留リスクが受容済み
- `DEFERRED`: 明示的な保留。閉包済みではない
- `REJECTED`: 提案または解決案が却下された
- `BLOCKED`: 前提不足または競合により進行不能
- `INDETERMINATE`: 証拠不足等により判定不能

リスク受容は必須要件の充足や不変条件の証明の代替ではない。適用可能な採択済みポリシーが許容する場合に限り、残留リスクの受容を扱う。

## 12. 閉包メトリクス

Closure Report には、確認できた範囲で次の指標を含める。

```
closure_metrics:
  expected_contract_count: UNKNOWN
  discovered_contract_count: UNKNOWN
  readable_contract_count: UNKNOWN
  digest_verified_count: UNKNOWN
  adoption_verified_count: UNKNOWN
  implementation_verified_count: UNKNOWN
  dependency_edge_count: UNKNOWN
  unresolved_dependency_count: UNKNOWN
  detected_conflict_count: UNKNOWN
  unresolved_material_conflict_count: UNKNOWN
  open_issue_count: UNKNOWN
  blocked_gate_count: UNKNOWN
  indeterminate_gate_count: UNKNOWN
  executed_test_count: UNKNOWN
  passed_test_count: UNKNOWN
  failed_test_count: UNKNOWN
```

集計値には対象集合、取得時点、集計方法、証拠参照を付与する。

- `expected_contract_count` は権限ある対象範囲から確定する。STEP番号の連続性だけで期待数を決めない。
- `discovered_contract_count` は実際に発見した契約から算出する。
- 未発見を不存在とみなさない。
- 不明値をゼロに置換しない。
- テスト仕様数と実行済みテスト数を混同しない。
- 合格率やカバレッジ率を算出する場合、分母の定義と対象範囲を固定する。
- 数値の集計が可能でも、規範上の閉包を自動的に証明したことにはならない。

## 13. リポジトリ監査プロトコル

最初のリポジトリ監査は読み取り専用で実施する。

### 13.1 手順

1. 対象リポジトリ、ブランチ、コミット、作業ツリー状態を確認する。
2. 契約群の実ファイル一覧を取得する。
3. 各ファイルの内容、バージョン、ダイジェスト、参照先を確認する。
4. 宣言された採択状態と、その状態を裏付ける権限ある証拠を別々に確認する。
5. 依存関係・規範用語・状態機械・スキーマ・ゲートを抽出する。
6. インベントリ、依存グラフ、整合性マトリクス、競合台帳を構築する。
7. 未解決事項と影響範囲を確定する。
8. 必要な検証コマンド・テストを計画する。
9. 監査結果を Closure Report に集約する。
10. 証拠に基づいて次の工程への移行可否を裁定する。

### 13.2 変更禁止

監査段階では、契約ファイル、実装、テスト、レジストリ、Canonical History を変更しない。修正が必要と判明した場合、変更案・理由・影響範囲を別途提案し、必要な承認を得る。

実際のリポジトリが未確認の間、パス、ダイジェスト、コミット、テスト結果を推定値で埋めない。コマンドを提案しただけで実行済みとは記録しない。

## 14. STEP-200 Global Acceptance への集約

STEP-200 の全体受入準備状況は、STEP-218 の報告だけで確定させず、対象契約に規定された条件と実証証拠から評価する。

少なくとも次のゲートを個別に評価する。

1. 対象範囲の完全性が検証済みである。
2. 必須契約の規範採択状態が確認済みである。
3. 必須依存関係が解決済みである。
4. Material Conflict が未解決のまま残っていない。
5. 必須不変条件の検証証拠が存在する。
6. 必要な実装・テスト検証が実行され、結果が確認済みである。
7. 権限・ポリシー・証拠・状態遷移が相互に整合している。
8. 未解決事項が規範上許容される手続きで処理されている。
9. 受入権限と受入対象範囲が明示されている。
10. 全体受入を認める権限ある決定が存在する。

この一覧は監査の最低限の確認軸であり、STEP-200 の正式なゲートを置き換えるものではない。正式なゲートとの不一致があれば、その不一致自体を競合または欠落として登録する。

`GLOBAL_ACCEPTANCE_READINESS: READY` とするには、適用される必須ゲートが根拠付きで充足されている必要がある。`READY` は受入決定そのものではない。

## 15. 契約追加の停止・継続判定

STEP-218 は、契約追加を続けるか、リポジトリ監査・実装検証へ移るかを決定するゲートである。

| 判定                                   | 条件                                        | 次の行動                  |
| ------------------------------------ | ----------------------------------------- | --------------------- |
| `CONTINUE_CONTRACT_DRAFTING`         | 証拠により独立した規範上の欠落が特定され、既存契約の補正では閉包できない      | 欠落範囲に限定して契約案を作成       |
| `STOP_DRAFTING_AUDIT_REQUIRED`       | 既存契約の実体・採択・依存関係が未確認                       | 新規契約追加を止め、読み取り専用監査を実施 |
| `STOP_DRAFTING_IMPLEMENTATION_AUDIT` | 規範上の必須欠落が見つからず、次の課題が実装・テストの未検証である         | 実装適合性とテスト証拠を検証        |
| `CLOSURE_BLOCKED`                    | Material Conflict、必須権限の欠落、または必須ゲートの未充足がある | 影響範囲を限定し、必要な裁定・是正を要求  |
| `CLOSURE_INDETERMINATE`              | 必要な対象・証拠を確認できず、閉包可否を決定できない                | 不足証拠を特定し、再監査を要求       |

新規契約の作成は、確認済みの規範上の欠落に対する対応であって、未監査状態を解消するための代用品ではない。

現時点ではリポジトリ監査も Cross-STEP 検証も実施済みとは確認できないため、契約追加を自動継続する根拠はない。一方、規範閉包を証明する根拠もない。したがって、現時点での推奨は `STOP_DRAFTING_AUDIT_REQUIRED` であり、これはプロジェクト完了の宣言ではない。

## 16. 閉包状態機械

```
INVENTORY_PENDING
  → INVENTORY_IN_PROGRESS
  → INVENTORY_COMPLETE
  → DEPENDENCY_AUDIT_PENDING
  → CONFLICT_AUDIT_PENDING
  → CLOSURE_BLOCKED
     | CLOSURE_INDETERMINATE
     | CLOSURE_READY_FOR_IMPLEMENTATION_AUDIT
     | CLOSURE_READY_FOR_ACCEPTANCE_REVIEW
     | CLOSURE_REJECTED
```

状態の意味：

- `INVENTORY_COMPLETE`: 対象範囲に対するインベントリが、定義済みの確認基準を満たした。規範閉包を意味しない。
- `CLOSURE_READY_FOR_IMPLEMENTATION_AUDIT`: 規範・依存関係の監査に基づき、実装監査へ移行できる。実装適合を意味しない。
- `CLOSURE_READY_FOR_ACCEPTANCE_REVIEW`: 必要な受入証拠が揃ったことが確認され、権限ある受入審査に進める。受入済みを意味しない。
- `CLOSURE_BLOCKED`: 必須条件が未充足で、該当工程へ移行できない。
- `CLOSURE_INDETERMINATE`: 証拠不足等により判定できない。
- `CLOSURE_REJECTED`: 適用規範に照らして、提示された閉包結果が不適合として却下された。

状態遷移には、遷移元・遷移先・実行主体・判定根拠・証拠参照・対象バージョンを記録する。状態の変更だけで過去の監査記録を上書きしてはならない。

## 17. 不変条件 STI-218

| ID         | 不変条件                                     |
| ---------- | ---------------------------------------- |
| STI-218-01 | インベントリ値には追跡可能な出所が必要である。                  |
| STI-218-02 | 未確認値を確定値として扱わない。                         |
| STI-218-03 | ファイル存在を規範採択の証拠にしない。                      |
| STI-218-04 | ダイジェスト一致を意味的妥当性の証拠にしない。                  |
| STI-218-05 | テスト仕様とテスト実行記録を分離する。                      |
| STI-218-06 | テスト合格と受入決定を分離する。                         |
| STI-218-07 | 依存宣言と検証済み依存関係を分離する。                      |
| STI-218-08 | 依存順序から規範優先順位を推定しない。                      |
| STI-218-09 | 規範競合を暗黙に解消しない。                           |
| STI-218-10 | Material Conflict の影響ゲートを未解決のまま通過させない。   |
| STI-218-11 | 未定義の重大度・閾値を創作しない。                        |
| STI-218-12 | 未発見と不存在を同一視しない。                          |
| STI-218-13 | 不明値をゼロとして集計しない。                          |
| STI-218-14 | 必須不変条件の未証明を合格として扱わない。                    |
| STI-218-15 | 監査中の変更を禁止する。                             |
| STI-218-16 | 競合裁定に権限根拠を要求する。                          |
| STI-218-17 | 採択済み変更の影響先を再検証する。                        |
| STI-218-18 | Closure Report を閉包そのものの証明とみなさない。         |
| STI-218-19 | Global Acceptance と Freeze を独立した判定として扱う。 |
| STI-218-20 | 規範上の欠落が実証されない限り、新規 STEP を自動生成しない。        |

## 18. 検証テスト ST-218

以下はテスト仕様案であり、実行結果ではない。

| ID        | 検証対象                    | 期待結果             |
| --------- | ----------------------- | ---------------- |
| ST-218-01 | 未発見契約の扱い                | 不存在ではなく未確認として記録  |
| ST-218-02 | 未確認の採択状態                | 採択済みに昇格しない       |
| ST-218-03 | ダイジェスト一致                | 意味的妥当性を自動合格にしない  |
| ST-218-04 | 未実行テスト                  | 実行済み件数に含めない      |
| ST-218-05 | 依存先の欠落                  | 依存未解決として記録       |
| ST-218-06 | 依存循環                    | 検出し、影響を分類する      |
| ST-218-07 | 依存順序と権限                 | 順序から優先権限を推定しない   |
| ST-218-08 | 用語定義の競合                 | 競合台帳へ登録          |
| ST-218-09 | 状態機械の不整合                | 影響ゲートを未合格とする     |
| ST-218-10 | スキーマのバージョン不明            | 判定不能として扱う        |
| ST-218-11 | 権限根拠の欠落                 | 裁定を承認済みと扱わない     |
| ST-218-12 | Material Conflict の残存   | 該当ゲートをブロック       |
| ST-218-13 | 未定義の閾値                  | 推測値を設定しない        |
| ST-218-14 | 未解決事項の件数                | 未確認件数をゼロにしない     |
| ST-218-15 | 監査中の修正要求                | 変更と監査を分離         |
| ST-218-16 | 採択済み変更                  | 依存先の再検証を要求       |
| ST-218-17 | Closure Report の存在      | 閉包済みへ自動遷移しない     |
| ST-218-18 | Global Acceptance の準備完了 | 受入決定を自動発行しない     |
| ST-218-19 | 受入済み状態                  | Freeze を自動認可しない  |
| ST-218-20 | 規範上の欠落が未確認              | 新規 STEP を自動作成しない |

## 19. 未解決事項 OI-218

以下は本契約の実証前に確認が必要な事項であり、実リポジトリで発見済みの欠陥を意味しない。

| ID        | 未解決事項                                 |
| --------- | ------------------------------------- |
| OI-218-01 | 対象契約の完全な実ファイル一覧                       |
| OI-218-02 | 各契約の実バージョンとダイジェスト                     |
| OI-218-03 | 各契約の正式な採択根拠                           |
| OI-218-04 | 規範レジストリの実体と権限                         |
| OI-218-05 | STEP間の正式な依存宣言                         |
| OI-218-06 | 依存グラフの実測結果                            |
| OI-218-07 | 用語・状態・スキーマの競合の有無                      |
| OI-218-08 | 権限・ポリシーの競合の有無                         |
| OI-218-09 | 必須不変条件の横断検証結果                         |
| OI-218-10 | テスト仕様と実行済みテストの対応関係                    |
| OI-218-11 | 未解決事項の完全な一覧                           |
| OI-218-12 | 未解決事項とゲートの依存関係                        |
| OI-218-13 | STEP-200 の正式な全体受入条件                   |
| OI-218-14 | STEP-217 の Acceptance Grant と既存契約の整合性 |
| OI-218-15 | RTO/RPO 等の運用値の定義状況                    |
| OI-218-16 | 変更・再検証・監査証拠の保持規則                      |
| OI-218-17 | Closure Report の正式な採択・承認主体            |
| OI-218-18 | 実装と規範契約の対応関係                          |
| OI-218-19 | リポジトリ監査に必要なアクセス・実行環境                  |
| OI-218-20 | 契約追加を停止できると判断するための実証結果                |

各事項の状態は監査後に更新する。推測で `RESOLVED` にしてはならない。

## 20. 受入ゲート AG-218

| ID        | ゲート               | 合格条件                          |
| --------- | ----------------- | ----------------------------- |
| AG-218-01 | 対象範囲              | 対象集合と除外理由が根拠付きで確定             |
| AG-218-02 | インベントリ            | 対象アーティファクトの確認状況が記録済み          |
| AG-218-03 | 同一性               | 必要なダイジェストが検証済み                |
| AG-218-04 | 採択                | 必須契約の規範権限が確認済み                |
| AG-218-05 | 依存関係              | 必須依存辺が検証済み                    |
| AG-218-06 | 循環                | 検出された循環の影響が裁定済み               |
| AG-218-07 | 用語                | Material な定義競合が未解決でない         |
| AG-218-08 | 状態                | 必須状態遷移の整合性が確認済み               |
| AG-218-09 | スキーマ              | 必須スキーマ間の整合性が確認済み              |
| AG-218-10 | 権限                | 必須操作の権限境界が確認済み                |
| AG-218-11 | ポリシー              | 必須ポリシーの選択規則が確認済み              |
| AG-218-12 | 完全性               | 必須の証拠・完全性条件が確認済み              |
| AG-218-13 | Canonical History | 履歴の不変性・Commit 境界が整合           |
| AG-218-14 | 再実行               | 冪等性・復旧・再照合条件が整合               |
| AG-218-15 | 不変条件              | 必須不変条件に検証証拠が存在                |
| AG-218-16 | テスト               | 必要なテストの実行結果が検証済み              |
| AG-218-17 | 未解決事項             | 必須事項が規範上許容される形で処理済み           |
| AG-218-18 | 全体受入              | STEP-200 の正式なゲートとの対応が確認済み     |
| AG-218-19 | 監査証跡              | Closure Report の根拠と再現可能性が確認済み |
| AG-218-20 | 工程移行              | 次工程への移行判断が権限と証拠に基づく           |

`AG-218-01..20` は提案されたゲートである。STEP-200 を含む既存契約の正式な受入条件を上書きしない。必須ゲートが未実行・未確認なら、そのゲートを合格扱いにしてはならない。

## 21. 提案アーティファクト構成

```
contracts/
└── step-218/
    ├── canonical_history_governance_normative_closure_contract.md
    ├── contract_inventory.schema.json
    ├── normative_registry_inventory.schema.json
    ├── dependency_graph.schema.json
    ├── cross_step_consistency_matrix.schema.json
    ├── normative_conflict_record.schema.json
    ├── open_issue_closure_record.schema.json
    ├── closure_report.schema.json
    ├── closure_acceptance_gates.yaml
    ├── invariant_catalog.yaml
    ├── test_plan.yaml
    └── evidence/
        └── README.md
```

これは提案ディレクトリ構成であり、ファイルを作成した、既存リポジトリに適合する、またはスキーマ検証済みであるという意味ではない。

## 22. 最終裁定と次の行動

```
STEP_218_DECISION:
  DRAFT_STATUS: DRAFT_COMPLETE
  NORMATIVE_STATUS: PROPOSED
  ADOPTION_STATUS: NOT_ADOPTED

  INVENTORY_STATUS: NOT_EXECUTED
  DEPENDENCY_CLOSURE: NOT_ASSESSED
  CONFLICT_CLOSURE: NOT_ASSESSED
  OPEN_ISSUE_CLOSURE: NOT_ASSESSED
  CROSS_STEP_CONFORMANCE: NOT_EXECUTED

  CONTRACT_DRAFTING:
    RECOMMENDATION: STOP_PENDING_REPOSITORY_AUDIT

  NEXT_PHASE:
    NAME: READ_ONLY_REPOSITORY_INVENTORY_AND_CROSS_STEP_AUDIT
    STATUS: NOT_STARTED

  GLOBAL_ACCEPTANCE: NOT_ASSESSED
  CANONICAL_MUTATION: NONE
  FREEZE_STATUS: NOT_AUTHORIZED
```

STEP-218 を、この契約シリーズの最後の予定済み草案作成ステップとします。 ただし、これは規範閉包・実装完成・受入完了を意味しません。

次に実施すべきことは、新しい STEP の追加ではなく、実リポジトリに対する読み取り専用インベントリと横断監査です。その結果に基づき、次のどちらかを判断します。

- 規範上の欠落が実証された場合に限り、対象を限定して追加契約または既存契約の改訂を提案する。
- 規範上の必須欠落が確認されなければ、STEP番号の追加を止め、実装・テスト・受入証拠の検証へ移行する。

現時点で確認できるのは、STEP-218 の契約草案を提示したことまでです。実ファイルの確認、テスト実行、採択、受入、Freeze は未実施です。