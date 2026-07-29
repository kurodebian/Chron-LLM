# Chron-LLM Kernel Specification R2.1 (FREEZE)

- **Status:** FROZEN
- **Authority:** Single Source of Truth

## 0. Meta Protocols & Execution Guarantees (前提不変条件)

本仕様に基づくすべての実装・実行環境は、以下のメタ不変条件を厳格に保証しなければならない。

- **Atomic Lock Acquisition (一括排他ロック原則)**  
  ロック取得はオール・オア・ナッシング（All-or-Nothing）で行われる。対象ノード群の一部でもロック不可の場合、いかなるロックも保持せず、即座に全体を取得失敗として処理（`INV_NODE_LOCKED`）する。
- **Clock Isolation (仮クロックの完全隠蔽)**  
  `PREPARE` 段階で内部採番される Tentative Clock は、実行中トランザクション内部のローカル計算に限定される。`COMMIT` 完了まで WorldHead および外部観測系（Observability）から一切不可視であり、システムクロックに欠番（Hole）を発生させない。
- **Configurable Timeout (決定論的タイムアウト)**  
  `PREPARING` または `APPLYING` 状態の滞留時間上限 `TX_TIMEOUT` の既定値は 3,000ms とする。本数値はカーネル設定（Config）経由でのみ調整可能であり、超過時は決定論的に `ABORTING` 遷移を誘発する。

## 1. Core Constitution & Authority Separation (Layer 1: 憲法と権威分離)

### 1.1 Canonical vs Non-Canonical
- **Canonical (権威層):** LISP AST、Write-Ahead Log (WAL)、因果グラフ（Worldline DAG）。カーネルの `COMMIT` イベント経由でのみ更新される不可変（Append-only）真実。
- **Non-Canonical / Derived (非権威層):** ベクトル DB、近傍検索インデックス、キャッシュ。Canonical から決定論的に 100% 再生成可能であり、単方向追従のみが許される。

### 1.2 Core Event Taxonomy
すべての状態変化は Event として扱われる。`COMMIT_CORRECTION` は本層（Layer 1）で第一級イベント（First-class Event）として定義され、Layer 4 のカーネルエンジンで処理される。

- `FeedbackIntent` / `CorrectionIntent`: 失敗評価や訂正要求の非同期入力。
- `CorrectionCandidate`: 非権威層に置かれる未検証の修正案。
- `VALIDATED_CORRECTION_FACT`: Validation 層を通過した不変事象ファクト。
- `COMMIT_CORRECTION`: 決定論的かつ不変に Canonical 記憶を更新する最終権威イベント。

## 2. S-expr Canonical Form Specification (Layer 2: データ形式と正規化規則)

`CorrectionCandidate` 内の動的修正は、Validation 前に必ず本形式へ決定論的に正規化される。

### 2.1 Modification Radius (変更半径制限)
1 回の `COMMIT_CORRECTION` が変更可能な範囲は、「指定された 1 つの標的ノード (`target-node`) およびその直接の子ノード（Depth=1）」 に限定される。広域修正は暗号的チェーンで連結された複数の独立 Correction Event に分解されなければならない。

### 2.2 Depth Flattening Rules ($N \le 6$)
S 式の最大木深さは $N \le 6$ と定義される。深さ $D \ge 6$ となる部分木 $S_{sub}$ は正規化器により切り出され、単体ノード `(node :id <NodeRefID> :body S_sub)` に平坦化（Flattening）の上、元位置は `(ref <NodeRefID>)` に置換される。

### 2.3 Standard 5-tuple Node Form
すべての正規化済み S 式は以下の 5-tuple で表現される。

```lisp
(correction-node
  :id        "<node-id>"                  ; [UUID/Hash] ノード識別子
  :target    "<target-canonical-id>"      ; [Ref] 標的 Canonical ノード ID
  :op        <operation-type>             ; [Symbol] :REWRITE | :INSERT-AFTER | :DEPRECATE | :ATTACH-GUARD
  :ast-delta (:before-hash "<sha256>"     ; [Fact] 修正前状態ハッシュ
              :after-ast    (<s-expr>))   ; [Canonical S-expr] 修正後正規化S式 (Depth <= 6)
  :bindings  ((<sym_1> . <type_1>) ...)   ; [Environment] 新規宣言型環境
)

```

## 3. Validation Guard & PolicyRouter Boundary (Layer 3: 事実評価と判断委譲)

### 3.1 Validation 5 大 Invariants (ファクト評価ルール)

Validation 層は副作用ゼロで以下のファクト判定のみを行い、レポート（`ValidationReport`）を出力する。「却下・適用」の判断は行わない。

| Invariant ID | 名称 | 事実判定基準 |
| --- | --- | --- |
| `INV_CAUSAL_CYCLE` | 因果グラフ DAG 性 | 修正適用により Worldline DAG に閉環（Loop）が生じるか否か。 |
| `INV_REGRESSION_FAILURE` | 回帰テスト影響 | ゴールデンテスト群に対する破壊数 (`break_count`) および深刻度スコア。 |
| `INV_AST_TOO_DEEP` | 構造・型閉包性 | AST 深さ $N > 6$ の有無、および型環境に未登録の `unbound_symbols` リスト。 |
| `INV_CONTINUITY_BROKEN` | 一貫性判定 | 標的ノードの消滅判定、および LamportClock の順序性。 |
| `INV_INSUFFICIENT_AUTHORITY` | 権威多要素検証 | Source == HUMAN 署名の有無、および SupervisorScore / ExecutionCount。 |

### 3.2 PolicyRouter の責務境界 (Boundary Rule)

* **Validation (Fact Generator):** 「何が起きているか（テスト破壊数 = 2, 深さ = 4, 未解決シンボル = []）」という純粋ファクトのみを提示する。
* **PolicyRouter (Decision Maker):** Validation が吐いたファクトと、現在のシステム/World 設定（Config）を照合し、「昇格を認めて Kernel へ `COMMIT_CORRECTION` を送るか」「Reject するか」の政策的判断を一手に担う。

## 4. Kernel State Machine Delta (Layer 4: 実行エンジン差分)

`06-kernel-state-machine.spec` に対する 2 Phase Commit (2PC) 補足仕様。

```
[ROUTING]
   │ (VALIDATED_CORRECTION_FACT)
   ▼
[PREPARING_CORRECTION] ─── (Atomic Lock 取得 + WAL PREPARE fsync)
   │ (PREPARE_OK)
   ▼
[APPLYING_CORRECTION]  ─── (In-Memory AST/DAG 変更 + WAL COMMIT fsync)
   │ (COMMIT_OK)
   ▼
[IDLE]                 ─── (Clock 昇格 + WorldHead 更新 + Lock 解除)

```

> **※ 異常系処理:** `PREPARING` / `APPLYING` 中の異常発生時は即座に `[ABORTING_CORRECTION]` へ遷移し、In-Memory 破棄・WAL ABORT fsync を実行して `[IDLE]` へ復帰する。

### 4.1 2PC 実行ステップと Clock 昇格

1. **Prepare Phase:** 対象ノード群を一括排他ロック。仮クロック $Clock_{tentative} = Clock_{kernel} + 1$ を設定し、`PREPARE_CORRECTION` を WAL へ書き込み fsync。
2. **Commit Phase:** In-Memory Canonical AST / 因果グラフを変更。`COMMIT_CORRECTION` を WAL へ書き込み fsync。
3. **Completion:** $Clock_{kernel} = Clock_{tentative}$ へ正規昇格し、WorldHead を更新。ロックを解除し、Derived 層へ `ReindexEvent` を発行。

### 4.2 Non-blocking / Immediate Reject

ロック対象ノード（`target-node` + 直接の子 + 新規 `NodeRefID`）のいずれかが占有中の場合、Kernel 内での待ち行列（Queueing）は行わず、即座に `INV_NODE_LOCKED` を返して処理を終了する。

## 5. Fault Tolerance & Recovery Protocol Delta (Layer 5: 復旧プロトコル差分)

`12-recovery.spec` に対するクラッシュロールバック/ロールフォワード補足仕様。

### 5.1 WAL 3-Way Recovery Protocol

再起動時、Kernel は WAL をスキャンし、未解決トランザクション（`tx-id`）を以下の 3 分岐で決定論的に復元・破棄する。

```
                       [スキャンされた未解決 tx-id]
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
【① PREPARE のみ存在】      【② PREPARE + ABORT 存在】  【③ PREPARE + COMMIT 存在】
(COMMIT 前のクラッシュ)     (ABORT 途中のクラッシュ)    (WorldHead 更新前のクラッシュ)
         │                          │                          │
         ▼                          ▼                          ▼
  [ROLLBACK 実行]            [ABORT 完遂]               [ROLLFORWARD 実行]
  WAL に ABORT を追記&fsync。 メモリ残骸を破棄。        変更を再適用し、WorldHead
  In-Memory 変更を破棄。     WAL に COMPLETE 追記。     を進める。

```

### 5.2 Epoch Guard Invalidation (Stale Candidate 排除)

* **Epoch の永続化:** 各 Canonical ノードは S 式ヘッダ内に `epoch_number` を保持する。`COMMIT_CORRECTION` 成功のたびに $N+1$ へ自動カウントアップされ、ノード属性として WAL に永続化される。
* **古コンテキスト自動破棄:** DeferredQueue から取り出された Candidate の `base_epoch` が現在のノードの `current_epoch` より古い場合、Validation 層で不適合と判定され、`DISCARD_STALE_CONTEXT` として即時破棄される。

### 5.3 Bulk Reindex Protocol

Recovery スキャン実行中は個別ノードごとの `ReindexEvent` 発行を一時抑止し、すべてのロールバック/ロールフォワード処理が完了した直後に **1 回の BulkReindexEvent を一括発行** して非同期インデックスを整合させる。

## 6. Dependency Graph & Architectural Constraints (単方向依存グラフ)

本仕様内の依存関係は下図の通り厳格な単方向であり、上位層（Recovery / Kernel）の変更が下位層（Constitution / Normalization）の不変条件を破ることは構造的に禁止される。

```
[ Layer 5: Fault Tolerance & Recovery ]  (3-Way Recovery, Epoch Invalidation, Bulk Reindex)
       │
       ▼ (依存)
[ Layer 4: Execution Engine ]            (2PC State Machine, Immediate Reject, Lock Scope)
       │
       ▼ (依存)
[ Layer 3: Validation & Policy ]         (5 Invariants, PolicyRouter Decision Boundary)
       │
       ▼ (依存)
[ Layer 2: Format & Normalization ]      (S-expr 5-tuple, Depth N <= 6, Modification Radius)
       │
       ▼ (依存)
[ Layer 1: Core Constitution ]           (Canonical / Non-Canonical, Commit-Only, Event Taxonomy)

```
