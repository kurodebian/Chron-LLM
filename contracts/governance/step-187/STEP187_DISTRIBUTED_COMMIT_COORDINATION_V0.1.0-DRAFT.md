# **STEP-187 — Distributed Commit Coordination / Canonical History Replication / Event Ordering / Conflict Resolution / Recovery Consistency Contract**

STEP\_ID: 187  
TITLE: Distributed Commit Coordination / Canonical History Replication / Event Ordering / Conflict Resolution / Recovery Consistency Contract  
VERSION: 0.1.0-draft  
STATUS: DRAFT\_COMPLETE  
NORMATIVE\_STATUS: PROPOSED  
ADOPTION\_STATUS: NOT\_ADOPTED  
IMPLEMENTATION\_STATUS: NOT\_VERIFIED  
TEST\_STATUS: NOT\_EXECUTED  
REPOSITORY\_INSPECTION: NOT\_PERFORMED  
COMMIT\_COORDINATION\_VALIDATION: NOT\_EXECUTED  
EVENT\_ORDERING\_VALIDATION: NOT\_EXECUTED  
REPLICATION\_CONSISTENCY\_VALIDATION: NOT\_EXECUTED  
CONFLICT\_RESOLUTION\_VALIDATION: NOT\_EXECUTED  
RECOVERY\_VALIDATION: NOT\_EXECUTED  
REPLAY\_INTEGRITY\_VALIDATION: NOT\_EXECUTED  
CANONICAL\_MUTATION: NONE  
GLOBAL\_ACCEPTANCE: NOT\_ASSESSED  
FREEZE\_STATUS: NOT\_AUTHORIZED  
TIMEZONE: Asia/Tokyo

## **1\. Purpose**

本契約は、分散環境における Canonical History の Commit、複製、順序付け、競合処理、障害復旧を規定するための提案である。

中心課題は、次の概念を混同せずに扱うことである。

* Canonical History：確定済みの Canonical Event の権威ある系列  
* Commit Authority：Canonical Event を確定する権限  
* Replication：確定済みイベントの複製と伝播  
* Ordering：イベント間の確定順序と因果関係  
* Projection：履歴から導出される状態  
* Recovery：既存の確定履歴を保持したまま、整合した運用状態へ復帰する処理

本契約は、複数ノードが存在することを理由に、Canonical History が自動的に複数存在する構成を認めるものではない。

## **2\. Scope / Non-Goals**

### **2.1 Scope**

1. Canonical Event Identity  
2. Commit Proposal / Validation / Commit  
3. Commit Authority と権限委譲  
4. Event Ordering / Causality  
5. Replication State / Acknowledgment  
6. Concurrent Proposal Conflict  
7. Idempotency / Deduplication  
8. Network Partition / Partial Failure  
9. Recovery Point / History Integrity  
10. Replay / Projection Rebuild  
11. Commit Attestation / Audit Evidence  
12. Canonical History の復旧・切替手続き

### **2.2 Non-Goals**

* 特定の Consensus Algorithm の無条件な採用  
* 分断中もすべてのノードが Commit できるという保証  
* 複数の競合履歴を無条件に一つへ自動統合すること  
* Replication Acknowledgment を Commit の代替とすること  
* Projection や Cache から Canonical Event を推測すること  
* Commit 済みイベントの破壊的な書換え・削除  
* 実装・テスト・リポジトリ検査・実環境検証

## **3\. Normative Language / Canonical Authority**

本 STEP は `PROPOSED` である。以下は採用前の規範案である。

Proposal  
    ↓  
Validation  
    ↓  
Commit Authorization  
    ↓  
Canonical Commit  
    ↓  
Replication  
    ↓  
Projection / Replay

### **3.1 Authority Invariants**

1. Canonical History の確定権限は、明示的に指定された Commit Authority に属する。  
2. Validator、Replica、Projection、Cache、Fleet Manager は、存在するというだけで Commit Authority を得ない。  
3. Commit 前の Proposal は Canonical Truth ではない。  
4. Commit 済みイベントの複製が遅れていることは、イベントの確定を取り消す理由にならない。  
5. Replica のローカル状態を、Canonical History と自動的に同一視してはならない。  
6. 競合が解消されていない Proposal は、規定された裁定が完了するまで Canonical Commit してはならない。  
7. Canonical History の訂正が必要な場合、過去のイベントを破壊的に改変するのではなく、承認された訂正イベントまたは補償イベントを用いる。

### **3.2 Commit の定義**

本契約では、Commit を単なる書込み成功やローカル永続化ではなく、規範上の確定操作として扱う。

具体的な Commit 条件は、Commit Authority、永続化保証、必要な証拠、障害時の判定規則を含む別途固定された Commit Profile によって定義する。

当該 Profile が未確定の場合、次の状態を区別する。

NOT\_SUBMITTED  
SUBMITTED  
VALIDATION\_PENDING  
AUTHORIZATION\_PENDING  
COMMIT\_PENDING  
COMMITTED  
REJECTED  
COMMIT\_STATUS\_UNKNOWN

`COMMIT_STATUS_UNKNOWN` は `COMMITTED` でも `REJECTED` でもない。再試行前に既存の Commit 状態を照合し、重複 Commit を防止する必要がある。

## **4\. Canonical Event Identity / Event Envelope**

### **4.1 Event Envelope**

canonical\_event:  
  event\_id: REQUIRED  
  event\_type: REQUIRED  
  schema\_version: REQUIRED  
  payload\_digest: REQUIRED  
  payload\_ref: REQUIRED  
  proposal\_id: REQUIRED  
  causation\_refs: REQUIRED  
  correlation\_id: REQUIRED  
  authority\_identity: REQUIRED  
  commit\_profile\_id: REQUIRED  
  commit\_sequence: REQUIRED  
  previous\_event\_ref: REQUIRED  
  committed\_at: REQUIRED  
  commit\_evidence\_ref: REQUIRED

この Envelope は提案形式であり、既存 Canonical Event Schema との整合性は未確認である。

### **4.2 Identity Rules**

* `event_id` は、イベントの再配送や再試行によって変化してはならない。  
* 同一 `event_id` に異なる `payload_digest` が対応する場合、正常な重複として処理してはならない。  
* `proposal_id` と `event_id` の意味を区別する。  
* イベントの同一性とイベント内容の等価性を区別する。  
* `correlation_id` は関連する処理群を示すために使い、因果順序の証明として扱わない。  
* Event ID の生成方式、衝突処理、正規化、ダイジェスト計算は別途規範化する。

### **4.3 Event Integrity**

Canonical Event の完全性を確認する際は、少なくとも次を検証対象とする。

1. Envelope の形式  
2. Payload と Digest の一致  
3. Event Identity の一意性  
4. Commit Evidence の真正性  
5. Authority Identity と権限の有効性  
6. Commit Profile の適用可能性  
7. 順序・因果参照の整合性

署名の有効性だけでは、イベントの意味論的な妥当性や Commit の権限を証明できない。

## **5\. Commit Coordination / Authorization**

### **5.1 Commit Lifecycle**

CREATED  
   ↓  
SUBMITTED  
   ↓  
VALIDATING  
   ├── REJECTED  
   └── VALIDATED  
          ↓  
     AUTHORIZATION\_PENDING  
          ├── DENIED  
          └── AUTHORIZED  
                 ↓  
            COMMIT\_PENDING  
                 ├── COMMIT\_FAILED  
                 ├── COMMIT\_STATUS\_UNKNOWN  
                 └── COMMITTED

`COMMIT_FAILED` は、確定が発生していないことを証拠で確認できた場合にのみ用いる。結果が不明な障害を `COMMIT_FAILED` と推定してはならない。

### **5.2 Commit Authorization Contract**

Commit 判定は、少なくとも以下を固定する。

commit\_authorization:  
  proposal\_id: REQUIRED  
  event\_id: REQUIRED  
  payload\_digest: REQUIRED  
  validation\_evidence\_ref: REQUIRED  
  policy\_snapshot\_ref: REQUIRED  
  authority\_identity: REQUIRED  
  authority\_scope: REQUIRED  
  commit\_profile\_id: REQUIRED  
  authorization\_decision: REQUIRED  
  decision\_evidence\_ref: REQUIRED

### **5.3 Authority Rules**

* Validation 成功は Commit Authorization の代替ではない。  
* Authorization 成功は、実際に Commit が確定したことの証明ではない。  
* Replica の応答数だけで Authority を決定してはならない。  
* Commit Authority の切替は、明示的な権限移譲イベントと検証可能な証拠を必要とする。  
* 古い Authority の権限が失効したか不明な場合、競合する Commit を並行して許可してはならない。  
* Commit Authority の権限範囲は、対象 History、イベント種別、Policy、時間・Epoch 等の条件に結び付ける。

### **5.4 Commit Acknowledgment**

以下を独立して扱う。

| 状態 | 意味 |
| ----- | ----- |
| `LOCAL_DURABLE` | ローカルで永続化された |
| `AUTHORITY_ACCEPTED` | Authority が要求を受理した |
| `CANONICAL_COMMITTED` | 規範上の Commit が確定した |
| `REPLICA_RECEIVED` | Replica がイベントを受信した |
| `REPLICA_DURABLE` | Replica がイベントを永続化した |
| `REPLICA_VERIFIED` | Replica の証拠・整合性を検証した |
| `REPLICATION_COMPLETE` | 規定された複製条件を満たした |

これらの状態は互いに同義ではない。Commit 成功の通知は、実際の Commit Evidence に結び付けなければならない。

## **6\. Event Ordering / Causality / Sequence Integrity**

### **6.1 Ordering Model**

本契約では、次の順序概念を区別する。

* `CAUSAL_ORDER`: 先行イベントへの依存関係  
* `COMMIT_ORDER`: Canonical History における確定順序  
* `OBSERVATION_ORDER`: ノードがイベントを観測した順序  
* `DELIVERY_ORDER`: ネットワーク経由でイベントを受信した順序  
* `WALL_CLOCK_ORDER`: 壁時計による時刻順序

CAUSAL\_ORDER ≠ OBSERVATION\_ORDER  
DELIVERY\_ORDER ≠ COMMIT\_ORDER  
WALL\_CLOCK\_ORDER ≠ COMMIT\_ORDER

### **6.2 Ordering Rules**

1. Canonical History の確定順序は、Commit Profile が定義する規則によって決定する。  
2. 壁時計のタイムスタンプだけで Commit 順序を決定してはならない。  
3. `causation_refs` が示す依存イベントは、Commit 前に存在・確定状態・参照整合性を検証する。  
4. 因果依存を持つイベントは、依存条件が満たされるまで確定してはならない。  
5. 因果依存のない Proposal 間の順序決定は、明示された決定規則に従う。  
6. Replica が異なる順序でイベントを受信した場合、Canonical Commit 順序を独自に再定義してはならない。  
7. 同一 Commit Sequence に異なるイベントが割り当てられた場合、整合性異常として扱う。

### **6.3 Sequence Integrity**

sequence\_integrity:  
  history\_id: REQUIRED  
  commit\_profile\_id: REQUIRED  
  sequence\_start: REQUIRED  
  sequence\_end: REQUIRED  
  event\_count: REQUIRED  
  first\_event\_ref: REQUIRED  
  last\_event\_ref: REQUIRED  
  gap\_manifest\_ref: REQUIRED  
  duplicate\_manifest\_ref: REQUIRED  
  verification\_status: REQUIRED

Sequence の欠落・重複・逆転・参照不整合は、それぞれ独立して検出する。検証できない範囲を正常な連続履歴とみなしてはならない。

## **7\. Replication Contract**

### **7.1 Replication State Machine**

NOT\_SENT  
   ↓  
IN\_FLIGHT  
   ↓  
RECEIVED  
   ↓  
INTEGRITY\_CHECKED  
   ↓  
DURABLE  
   ↓  
CANONICAL\_ORDER\_VERIFIED  
   ↓  
REPLICATION\_VERIFIED

例外状態：

DELIVERY\_FAILED  
INTEGRITY\_FAILED  
ORDERING\_CONFLICT  
REPLICATION\_LAGGING  
REPLICATION\_UNKNOWN  
REPLICA\_QUARANTINED

### **7.2 Replication Rules**

* Replication は Canonical Commit の後続処理であり、Commit Authority を自動的に移譲しない。  
* Replica は受信したイベントの Digest、Identity、Commit Evidence、Sequence を検証する。  
* 受信済みでも永続化されていないイベントを、耐久性が確認されたものとして報告してはならない。  
* Replica のローカル書込み成功は、Canonical Commit の証拠にならない。  
* 複製遅延を隠すために、未受信イベントを推測で生成してはならない。  
* Replica の復旧・再同期時は、確定済みイベントと未確定 Proposal を区別する。  
* 複製の失敗・再試行・再送は追跡可能なイベントとして記録する。

### **7.3 Replication Profile**

replication\_profile:  
  profile\_id: REQUIRED  
  source\_history\_id: REQUIRED  
  replica\_set\_ref: REQUIRED  
  durability\_requirement: REQUIRED  
  verification\_requirement: REQUIRED  
  ordering\_requirement: REQUIRED  
  acknowledgment\_requirement: REQUIRED  
  lag\_threshold: REQUIRED  
  failure\_policy: REQUIRED  
  recovery\_policy: REQUIRED

Replica の必要数、耐久性、確認方式、遅延許容値は用途ごとに規範化する。本ドラフトでは具体値を仮定しない。

## **8\. Concurrent Proposal / Conflict Resolution**

### **8.1 Conflict Classification**

| 分類 | 意味 |
| ----- | ----- |
| `NO_CONFLICT` | 規定の判定範囲で競合なし |
| `SAME_ID_SAME_PAYLOAD` | 同一イベントの再送・重複候補 |
| `SAME_ID_DIFFERENT_PAYLOAD` | 同一 ID に異なる内容 |
| `CAUSAL_CONFLICT` | 因果依存と整合しない競合 |
| `STATE_PRECONDITION_CONFLICT` | Commit 前提条件の不一致 |
| `AUTHORITY_CONFLICT` | 権限・Epoch・委譲状態の競合 |
| `SEQUENCE_CONFLICT` | Sequence または順序の競合 |
| `UNRESOLVED_CONFLICT` | 証拠不足または裁定未完了 |

### **8.2 Conflict Rules**

1. 同一 ID・同一 Payload の再送は、Identity と Commit 状態を確認したうえで冪等に処理する。  
2. 同一 ID・異なる Payload は、通常の重複として処理してはならない。  
3. State の事前条件が Commit 時点で成立しない Proposal は、規定の再検証・拒否・裁定経路へ送る。  
4. `last-write-wins`、最新タイムスタンプ、Replica の多数決を暗黙の競合解決規則として使用してはならない。  
5. 競合を自動解決する場合、その規則、入力、結果、適用バージョンを固定し、再現可能にする。  
6. 意味論的裁定が必要な競合は、Commit Authority の前提を満たすまで未確定とする。  
7. Conflict Resolution は元の Proposal とその証拠を消去しない。

### **8.3 Conflict Record**

conflict\_record:  
  conflict\_id: REQUIRED  
  history\_id: REQUIRED  
  proposal\_refs: REQUIRED  
  event\_identity\_refs: REQUIRED  
  conflicting\_preconditions: REQUIRED  
  policy\_snapshot\_ref: REQUIRED  
  detected\_at: REQUIRED  
  classification: REQUIRED  
  resolution\_status: REQUIRED  
  resolution\_evidence\_ref: REQUIRED  
  adjudicator\_ref: REQUIRED

`resolution_evidence_ref` は、解決規則の適用、明示的な裁定、または拒否の根拠を参照する。

## **9\. Idempotency / Deduplication / Retry**

### **9.1 Idempotency Contract**

同一の論理操作を再送した際、再送によって新たな Canonical Event が重複確定しないようにする。

idempotency\_record:  
  idempotency\_key: REQUIRED  
  operation\_scope: REQUIRED  
  proposal\_digest: REQUIRED  
  original\_event\_ref: OPTIONAL  
  original\_commit\_status: REQUIRED  
  first\_seen\_at: REQUIRED  
  last\_seen\_at: REQUIRED

### **9.2 Rules**

* Idempotency Key の有効範囲と保持期間を明示する。  
* Key の一致だけで Payload の一致を推定しない。  
* 同じ Key で異なる Payload が到着した場合、Conflict として処理する。  
* Commit 状態が不明な場合、同一操作を新しい Event ID で再実行する前に照合する。  
* Deduplication の記録を削除する場合、削除後に重複 Commit が起こらないことを別途保証する。  
* Retry は元の要求と関連付け、初回失敗を隠さない。  
* 冪等性は Commit 操作の重複抑止を目的とし、すべての副作用の重複抑止を自動的に保証するものではない。

## **10\. Network Partition / Commit Safety**

### **10.1 Partition Model**

CONNECTED  
DEGRADED  
PARTITIONED  
RECONNECTING  
RECONCILING  
RECOVERY\_VERIFICATION  
OPERATIONAL

この状態モデルは提案である。ネットワーク状態と Canonical Commit の状態は別々に管理する。

### **10.2 Safety Rules**

1. Commit Authority の唯一性または有効な排他性を確認できない場合、競合する Canonical Commit を許可してはならない。  
2. Authority への接続断は、Authority の失効や権限移譲の証明ではない。  
3. ローカル永続化は、Canonical Commit の代替ではない。  
4. Partition 中にオフライン操作を許可する場合、操作範囲、競合可能性、後続の検証・裁定規則を事前定義する。  
5. オフラインで生成された Proposal は、別途承認された Commit 手続きが完了するまで Canonical Event として扱わない。  
6. Commit の成否が不明な場合、確定済みかどうかを照合するまで、同じ論理操作を重複確定させてはならない。  
7. Safety を維持できない場合、対象操作を停止・制限する。

### **10.3 Recovery Reconciliation**

再接続後、少なくとも以下を照合する。

* Canonical History Identity  
* Commit Authority と委譲状態  
* 最終確認済み Commit Sequence  
* Event Identity と Payload Digest  
* Commit Evidence  
* Replication Gaps / Duplicates  
* 未確定 Proposal  
* Conflict Record  
* Idempotency Record  
* Policy / Trust Snapshot

競合が残る場合、単に最新のローカル履歴を採用してはならない。裁定不能な範囲は `RECOVERY_UNRESOLVED` として保持する。

## **11\. Recovery Point / History Integrity**

### **11.1 Recovery Point Manifest**

recovery\_point:  
  recovery\_point\_id: REQUIRED  
  history\_id: REQUIRED  
  commit\_profile\_id: REQUIRED  
  last\_verified\_sequence: REQUIRED  
  last\_verified\_event\_ref: REQUIRED  
  history\_digest: REQUIRED  
  verification\_profile\_ref: REQUIRED  
  replication\_evidence\_ref: REQUIRED  
  unresolved\_gap\_manifest\_ref: REQUIRED  
  created\_at: REQUIRED  
  verification\_status: REQUIRED

Recovery Point は、指定範囲の履歴が特定の検証プロファイルで確認されたことを表す証拠であり、それ以降のイベントが存在しないことや、全 Replica が一致していることを単独で証明しない。

### **11.2 Recovery Rules**

* 復旧開始時に、信頼できる Recovery Point と検証済み履歴範囲を識別する。  
* Recovery Point 以降のイベントは、存在・順序・完全性を検証してから再構築対象に含める。  
* 欠落範囲を推測したイベントで補完してはならない。  
* 復旧元の履歴に矛盾がある場合、矛盾を記録し、裁定なしに履歴を統合しない。  
* 復旧操作自体を監査可能にする。  
* 復旧後の状態再構築が成功しても、それだけで Canonical History の完全性を証明したことにはならない。

### **11.3 Recovery Status**

RECOVERY\_PENDING  
RECOVERY\_IN\_PROGRESS  
RECOVERY\_VERIFIED  
RECOVERY\_PARTIAL  
RECOVERY\_UNRESOLVED  
RECOVERY\_FAILED

`RECOVERY_PARTIAL` は、検証済み範囲と未検証範囲を明確に区別できる場合に限る。未検証範囲を正常と扱ってはならない。

## **12\. Replay / Projection Rebuild**

### **12.1 Replay Contract**

Replay は Canonical History を入力として Projection を再構築する処理であり、履歴そのものを書き換える処理ではない。

Canonical History  
    ↓  
History Verification  
    ↓  
Ordered Event Stream  
    ↓  
Deterministic Replay  
    ↓  
Projection  
    ↓  
Projection Verification

### **12.2 Replay Manifest**

replay\_manifest:  
  replay\_id: REQUIRED  
  history\_id: REQUIRED  
  history\_range: REQUIRED  
  history\_digest: REQUIRED  
  replay\_engine\_identity: REQUIRED  
  replay\_engine\_digest: REQUIRED  
  schema\_registry\_snapshot: REQUIRED  
  policy\_snapshot\_ref: REQUIRED  
  projection\_schema\_version: REQUIRED  
  replay\_profile\_id: REQUIRED  
  output\_digest: REQUIRED

### **12.3 Rules**

1. Replay の入力範囲、Event Order、Schema、実行環境を固定する。  
2. 不明な Event Type や Schema Version を暗黙に無視してはならない。  
3. Projection の差異は、Canonical History の変更ではなく、再構築結果の差異として記録する。  
4. Replay の結果が過去の Projection と一致しない場合、差異の原因が判明するまで同一結果とみなさない。  
5. Replay の成功を、元の Canonical Event の意味論的正当性の証明としない。  
6. Projection の修正・再構築から Canonical History を逆算・改変してはならない。  
7. Replay Engine のバージョン変更による差異は、独立した検証イベントとして扱う。

### **12.4 Projection Status**

PROJECTION\_CURRENT  
PROJECTION\_STALE  
PROJECTION\_REBUILDING  
PROJECTION\_VERIFIED  
PROJECTION\_DIVERGENT  
PROJECTION\_UNVERIFIABLE

Projection が `PROJECTION_DIVERGENT` または `PROJECTION_UNVERIFIABLE` の場合、その Projection に依存する処理は用途別の制限を適用する。

## **13\. Commit Attestation / Audit Evidence**

### **13.1 Commit Evidence Bundle**

commit\_evidence:  
  event\_id: REQUIRED  
  proposal\_digest: REQUIRED  
  validation\_evidence\_ref: REQUIRED  
  authorization\_evidence\_ref: REQUIRED  
  commit\_authority\_identity: REQUIRED  
  commit\_profile\_id: REQUIRED  
  commit\_sequence: REQUIRED  
  previous\_event\_ref: REQUIRED  
  durability\_evidence\_ref: REQUIRED  
  commit\_attestation\_ref: REQUIRED

### **13.2 Evidence Rules**

* Commit Evidence は、Commit 対象と Authority、Sequence、適用 Profile を結び付ける。  
* Attestation は、対象データの Digest と署名者の Identity に結び付ける。  
* 署名の有効性と、Commit 手続きが規範に適合したかどうかを区別する。  
* Evidence Bundle の欠落・改変・参照不能は、明示的に記録する。  
* Commit 後の証拠追加は、追補記録として扱い、既存の証拠を黙って置換しない。  
* 証拠の保管期間・アクセス制御・鍵失効時の再評価規則は別途定義する。

### **13.3 Audit Result**

PASS  
FAIL  
INDETERMINATE  
NOT\_EVALUABLE  
INPUT\_INVALID  
AUDIT\_FAILED

Audit の `PASS` は、対象範囲内の Commit Evidence と履歴整合性が指定プロファイルに適合したことを示す。履歴外の事象や未評価範囲まで保証するものではない。

## **14\. Failure / Recovery Matrix**

| Failure | 必須処理 | 復帰条件 |
| ----- | ----- | ----- |
| Event ID 重複・Payload 不一致 | Conflict として隔離 | Identity と裁定結果の確認 |
| Commit Authority 不明 | Commit を停止 | 権限・Epoch の再検証 |
| Commit 状態不明 | 再送前に状態照合 | Commit 状態の確定 |
| Commit Sequence の競合 | 確定処理を停止 | 正規順序と証拠の確認 |
| Replica の Digest 不一致 | 対象 Replica を隔離 | 証拠を用いた再同期 |
| Replication Lag | 遅延を記録 | Profile の条件を満たす |
| Partition 中の競合 Proposal | 未確定のまま保持 | 再接続後の検証・裁定 |
| Idempotency Record 欠落 | 重複確定リスクを評価 | 安全な照合経路の確立 |
| Recovery Point の不整合 | 復旧を保留 | 信頼できる復旧点の確定 |
| History Gap | 欠落範囲を明示 | 欠落の解決または裁定 |
| Replay の出力差異 | Projection を不一致扱い | 差異の原因特定・再検証 |
| Commit Evidence 欠落 | Audit を未確定化 | 必須証拠の回復・検証 |
| Authority 切替の競合 | 並行 Commit を停止 | 権限移譲の確定 |
| 復旧時の履歴競合 | 自動統合を禁止 | 規範化された裁定 |

失敗からの復旧では、原イベント、原証拠、失敗記録、再試行記録を保持する。復旧処理が成功したことを理由に、初回失敗の存在を削除してはならない。

## **15\. Invariants — `STI-187-01..20`**

全項目 `PROPOSED / NOT_VERIFIED`。

| ID | Invariant |
| ----- | ----- |
| STI-187-01 | Canonical History の確定権限は明示された Commit Authority に限定される。 |
| STI-187-02 | Proposal は Commit 完了前に Canonical Truth とならない。 |
| STI-187-03 | Event Identity と Payload の同一性を別々に検証する。 |
| STI-187-04 | Commit Sequence は規範化された順序規則に従う。 |
| STI-187-05 | 壁時計だけで Canonical Commit 順序を決定しない。 |
| STI-187-06 | 因果依存を満たさないイベントを確定しない。 |
| STI-187-07 | Validation と Commit Authorization を区別する。 |
| STI-187-08 | Authorization と Commit 完了を区別する。 |
| STI-187-09 | Replication と Canonical Commit を区別する。 |
| STI-187-10 | Replica のローカル状態を Canonical History と同一視しない。 |
| STI-187-11 | 同一 ID・異なる Payload を正常な重複として処理しない。 |
| STI-187-12 | Commit 状態が不明な要求を照合前に重複確定しない。 |
| STI-187-13 | 競合をタイムスタンプや多数決だけで暗黙解決しない。 |
| STI-187-14 | Partition 中も Commit Authority の排他性を維持する。 |
| STI-187-15 | 未解決の履歴競合を自動統合しない。 |
| STI-187-16 | Recovery Point と未検証範囲を区別する。 |
| STI-187-17 | Replay / Projection Rebuild は Canonical History を変更しない。 |
| STI-187-18 | Projection の差異を履歴の書換えで解消しない。 |
| STI-187-19 | Commit Evidence は対象イベントと権限・順序を結び付ける。 |
| STI-187-20 | Rollback・Recovery・Replay は過去の確定証拠を破壊しない。 |

## **16\. Test Candidates — `ST-187-01..20`**

全項目 `NOT_EXECUTED`。実行済みの試験ではない。

| ID | Test Candidate | 期待される検証 |
| ----- | ----- | ----- |
| ST-187-01 | Commit Authority を欠く要求 | Commit を拒否する。 |
| ST-187-02 | Validation 成功・Authorization 失敗 | Commit しない。 |
| ST-187-03 | Authorization 成功・Commit 状態不明 | 確定扱いせず状態照合を要求する。 |
| ST-187-04 | 同一 Event ID・異なる Payload | Conflict を検出する。 |
| ST-187-05 | Commit Sequence の重複 | 履歴整合性違反を検出する。 |
| ST-187-06 | 壁時計が逆転したイベント | 規範的 Commit 順序を保持する。 |
| ST-187-07 | 未確定の因果依存先 | 依存条件を満たすまで確定しない。 |
| ST-187-08 | 重複した Replication Delivery | 二重 Commit を発生させない。 |
| ST-187-09 | Replica の Payload 改変 | Digest 不一致を検出する。 |
| ST-187-10 | Replica の未永続化応答 | 耐久性確認済みと扱わない。 |
| ST-187-11 | Partition 中の競合 Commit | Authority の排他性を維持する。 |
| ST-187-12 | Authority 切替中の旧 Authority の要求 | 権限状態を検証し、不正な確定を防ぐ。 |
| ST-187-13 | Idempotency Key 再利用・異なる Payload | Conflict として扱う。 |
| ST-187-14 | Commit 状態不明後の Retry | 重複確定を防ぐ。 |
| ST-187-15 | Recovery Point 後の履歴欠落 | 未検証範囲を検出する。 |
| ST-187-16 | 異なる履歴を持つ Replica の再同期 | 自動統合せず競合を記録する。 |
| ST-187-17 | Replay の結果が過去 Projection と異なる | 差異を独立記録する。 |
| ST-187-18 | Replay から Canonical History への書換え要求 | 書換えを拒否する。 |
| ST-187-19 | Commit Evidence の署名有効・参照欠落 | 完全な適合を認定しない。 |
| ST-187-20 | Recovery 後の原証拠照合 | 既存証拠の保持と追跡可能性を確認する。 |

## **17\. Open Issues — `OI-187-01..20`**

全項目 `OPEN`。

| ID | 未解決事項 |
| ----- | ----- |
| OI-187-01 | Canonical History の物理配置と論理的権威の定義 |
| OI-187-02 | Event ID の生成・衝突処理・保持期間 |
| OI-187-03 | Commit Profile の正式なスキーマと登録先 |
| OI-187-04 | Commit Authority の選出・委譲・失効手続き |
| OI-187-05 | Commit の永続化保証と確定点の定義 |
| OI-187-06 | Commit Sequence の割当てと順序保証方式 |
| OI-187-07 | 因果依存の規範的表現と検証規則 |
| OI-187-08 | 複製の耐久性・Acknowledgment 条件 |
| OI-187-09 | Replica 数・障害許容範囲・復旧条件 |
| OI-187-10 | 同時 Proposal の競合分類と裁定権限 |
| OI-187-11 | Idempotency Key のスコープと保持期間 |
| OI-187-12 | Partition 中の操作クラス別 Commit Policy |
| OI-187-13 | Authority 切替時の旧権限失効の証明方法 |
| OI-187-14 | Recovery Point の信頼根と作成条件 |
| OI-187-15 | 履歴欠落・破損時の修復可能性の判定規則 |
| OI-187-16 | Replay の決定性と Schema 移行時の互換性 |
| OI-187-17 | Projection 差異の分類・裁定・再構築基準 |
| OI-187-18 | Commit Attestation の正規形式と鍵ライフサイクル |
| OI-187-19 | Canonical History のバックアップ・保持・復旧規則 |
| OI-187-20 | STEP-182〜186 および既存 Kernel / History Contract との実際の整合性 |

## **18\. Acceptance Gates — `AG-187-01..20`**

全項目 `NOT_ASSESSED`。

| ID | Acceptance Gate |
| ----- | ----- |
| AG-187-01 | Canonical History と Replica の権威境界が規範化されている。 |
| AG-187-02 | Event Identity と Payload Integrity の規則が固定されている。 |
| AG-187-03 | Commit Lifecycle の全状態と遷移条件が定義されている。 |
| AG-187-04 | Commit Authority の権限・委譲・失効が規範化されている。 |
| AG-187-05 | Commit の確定点と永続化保証が明示されている。 |
| AG-187-06 | Event Ordering と因果依存の規則が固定されている。 |
| AG-187-07 | Commit Sequence の欠落・重複検出が定義されている。 |
| AG-187-08 | Replication の耐久性と確認条件が定義されている。 |
| AG-187-09 | Replica の再同期・隔離・復帰条件が定義されている。 |
| AG-187-10 | Concurrent Proposal の競合分類と裁定規則が定義されている。 |
| AG-187-11 | Idempotency と Retry の安全条件が規範化されている。 |
| AG-187-12 | Partition 中の Commit 安全性が検証可能である。 |
| AG-187-13 | Authority 切替中の二重確定防止が検証可能である。 |
| AG-187-14 | Recovery Point の作成・検証条件が固定されている。 |
| AG-187-15 | History Gap と破損履歴の処理が規範化されている。 |
| AG-187-16 | Replay が Canonical History を変更しないことを検証できる。 |
| AG-187-17 | Projection 差異の記録・裁定・再構築条件が定義されている。 |
| AG-187-18 | Commit Evidence の完全性と検証可能性が定義されている。 |
| AG-187-19 | Recovery / Rollback による証拠の破壊を防止できる。 |
| AG-187-20 | 必須テストと受入証拠が追跡可能である。 |

## **19\. Proposed Artifact Tree**

contracts/  
└── step-187/  
    ├── distributed\_commit\_contract.md  
    ├── canonical\_event.schema.json  
    ├── commit\_authorization.schema.json  
    ├── commit\_evidence.schema.json  
    ├── replication\_profile.schema.json  
    ├── replication\_record.schema.json  
    ├── sequence\_integrity.schema.json  
    ├── conflict\_record.schema.json  
    ├── idempotency\_record.schema.json  
    ├── recovery\_point.schema.json  
    ├── replay\_manifest.schema.json  
    ├── commit\_state\_machine.md  
    ├── event\_ordering\_rules.md  
    ├── replication\_consistency\_rules.md  
    ├── conflict\_resolution\_contract.md  
    ├── partition\_safety\_contract.md  
    ├── recovery\_and\_replay\_contract.md  
    ├── invariants.yaml  
    ├── test\_plan.yaml  
    ├── open\_issues.yaml  
    └── acceptance\_gates.yaml

状態は `PROPOSED`。ファイル作成、既存ファイルとの統合、Schema 検証、テスト実行は行っていない。

## **20\. Dependency Matrix**

| Dependency | 必要な整合性 | 状態 |
| ----- | ----- | ----- |
| STEP-182 | 上流の検証・証拠契約 | 未検証 |
| STEP-183 | 検証結果・信頼境界 | 未検証 |
| STEP-184 | Determinism / Trace / Attestation | 未検証 |
| STEP-185 | Qualification / Certification / Rollback | 未検証 |
| STEP-186 | Fleet / Policy / Revocation / Drift | 未検証 |
| Kernel / History Contract | Commit Authority と History の単一権威 | 規範案のみ |
| Policy Registry | Commit Policy と Version の固定 | 未検証 |
| Trust / Key Lifecycle | Authority・署名・失効の検証 | 未検証 |
| Replication Layer | 永続化・順序・再同期 | 未検証 |
| Replay / Projection | History からの決定的再構築 | 未検証 |
| Audit / Evidence Store | Commit 証拠の保持・参照 | 未検証 |

## **21\. Adjudication / Status**

STEP\_ID: 187  
DRAFT\_STATUS: COMPLETE  
NORMATIVE\_STATUS: PROPOSED  
ADOPTION\_STATUS: NOT\_ADOPTED

REPOSITORY\_INSPECTION: NOT\_PERFORMED  
SCHEMA\_VALIDATION: NOT\_EXECUTED  
IMPLEMENTATION\_STATUS: NOT\_VERIFIED  
TEST\_STATUS: NOT\_EXECUTED

COMMIT\_COORDINATION\_VALIDATION: NOT\_EXECUTED  
EVENT\_ORDERING\_VALIDATION: NOT\_EXECUTED  
REPLICATION\_CONSISTENCY\_VALIDATION: NOT\_EXECUTED  
CONFLICT\_RESOLUTION\_VALIDATION: NOT\_EXECUTED  
RECOVERY\_VALIDATION: NOT\_EXECUTED  
REPLAY\_INTEGRITY\_VALIDATION: NOT\_EXECUTED

INVARIANTS:  
  TOTAL: 20  
  VERIFIED: 0

TEST\_CANDIDATES:  
  TOTAL: 20  
  EXECUTED: 0

OPEN\_ISSUES:  
  TOTAL: 20  
  CLOSED: 0

ACCEPTANCE\_GATES:  
  TOTAL: 20  
  PASSED: 0  
  ASSESSED: 0

CANONICAL\_MUTATION: NONE  
GLOBAL\_ACCEPTANCE: NOT\_ASSESSED  
FREEZE\_STATUS: NOT\_AUTHORIZED

裁定：STEP-187 は契約ドラフトとして完成。規範採用・実装・検証・受入・Freeze は未承認。

この STEP で最も重要な未確定点は、何をもって Commit が不可逆的に確定したと判断するかである。永続化、Authority の承認、必要な複製条件、Commit Evidence の生成を、どの順序・条件で一つの確定手続きに束ねるかは、実装方式を選ぶ前に規範として固定する必要がある。

## **22\. 次 STEP**

STEP-188 — Canonical History Governance / Commit Finality / Authority Transfer / History Correction / Retention and Archival Contract

次段階では、分散 Commit の仕組みを追加するだけでなく、Canonical History の長期的な権威・確定性・訂正・保存を扱う。

予定する対象：

1. Canonical History の唯一性と確定性  
2. Commit Finality と不確定状態の裁定  
3. Commit Authority の移譲・失効・復旧  
4. History Correction / Compensating Event  
5. Canonical History の保持・アーカイブ・移行  
6. 証拠の保持期限と削除条件  
7. 履歴の完全性・連続性・真正性の再検証  
8. 長期保存後の Replay と検証可能性  
9. Canonical History と派生 Projection の分離  
10. 履歴に関する規範変更と既存証拠の扱い

次 STEP でも、履歴の訂正と履歴の改変、複製の一致と権威の一致、保存の完了と検証可能性の維持を、それぞれ独立した概念として扱う。