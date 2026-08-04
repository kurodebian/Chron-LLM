# Chron-LLM WAL (Write-Ahead Logging) Engine Specification

- **Version:** 2.0.0
- **Status:** Draft / Implementation Phase
- **Target Subsystem:** Phase-D Commit Kernel & Recovery Engine (`chron.kernel.wal`)

---

## 1. 概要 (Overview)

Chron-LLM の 2PC (Two-Phase Commit) トランザクション永続化およびクラッシュ復旧を担保する WAL (Write-Ahead Logging) エンジンの物理フォーマットと動作モデルを定義する。
本エンジンは SBCL ネイティブの POSIX I/O (`fdatasync`, `O_APPEND`) を直接叩くことで、ゼロコピーに近い最小オーバーヘッドでのアトミック追記と Fail-Stop 型クラッシュリカバリを実現する。

---

## 2. 物理レコードフォーマット (Physical Record Format)

すべての WAL レコードは **48バイト固定長ヘッダー**、**可変長ペイロード**、**4バイト CRC32C**、および **アライメントパディング** で構成される。

### 2.1 ヘッダーレイアウト (48 Bytes Fixed Header)

メモリおよび CPU 非整列アクセスコストを排除するため、すべての 8 バイト境界フィールドは 8 の倍数オフセットにアライメントされる。

| オフセット | サイズ | フィールド名 | 型 | 説明 |
|---|---|---|---|---|
| `0..3` | 4B | Magic | `uint32_le` | 固定識別子 `'CHWA'` (`0x43485741`) |
| `4..5` | 2B | Version | `uint16_le` | フォーマットバージョン (`0x0201`) |
| `6` | 1B | Record Type | `uint8` | レコード種別 (1: PREPARE, 2: COMMIT, 3: ABORT, 4: CHECKPOINT, 5: RECOVERY_COMPLETE) |
| `7` | 1B | Flags | `uint8` | 予約領域 (現状 `0x00`) |
| `8..15` | 8B | Tx-ID | `uint64_le` | トランザクション ID (64bit 整数) |
| `16..23` | 8B | Tentative Clock | `uint64_le` | 論理クロック / タグ |
| `24..31` | 8B | Target Hash High | `uint64_le` | 128bit ノードハッシュ上位 64bit |
| `32..39` | 8B | Target Hash Low | `uint64_le` | 128bit ノードハッシュ下位 64bit |
| `40..43` | 4B | Payload Length | `uint32_le` | 後続する可変長ペイロードのバイト数 ($L$) |
| `44..47` | 4B | Reserved | `uint32_le` | 将来拡張用パディング (`0x00000000`) |

### 2.2 レコード全体のアライメントと CRC32C

1. **Header**: Offset `0`〜`47` (48 bytes)
2. **Payload**: Offset `48`〜`48+L-1` ($L$ bytes)
3. **CRC32C**: Offset `48+L`〜`48+L+3` (4 bytes, Header + Payload に対するチェックサム)
4. **Padding**: 0〜7 バイトのパディングを挿入し、レコード全体の総バイト数が **8 の倍数** になるよう調整する。

---

## 3. レコード種別 (Record Types)

- `0x01` **PREPARE**: トランザクションの準備状態を書き込む。UTF-8 エンコードされた S 式ペイロードを保持。
- `0x02` **COMMIT**: トランザクションのコミットを確定。
- `0x03` **ABORT**: トランザクションの中断を確定。
- `0x04` **CHECKPOINT**: システムのスナップショット起点を示すマーカー。
- `0x05` **RECOVERY_COMPLETE**: リカバリ処理完了を示すマーカー。

---

## 4. スキャン & 検証パイプライン (Scan & Validation)

ファイル読み込み（またはリカバリ）時は、段階的検証により不完全な書き込み（Torn Writes / Partial Writes）を検出し、検出時点で即座にスキャンをストップ（Fail-Stop）する。

1. **Header Boundary Check**: 残りバイト数が 48 バイト未満の場合は即座に終了。
2. **Magic & Version Match**: `Magic == 0x43485741` かつ `Version == 0x0201` であることを検証。
3. **Payload Bounds Check**: `Payload Length` が最大許容長 (`*max-payload-bytes*`, デフォルト 64KB) を超えていないか検証。
4. **Record Length Availability**: ファイルの残りバイト数が `48 + Payload Length + 4 + Padding` 以上存在するか検証。
5. **CRC32C Checksum Validation**: ヘッダー + ペイロード部分に対する CRC32C 計算値が、レコード末尾の 4 バイト CRC32C 値と一致するか検証。

---

## 5. 3-Way リカバリプロトコル (3-Way Recovery Protocol)

1. **File Truncation**: スキャンによって特定された最後の正常な完全レコード位置 (`valid-offset`) 以降の不完全データを POSIX `ftruncate` で直ちに物理切り捨て。
2. **Transaction State Classification**:
   - **PREPARED のみ** (COMMIT も ABORT も無し) $\rightarrow$ **ROLLBACK** (WAL に `ABORT` レコードを追記・同期)。
   - **COMMITTED 存在** $\rightarrow$ **ROLLFORWARD** (S 式ペイロードを安全にリードし、State Machine に適用)。
   - **ABORTED 存在** $\rightarrow$ **IGNORE** (無視)。
3. **Recovery Completion**: リカバリ完了後、WAL ファイルに `RECOVERY_COMPLETE` レコードを発行し `fdatasync` を強制。

---

## 6. セキュリティと堅牢性 (Security & Error Handling)

- **Safe Read Policy**: S 式リード時、`*read-eval*` を `nil` に厳格束縛し、`read-from-string` による不審なコード実行攻撃を防ぐ。
- **Return Values over Signaled Errors**: ファイル書き込み・アペンド処理において `error` コンディションの送出を回避し、`values` による二値ファクト返却（例: `(values nil :payload-too-large)`) に統一する。
- **POSIX Flags**: 通常書込用 FD は `O_CREAT | O_WRONLY | O_APPEND` (Mode `#o644`) でオープンする。