# Chron-LLM R2.1-D Commit Kernel Specification (FREEZE)

- **Version:** R2.1.0-FREEZE
- **Target Component:** Phase-D Commit Kernel (`chron.kernel.wal` / `chron.kernel.state-machine`)
- **Status:** APPROVED & FROZEN
- **Upstream Spec:** `Chron-LLM_R2.0-D_Commit_Kernel_Constitution_Spec.md`

---

## 1. フリーズ宣言 (Freeze Declaration)

本仕様書は、Chron-LLM R2.1 における Commit Kernel の物理バイナリレイアウト、クラッシュリカバリプロトコル、およびトランザクション整合性ルールを不可変（Frozen）として定義する。
本仕様に反する変更はメジャーバージョンアップ（R3.0）を除き認められない。

---

## 2. 不変条件 (Core Invariants)

1. **Strict 48-Byte Header Alignment**: WAL ヘッダーは 48 バイト固定とし、すべての 64bit フィールドは 8 バイト境界に配置する。CPUの非整列アクセスを一切発生させない。
2. **Fail-Stop Verification**: レコードの破損、切り欠き（Torn Write）、CRC不一致を検出した時点で直ちにスキャンを中断し、それ以降のデータをTruncateする。
3. **3-Way Recovery Protocol**:
   - `PREPARED` のみ $\rightarrow$ `ABORT` レコード追記によるロールバック
   - `COMMITTED` 存在 $\rightarrow$ State Machine へのロールフォワード適用
   - `ABORTED` 存在 $\rightarrow$ 無効としてスキップ
4. **Non-Signaling Fact Return**: 正常系・異常系ともに Lisp `error` コンディションの送出を禁止し、多値ファクト `(values result status-tag)` で結果を返却する。
5. **Safe Reader Boundaries**: ペイロード（S式）デコード時は `*read-eval*` を `nil` に固定し、任意のコード実行攻撃を物理遮断する。

---

## 3. 物理フォーマット仕様 (Physical Binary Spec)

+-----------------------------------------------------------------------+
| Header (48 Bytes)                                                     |
| [0..3] Magic ('CHWA')  [4..5] Version (0x0201)  [6] Type  [7] Flags   |
| [8..15] TxID           [16..23] Clock                                 |
| [24..31] Target Hash High  [32..39] Target Hash Low                   |
| [40..43] Payload Len   [44..47] Reserved                              |
+-----------------------------------------------------------------------+
| Payload (L Bytes)                                                     |
+-----------------------------------------------------------------------+
| CRC32C (4 Bytes)                                                      |
+-----------------------------------------------------------------------+
| Padding (0..7 Bytes to ensure total record size is 8-byte aligned)    |
+-----------------------------------------------------------------------+


---

## 4. Kernel State Machine & ロック境界

1. **排他制御**: `sb-thread:mutex` によるカーネル一括排他ロック。2PC（Prepare/Commit/Abort）処理中は状態遷移のアトミック性を保証する。
2. **2PC 状態遷移**:
   - `IDLE` $\rightarrow$ `PREPARED` (`write-prepare-record` & `fdatasync`)
   - `PREPARED` $\rightarrow$ `COMMITTED` (`write-commit-record` & `fdatasync` & State Machine Apply)
   - `PREPARED` $\rightarrow$ `ABORTED` (`write-abort-record` & `fdatasync`)

---

## 5. 構成ファイル一覧

- `runtime/phase-d/wal.lisp`: WAL物理エンコード/デコード/リカバリエンジン
- `runtime/phase-d/state-machine.lisp`: 2PC メモリ状態管理およびスレッド同期
- `chron-r2-0-d.asd`: Phase-D パッケージ構成定義