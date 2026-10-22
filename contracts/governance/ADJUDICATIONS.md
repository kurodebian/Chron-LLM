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

D4 — STEP-192 進行可否: RESOLVED — HOLD → HOLD LIFTED (2026-10-21 同日更新)
  原裁定: 進行停止。保留条件 = 187..191 系列の filing 完了と D1..D6 裁定確定。
  条件充足の確認 (2026-10-21): filing 完了（commits 4d42a10, a01b4db: STEP-187..191,
  NCCI-218 filing 済み）、D1..D6 すべて RESOLVED（D2/D3 は commit 786b407 で解決記録）。
  ユーザーが STEP-192 ドラフト着手フェーズへの移行を宣言（2026-10-21、セッション内メッセージ）。
  留保: E-218-008（organizer 乖離）は D4 の保留条件ではなく、UNRESOLVED のまま残る。
  STEP-192 ドラフトを妨げないが、クリア済みとして記録してはならない
  （ゲートコンポーネント単体テストは EXECUTED_PASS / 本番ゲート再実行は NOT_EXECUTED、
  evidence_ledger_218.json E-218-011 参照）。

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

D7 — OI-192-03 裁定（INDETERMINATE 末尾区間 [k, N) の扱い）: RESOLVED (2026-10-22)
  裁定: 候補C 採用 — 検証後決定ハイブリッド（verify-then-decide）。
    R1 決定論的分類: [k, N) の各レコードを VERIFIED_COMPLETE（フレーミング完全・
       先行レコードとのハッシュ連結 intact・OperationID 一意性と Idempotency Record
       突合一致・§11 監査対応あり）か UNVERIFIED に分類する。
    R2 修復前缀: k から始まる VERIFIED_COMPLETE の連続最長前缀 [k, m) を保持し
       gapless 連鎖へ再接続する。照合イベント自体は D6 に従い監査ログ側
       （Canonical History 外）に記録する。
    R3 以降切り捨て: 最初の UNVERIFIED 以降 [m, N) を切り捨てる。該当操作は
       NOT_COMMITTED とし §9 により同一 OperationID で再試行可。孤児 Intent の
       処理は OI-192-01 に委ねる。
    R4 Receipt 錨: 有効な永続化 Receipt を持つレコードは絶対に切り捨てない
       （Receipt ⇒ COMMITTED 錨）。
    R5 保守フォールバック: 分類が決定論的に不能な場合（監査ログ欠落等）は
       k まで全切り捨てとし、破棄区間のバイト列は外部監査ストレージ（D6）へ
       退避し、無断破棄としない。
    R6 合成禁止: 修復は新規正準レコードを書かない。検証済み既存バイトの
       保持のみ（単一追記経路の前提 T-191-D を維持）。
    連続性規則: UNVERIFIED の後ろに VERIFIED_COMPLETE が続く場合、後者も
       切り捨てる（隙間禁止・D3 gapless）。
  理由（記録）: R1〜R6 はディスク状態 + Idempotency Record + 監査ログの純関数であり
    §10 の決定論保証を満たす。A（全切り捨て）は検証済み完全レコードの破棄と
    Receipt 矛盾のリスクを、B（全区間保持）は §2 公理（INDETERMINATE != COMMITTED）
    違反と履歴純度（D6）侵害のリスクをそれぞれ抱える。C は両者の失敗モードを
    排除する最小の規則集合である。
  適用条件: STEP-192 契約本文への反映は採択裁定（ADOPTION）時に実施する。
    本裁定はドラフト §9 の「採択時に別途裁定する」の該当裁定であり、
    ドラフト本文そのものは変更しない（filing discipline）。
  依存: R1 の検証可能性の範囲は OI-192-02（Receipt 決定論的再生成に必要な
    永続化情報の最小集合）の確定に依存する。OI-192-02 の早期確定を事実上要求する。
  対象: STEP192_COMMIT_ADMISSION_ATOMICITY_v0.1.0-draft.md §9 L128-131 / §13 OI-192-03。

D8 — OI-192-02 裁定（Receipt 決定論的再生成に必要な永続化情報の最小集合）: RESOLVED (2026-10-22)
  裁定: 案A 採用 — 時刻なし Receipt 同一性。
    M1 Receipt 同一性は永続化状態の純関数:
       Receipt = H(OperationID, 正準イベント識別子, 位置 n, prev-hash 連鎖状態,
                   AuthorityRef/CausalID)。wall-clock 時刻は Receipt 同一性に参加しない。
    M2 §6 の「発行時刻」は論理的 commit 点 (n, 正準イベントハッシュ) と再定義する
       （§10 の線形化点=永続化確認点と整合）。観測 wall-clock 時刻は D6 に従い
       監査ログ側のみに記録され、Receipt 検証に入力されない。
    M3 永続化証明は構造的: フレーミング intact + prev-hash 連鎖 intact + [0,n) gapless。
       個別の fsync 証明書は要求しない（CP4/CP5 を生き残れないため証明として無意味）。
    M4 最小永続化集合 P_min:
       P1 Intent レコード（正準書込み前に永続化・§5 WAL）: OperationID、対象操作の
          正準表現ハッシュ、AuthorityRef/CausalID、意図の時刻境界（宣言レベル・
          §12 により D5 凍結層拡張まで実行時強制なし）。
       P2 正準イベント レコード: 位置 n、内容、prev-hash バインド。
       P3 Idempotency Record（正準書込み前に永続化）: OperationID → 試行状態
          {INTENT_FIXED / WRITE_STARTED / PERSISTENCE_CONFIRMED / RECEIPT_ISSUED}、
          Intent へのポインタ。
       P4 AuthorityRef が正準チェーン内で解決可能であること（D5）。
    M5 再生成と再発行の境界: 再生成（バイト同一の再計算）は再構築であり発行では
       ないため許可（CP5・§9「Receipt 再生成」）。再発行（内容の異なる Receipt）は
       禁止であり §6 の障害イベントとして照合（§9）へ回付し監査記録する。
       これにより OI-192-04 の境界が導出される。
    M6 署名を使用する場合、Receipt 内容ハッシュに対する決定論的署名
       （RFC 6979 型）でなければならない。無署名（検証=再生成一致）も可。
  理由（記録）: §6 L88「発行時刻」の wall-clock 解釈は CP6 での再生成と両立せず、
    同一 OperationID に異なる Receipt 2つという §6 障害を構造的に誘発する。
    M1〜M6 は Receipt 検証をディスク状態の純関数とし、§6 一意性・§6 検証決定論・
    §10 決定論保証（再起動回数・時刻非依存）を運用規律ではなく構造で保証する。
  適用条件: §6 L88「発行時刻」の語義改訂は採択裁定（ADOPTION）時にドラフト本文へ
    反映する。本裁定時点ではドラフト本文を変更しない（filing discipline）。
  帰結: D7 R1 の VERIFIED_COMPLETE 判定は P1+P2+P3 の intact 性 + §11 監査対応として
    決定可能。D7 R4 の錨検証は「保存済み Receipt == 再計算 Receipt」の一致判定。
    OI-192-01 は分類側が導出可能（P1 のみ・P2 なし・OperationID 正準列に皆無 →
    孤児 Intent = NOT_COMMITTED・§9）。孤児 Intent の保持期間と除去規則は D9 で解決。
  対象: STEP192_COMMIT_ADMISSION_ATOMICITY_v0.1.0-draft.md §6 / §7 CP5 / §9 / §13 OI-192-02。

D9 — OI-192-01 裁定（孤児 Intent の保持期間と除去規則）: RESOLVED (2026-10-22)
  裁定: 案A 採用 — 照合トリガー型転送。
    G1 保持下限: 孤児 Intent（D8 分類: P1 のみ・P2 なし・OperationID 正準列に皆無）は
       RECONCILIATION 完了まで Intent ストアに保持する。孤児 Intent は §9 突合の
       証拠そのものであり、照合完了前の除去は §9 突合を不能にするため禁止。
    G2 除去トリガー: 除去のトリガーは照合イベントのみ。照合が D8 分類を適用し、
       Idempotency Record の状態を ORPHAN_RESOLVED へ遷移した後に限り除去可。
       wall-clock 経過による GC は禁止（T-191-B により実行時強制が凍結層に存在せず、
       時刻依存の復旧状態は §10 決定論保証に違反）。凍結層拡張（OI-192-06/D5）後も、
       時間 GC は照合トリガーを代替できない。
    G3 転送先: 除去は削除ではなく転送 — 孤児 Intent レコードは監査ストア（D6・
       Canonical History 外）へ転送され、ライブ Intent ストアから除去する。
       §7 CP2「正準履歴に現れない MUST」と整合（孤児 Intent は正準列に書かれない）。
       転送は冪等: 照合の再実行は同一結果を産し、二重転送・隙間を産まない。
    G4 §4 一意性との整合: §4 L71「同一 OperationID の Intent が2つ存在しては
       ならない」は「ライブ（未解決）Intent が高々1つ」と解釈する。同一 OperationID
       での再試行（§9 L127）は ORPHAN_RESOLVED 到達後にのみ許可。これにより
       §4 と §9 の正面衝突を解消。
    G5 保持期間の二段構造: 強制下限 = 照合完了まで（本裁定）。監査ストア側の
       保持期間・完全性契約は本裁定では発明せず OI-192-04（STEP-191 OI-191-15/16
       と統合）に委譲する。
  理由（記録）: 案B（固定期間）は T-191-B で強制不能かつ §10 違反かつ任意の T の
    発明。案C（永久保持）はライブ孤児 Intent が同一 OperationID 再試行を恒久ブロック
    する読みを許し §9 L127 と矛盾。案A は除去をディスク状態 + 照合の純関数とし、
    §4・§7 CP2・§9・§10 のすべてと整合。
  適用条件: §4 L71・§7 CP2 の語義反映（ライブ Intent 解釈・転送語義）は採択裁定
    （ADOPTION）時にドラフト本文へ反映する。本裁定時点ではドラフト本文を変更しない。
  帰結: STEP-192 の孤児 Intent 処理は分類（D8）→ 保持（G1）→ 遷移（G2）→ 転送（G3）
    → 再試行許可（G4）の決定論的パイプラインとして閉じる。残存依存は監査側保持
    （G5→OI-192-04）のみ。
  対象: STEP192_COMMIT_ADMISSION_ATOMICITY_v0.1.0-draft.md §4 / §7 CP2 / §9 / §13 OI-192-01。

## 未決のまま残るもの

- STEP-187/188/189 の全文確定と filing（全文はセッション DB にのみ存在）
- 凍結層拡張（AuthorityRegistry.valid の time/expiry 拡張）の採択可否 — D5 は方針裁定であり、凍結層変更そのものの認可ではない。
- STEP-192 OI-192-04（監査ログ スキーマ・保持・完全性契約 — 再生成/再発行の境界は D8 M5、孤児 Intent の監査側保持は D9 G5 により委譲先として確定、STEP-191 OI-191-15/16 と統合）/ OI-192-05（直列化可能性の検証方法）/ OI-192-06（intent_expiry と D5 凍結層拡張の接続）。OI-192-01 は D9、OI-192-02 は D8、OI-192-03 は D7 で解決済み。
