# STEP-192 L1 参照モデル + 検証ハーネス (ADOPTION フェーズ)

D11 裁定 (OI-192-05) が定めた二層検証構成の実装物。stdlib-only (Python 3.12,
依存パッケージなし; 検証用 venv は `python -m venv` による隔離のみ)。

## 構成

- `l1_reference_model.py` — 契約レベル参照モデル L1
  - §5 単一正典追記パス (frame CANON_REC_V1, position, prev_hash 連鎖)
  - §7 クラッシュポイント CP1..CP6 / §8 永続性分岐 (CP4 survives/lost)
  - D9 G1..G4: reconcile 起動型 orphan Intent パイプライン
    (retain -> resolve -> transfer、壁時計 GC 禁止、transfer は audit-idempotent)
  - D10 I4/I5/I6: 独立 audit ハッシュチェーン、DISCARDED_INTERVAL 逐語退避
    (NO_SILENT_DISCARD 1:1)、admission-before-intent、audit 書込失敗 -> HOLD
  - D12 X2: 位置ベース revocation (governance event として同一経路で commit;
    wall-clock は妥当性判定に不使用; NO_RETROACTIVE_INVALIDATION)
  - §11 INVALID_COMMIT 双方向 / §12 凍結層 (Authority.lean / WAL.lean) 非変更
- `test_l1_validation_harness.py` — INV-01..INV-08 検査 + 二層スイープ
  - Tier 1 網羅: ops 1..3 x CP1..CP6 x crash_index x audit 失敗部分集合
    (サイズ<=2) x CP4 永続性 x 再起動 0..2 (1602 ケース)
  - Tier 2 property-fuzz: 固定シード (19205) 300 ケース
  - INV-H1: シード独立性 — `run_sweep.py --seed N` の results_digest が
    PYTHONHASHSEED / sweep 順序に依存しない (サブプロセス検査込み)
- `run_sweep.py` — 決定論的スイープ実行 + results_digest 出力

## 実行

    python -m pytest test_l1_validation_harness.py -q        # 138 passed
    python run_sweep.py --seed 0                              # results_digest

## 現在の検証結果 (2026-10-23 実行)

- Tier 1 網羅 1602 ケース: violations_total = 0
- Tier 2 fuzz 300 ケース: violations_total = 0
- INV-H1: seed 0 / 12345 で results_digest 一致
  `94ab2a5a66cd1ba3e332ddc4ed494379829b4eb027bac0e34c342fbee6003fd1`

## 規律 (裁定 D11 / D12 より、そのまま有効)

- VERIFICATION_IS_NOT_AUTHORIZATION
- TEST_PASS != ACCEPTANCE、ACCEPTANCE != GLOBAL_ACCEPTANCE
- モデル検証 PASS は実装検証ではない (LINEARIZATION_VALIDATION の
  NOT_EXECUTED フィールドは adoption 裁定が更新するまでそのまま)
- 反例 (counterexample) は発見時にモデルを静かに修正せず、ガバナンス裁定へ
  ルートする。本ハーネスで検査が変更された場合 (例: INV-07 の attempted-prefix
  比較、INV-03 の audit/fault 冪等性規則) は、モデルの決定論的整合性を
  保つための局所修正であり、反例の握り潰しではない — 変更履歴はコミットで
  追跡可能。
- 凍結層 read-only: Authority.lean / WAL.lean は本ディレクトリのいかなる
  実行物からも参照のみ、非変更 (no unfreezing authorized, D5 適用条件)。
