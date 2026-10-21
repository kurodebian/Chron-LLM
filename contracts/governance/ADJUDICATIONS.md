# Governance Adjudications — 裁定記録

RECORDED: 2026-10-21 (Asia/Tokyo)
RECORD_STATUS: RECORDED_USER_ADJUDICATION
  — ユーザーの裁定表明（2026-10-21、~/.hermes/pastes/paste_5_145121.txt,
    sha256 88c086e07a25f8979ccb88f829ec748a64b52b540a9b1c7a815b26dca3571a58）を
    記録したもの。これ自体はどの契約も採択しないし、凍結層への変更を認可しない。
  — 凍結層（Authority.lean 等）や契約本文に実質的に波及する適用は、各自の独立の
    採択裁定を必要とする（VERIFICATION_IS_NOT_AUTHORIZATION /
    AUTHORIZATION_IS_NOT_COMMIT）。

## 裁定一覧

D1 — ファイリング可否: RESOLVED (2026-10-21)
  裁定: ファイリング移行を承認。STEP-190 / STEP-191 / NCCI-218 を
  contracts/governance/ へ NOT_ADOPTED ドラフトとして物理 filing した（本フェーズで実行）。
  効果: 追跡可能性の確立のみ。採択効果なし。

D2 — checkpoint 足場（STEP-187/188）: RESOLVED (2026-10-21)
  裁定: 凍結 Lean 層（v2.8.0-C）への変更は行わず、高位の契約レベル（STEP-190/191）におけるスキーマ定義としてのみ分離採用する（DEFERRED_TO_CONTRACT_LEVEL）。
  理由: 凍結層の決定論的意味論を汚染せず、ガバナンス契約の仕様として先行定義するため。

D3 — half-open [a,b) 境界慣習: RESOLVED (2026-10-21)
  裁定: 半開区間 [a, b) および gapless 連結モデルを正式に採用する（RESOLVED_ACCEPTED）。
  理由: 境界値エラーを構造的に防ぎ、凍結層の sequence 意味論と完全に整合するため。

D4 — STEP-192 進行可否: RESOLVED — HOLD (2026-10-21)
  裁定: 進行停止を継続。187..191 系列の filing と D1..D6 裁定確定を最優先。
  STEP-192 ドラフト着手は、基礎契約群の filing 完了と D2/D3 裁定まで保留。

D5 — 失効建模の方針: RESOLVED (2026-10-21)
  裁定: 候補A 採用 — 正準 governance event（凍結親和）。
  方向: 独立 Trust 台帳を新設せず、凍結済みの正準イベントチェーン
  （SerializationContext / AuthorityRegistry）へ組み込み、
  AuthorityRegistry.valid の拡張方向で失効・期限を建模する。
  理由（記録）: 二重の信頼ルート・同期ズレの回避、決定論的保証の維持。
  適用条件: Authority.lean / 凍結 spec への実質変更は独立の採択裁定が必要
  （FROZEN 層の性質上、変更は凍結解除または拡張契約の採択を要する）。
  関連ギャップ: T-191-B（凍結層に時刻・期限・失効の足場ゼロ）。

D6 — Admission Record / 拒否記録の保存先: RESOLVED (2026-10-21)
  裁定: 既定で Canonical History 外（専用監査ログ / 付加的な別ストレージ）。
  理由（記録）: Canonical History は合意済み確定イベントの gapless 順序の聖域。
  拒否要求・不正試行のメタデータを混入させない。
  関連: OI-191-15/16、T-191-D（凍結層は正準追記経路1本、Audit Store 未定義）。
  留意: D5 候補A 採用時、失効・例外認可の governance event 自体は
  正準 Commit Authority を経て Canonical History に commit される
  （拒否「試行」記録 ≠ 認可された governance イベント。両者は区別される）。

## 未決のまま残るもの

- STEP-187/188/189 の全文確定と filing（全文はセッション DB にのみ存在）
- 凍結層拡張（AuthorityRegistry.valid の time/expiry 拡張）の採択可否 — D5 は方針裁定であり、凍結層変更そのものの認可ではない。
