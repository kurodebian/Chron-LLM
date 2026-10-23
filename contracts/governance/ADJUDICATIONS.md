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

D10 — OI-192-04 裁定（監査ログ スキーマ・保持・完全性契約 — OI-191-15/16 統合）: RESOLVED (2026-10-22)
  裁定: 案A1 / 案B2+B3 / 案C1 / 案D-a の組合せ採用。
    I1 完全性（案A1）: 監査ストアは独立の追記専用ハッシュチェーンを持つ。各監査レコードは
       AuditEventID、監査列番号 s（監査専用 namespace。正準 sequence の流用禁止 —
       正準 position を監査列の位置として扱わない）、prev-audit-hash、内容ハッシュ
       （sha256 commitment、Crypto.lean 契約レベル、凍結層変更不要）を持つ。
       監査列の gap / prev-hash 不一致は AUDIT_INTEGRITY_FAULT として監査列自体に記録し、
       照合（監査経路の復旧、STEP-191 §13）を起動する。監査チェーンの破損は正準列の
       妥当性を無効化しない（STEP-192 §11 / STEP-191 §12 の分離検証）。
       正準スナップショット・アンカーレコード（正準 prefix ハッシュの写し。監査ストア側にのみ
       記録し正準列へ書かない）は MAY。外部タイムスタンピング（A2）・正準 governance event による
       checkpoint commit（A3）は強化オプション（プロファイル承認制、STEP-190 L216 方向）として
       留保し、本裁定では MUST にしない。
    I2 保持下限（案B2・証拠依存）: 障害記録（RECEIPT_REISSUE_FAULT・INVALID_COMMIT・
       AUDIT_INTEGRITY_FAULT・照合イベント・DISCARDED_INTERVAL）は対応する正準区間が
       検証可能である限り保持。孤児 Intent 転送レコード（D9 G3）は該当 OperationID の
       試行系譜（Idempotency Record 系譜）が照合可能である限り保持。拒否 Admission 記録は
       STEP-191 §9.2（失敗記録の消去禁止）により同じ証拠依存で保持。
       wall-clock による保持期限・GC は禁止（D9 G2、T-191-B、§10 時刻非依存）。
    I3 容量圧迫（案B3・二段アーカイブ）: ライブ監査ストア + 監査アーカイブ。圧迫トリガーは
       監査列番号の構造的条件であり時刻で定義しない。転送対象は閉合済みセグメント
       （セグメント内の全照合が ORPHAN_RESOLVED 等に到達済み）のみ。転送は冪等
       （D9 G3 の鏡像、二重転送・隙間を産まない）。転送時にアーカイブ側で prev-audit-hash
       連鎖の再検証 MUST。ライブストアからの除去はアーカイブ側再検証成功後にのみ許可
       （verify-then-remove、D7 verify-then-decide と同型）。アーカイブからの真の破棄は
       本裁定では発明せず、将来の独立ガバナンス裁定へ委譲する。
    I4 フォールバック表現（案C1）: DISCARDED_INTERVAL 監査レコード — reason code
       （Closed Vocabulary 方向、OI-191-19 統合）、破棄区間の論理記述（正準列上の想定範囲と
       Intent/Idempotency 参照）、破棄バイト列の逐語保存（framing メタデータ付き）、
       破棄バイト列の sha256 commitment、破棄を承認した照合イベントへの参照、破棄時点の
       チェーン状態の写し（検証済み position k と prev-hash）。破棄バイト列自体が監査チェーンに
       参加し、後日 intact なチェーン下で再検証可能。不変条件 NO_SILENT_DISCARD: 正準末尾から
       失われたバイトは DISCARDED_INTERVAL レコードと 1:1 対応（STEP-191 §8.2 / §7 CP2 の鏡像）。
       破棄区間の正準列への自動復帰は行わない（復帰は新しい照合裁定を要する — D7 R6 合成禁止と整合）。
    I5 監査保存障害（案D-a・OI-191-15/16 統合）: 監査記録は Admission に対して MUST、
       Commit Finality に対しては NOT MUST。監査書込み失敗 → 新しい Admission Decision は HOLD
       （STEP-191 §13「保留・拒否」・§9.2 の人間裁定経路と接続）。永続化確認済みの commit は
       影響を受けわない（§11「監査ログ側の欠落は正準列の妥当性を無効化しない」）。欠落は
       AUDIT_GAP として監査列に追記記録し、監査経路復旧後の照合で補充（追記で埋め、遡及改変しない）。
       保存関係（OI-191-15）: 物理分離 + 参照単方向（監査→正準のみ。position n とイベントハッシュの
       写しを内容として持つ。正準レコードは監査参照を持たない — 履歴の純度 D6）。
       監査書込みと正準書込みの 2 フェーズコミットは導入しない（単一正準追記経路 T-191-D 維持）。
       順序規則: admission-before-intent（Admission 決定の監査レコードは Intent 固定前に永続化）、
       receipt-after-record（Commit 結果の監査レコードは Receipt 発行後遅延なく。欠落は欠陥記録）。
  理由（記録）: I1〜I5 は監査完全性の検証を監査ストアのバイト列の純関数とし（D8 M1 と同型）、
    §11 の非対称性（監査欠落 ≠ 正準無効化）、履歴の純度（D6）、§10 決定論保証（時刻非依存）を
    構造で保証する。A2/A3 は外部時刻依存・正準混入を持ち込み D6/OI-192-06 への前倒し依存を
    生む。B4（固定期間）は D9 案B と同一の失敗モード（T-191-B 強制不能・§10 違反・任意の T の
    発明）。C2（ダイジェストのみ）は D7 R5 の「退避・無断破棄禁止」を空洞化。D-b は監査ストアの
    可用性を正準 Finality の必須条件とし §11 と正面衝突。D-c は監査必須性を空洞化する。
  適用条件: STEP-192 §11/§13・STEP-191 OI-191-15/16 への語義反映（監査チェーン・DISCARDED_INTERVAL・
    HOLD 方針）は採択裁定（ADOPTION）時にドラフト本文へ反映する。本裁定時点ではドラフト本文を
    変更しない（filing discipline）。
  帰結: D9 G5 の委譲先が閉じる。D8 M5 障害イベント・D7 R5 破棄バイト列退避・D9 G3 冪等転送の
    受け皿が単一の監査契約（I1〜I5）として統一される。STEP-192 の OI-192-01/02/03/04 は
    すべて解決済み。残存 OI は OI-192-05（直列化可能性の検証方法）と OI-192-06
    （intent_expiry と D5 凍結層拡張の接続）のみ。
  裁定表明: 2026-10-22、セッション内裁定フォーム（4 項目すべて推奨案で採択）。
    検討文書（repo 外）: ~/design-192/STEP192_OI192-04_ANALYSIS.md。
  対象: STEP192_COMMIT_ADMISSION_ATOMICITY_v0.1.0-draft.md §11 / §13 OI-192-04 /
    STEP191_DECISION_ENFORCEMENT_v0.1.0-draft.md OI-191-15 / OI-191-16。

D11 — OI-192-05 裁定（直列化可能性の検証方法）: RESOLVED (2026-10-22)
  裁定: 案1a / 案2a / 案3a / 案4a の組合せ採用。
  V1 検証対象の定義（発明ではなく §10 + 上流裁定からの導出）: 単一正準追記経路
    （T-191-D）により正準書込み自体は直列化済みであり、並行性は [admission, commit_point)
    領域にのみ存在する。検証は 4 命題として閉じる — S1 順序整合（正準列の gapless 順序は
    永続化確認点の happens-before を保存、§10 線形化点）、S2 復旧不変性（復旧状態は
    ディスク状態の純関数で再起動回数・時刻に依存しない、§10 決定論保証）、S3 一意性
    （同一 OperationID の committed レコード高々 1・Receipt 高々 1、§4・§6・D8 M5・D9 G4）、
    S4 監査非干渉（監査障害・欠落は復旧分類と正準順序を変えない、§11・D10 I5。唯一の例外は
    D7 R5 分類不能フォールバックで、DISCARDED_INTERVAL として明示記録される経路のみ）。
  V2 中核手法（案1a）: 二層構造。層 1 = 網羅モデルチェック（小ケース空間の完全証明:
    Operation 数 ≤3 × Idempotency 状態 {INTENT_FIXED, WRITE_STARTED, PERSISTENCE_CONFIRMED,
    RECEIPT_ISSUED, ORPHAN_RESOLVED} × クラッシュ点 CP1〜CP6 × 再起動 0〜2 × 監査書込み
    成功/失敗 を全 interleaving で網羅）。層 2 = プロパティベース fuzz（Operation 5〜10・
    複合監査障害等大ケース空間の網外探索）。反例はガバナンス裁定へ回付し、モデル側で
    勝手に修正しない。
  V3 不変条件スイート INV-01..08: INV-01 保持済み committed prefix の gapless 性（S1・D3・
    SequenceProof 方向）。INV-02 Receipt 一意性 + 再生成バイト同一（S3・D8 M5）。
    INV-03 復旧の再起動回数・時刻非依存（S2・§10）。INV-04 孤児 Intent パイプライン
    （分類→保持→遷移→転送→再試行、D9 G1〜G4）と転送冪等性（G3）。INV-05 NO_SILENT_DISCARD
    （正準末尾から失われたバイトと DISCARDED_INTERVAL の 1:1 対応、D10 I4）。
    INV-06 永続化確認 happens-before の正準順序保存（S1）。INV-07 監査障害は復旧分類を
    変えない（S4・§11）。INV-08 監査書込み失敗 → 新規 Admission HOLD・committed finality
    無影響（D10 I5）。
  V4 検証対象（案2a）: 契約レベル実行可能参照モデル L1（§3〜§9 + D7/D8/D9/D10 規則の純関数
    実装: commit_attempt / crash(CP1..CP6) / recover(disk_state)）を正本とする。L1 は本番
    実装ではなく、スイートは将来の本番実装に対してそのまま再実行可能に設計する（実装検証は
    独立ゲート。IMPLEMENTATION_STATUS / LINEARIZATION_VALIDATION は NOT_EXECUTED のまま）。
    tests/test_commit_kernel.py（STEP-192 意味論を実装していない mock）は検証対象外
    （差し替えず別資産として残す）。凍結層 grounding: SequenceProof（Replay.lean）と
    fold_determinism / fold_index_correspondence（HistoryFold.lean）は借用 — OI-192-05 が
    検証するのは「復旧照合が fold 入力として同一の正準 prefix を産すこと」。凍結層変更不要。
  V5 Lean 定式化（案3a）: recover の well-definedness 証明（凍結層不変更・新ファイル限定）は
    強化オプションとして留保（D10 の A2/A3 留保と同型。プロファイル承認制）。
  V6 ハープ規律（案4a）: INV-H1 — 検証ハープ自身は PYTHONHASHSEED 非依存（全反復 sorted()
    走査、set/dict 反復順序に依存しない。同一テストを複数 seed で実行し結果のバイト同一を
    確認。乱数系列は明示 seed。回帰コーパスは固定 seed で常時再実行）。stdlib-only を既定と
    し、hypothesis 等の依存追加は独立の工具裁定。organizer.py の決定論（32bbe9d）と
    E-218-008 は証拠トラック分離 — OI-192-05 の受理証拠に合算しない（E-218-008 は
    UNRESOLVED のまま別トラックで追跡。工具決定論と commit 経路の直列化可能性の合算は
    証拠のカテゴリ混同）。
  受理ゲート方向（採択時の持ち越し案）: AG-192-05a 小ケース空間網羅完了と INV-01..08 全保持
    （または反例の裁定済み処理）。AG-192-05b fuzz スイートの INV-H1 証明完了。
    AG-192-05c 回帰コーパス固定 seed 再実行の証跡保存。宣言規律: PASS は
    LINEARIZATION_VALIDATION: EXECUTED の根拠となるが ACCEPTANCE != GLOBAL_ACCEPTANCE・
    TEST_PASS != ACCEPTANCE（モデル検証 PASS は実装検証ではない）をゲート文言に明記。
  理由（記録）: 1b は大ケース空間の証拠空白、1c は決定論保証の全ケース証明の欠落。2b は
    検証対象の取り違え（TEST_PASS != ACCEPTANCE の対象誤り）。3b はクラッシュ・部分書込み・
    framing の Lean 建模コストを契約採択前に前倒しする。4b は工具決定論と commit 経路
    直列化可能性の合算による証拠のカテゴリ混同。
  適用条件: STEP-192 §10 / OI-192-05 への語義反映（検証手法・INV 一覧・受理ゲート）は
    採択裁定（ADOPTION）時にドラフト本文へ反映する。本裁定時点ではドラフト本文を変更しない
    （filing discipline）。凍結層（v2.8.0-C / v2.9.4）は変更不要（D2 維持）。
  帰結: STEP-192 の OI は OI-192-06（intent_expiry と D5 凍結層拡張の接続）のみが残存 —
    これは凍結層拡張の独立採択裁定を内包するため、凍結層変更不要で閉じる OI-192-05 より
    後に順序する。検証スイート（L1 参照モデル + INV-01..08 + INV-H1）の実装は採択後の
    実工作業であり、本裁定は手法と受理基準のみを確定する。
  裁定表明: 2026-10-22、セッション内裁定フォーム（4 項目すべて推奨案で採択）。
    検討文書（repo 外）: ~/design-192/STEP192_OI192-05_ANALYSIS.md。
  対象: STEP192_COMMIT_ADMISSION_ATOMICITY_v0.1.0-draft.md §10 / §13 OI-192-05。

D12 — OI-192-06 裁定（intent_expiry と D5 凍結層拡張の接続）: RESOLVED (2026-10-23)
  裁定: 案E2 / 案G1 / 分離採択 / 案4a の組合せ採用。
  X1 拡張形態（案E2）: 凍結 Authority.lean / WAL.lean を一切変更しない。付加的拡張契約
    （新ファイル、例 AuthorityExpiry.lean — D5 適用条件の「拡張契約の採択」経路。凍結解除
    ではない）として validAt : ガバナンス prefix（またはその畳み込み状態）→ CausalContext →
    AuthorityRef → Prop を frozen valid と Composition で定義する。AuthorityProof
    （Replay.lean）は frozen valid のまま無変更で歴史的有効性を証明し続ける。
    E1（凍結 SignedAuthorityPayload への expiry フィールド追加 / valid の時刻再パラメータ化）は
    却下 — 凍結解除必須（D5 適用条件）、F3 により全既存署名証拠の再署名を要し、F5 により
    AuthorityProof / ValidatedEventStream / replay 全消費側の再定義を招き、歴史的有効性が
    時刻依存となり §10 決定論保証と衝突。E3（契約レベル宣言のみ）は E2 の前段として包含。
  X2 失効セマンティクス（案G1・位置ベース）: 失効・revocation は正準 governance event
    （D5 候補A）として正準列にコミットされ、「位置 e のガバナンス event 以降、その
    AuthorityRef への新規 commit を受け付けない」として建模。強制は現在有効性のみ
    （[admission, commit_point) 領域）。intent_expiry の時刻境界 [intent_begin, intent_expiry)
    （§4）は event payload の宣言時刻（契約レベル）で表現され、有効性判定そのものは位置照合。
    wall clock は判定に入らない（§10 時刻非依存・D9 G2 / D10 wall-clock 禁止と整合）。
    G2（wall-clock 引数失効）は却下。G3（監査側タイムスタンプ MAY）は本裁定では採用せず、
    D10 I1 の A2 留保と同型の強化オプションとして留保。
  X3 有効性の二面性分離 + NO_RETROACTIVE_INVALIDATION: 歴史的有効性（事象の正準位置時点の
    ガバナンス状態に対する述語。履歴 prefix のみから決定論的に評価可能・再生成不変。
    AuthorityProof はこれに対して無変更）と、現在有効性（admission 領域での実行時強制。
    §3 STALE_DECISION != CURRENT_PERMISSION の実行時版。監査ストアではなく正準ガバナンス
    prefix の最新位置から評価）を分離する。不変条件 NO_RETROACTIVE_INVALIDATION: 失効・
    revocation は発効位置より後の admission にのみ作用し、それ以前の committed レコード・
    Receipt・AuthorityProof を変更しない（変更すれば D8 M5・INV-03 の再生成決定論が崩れる）。
    単一の「現在有効性」への統一は却下（遡及無効化と再生成時刻依存のリスク）。
  X4 前提証拠ギャップ（案4a）: CausalContext の SSOT 定義の入手・監査（職場ホストまたは
    凍結ソースの提示）を採択（ADOPTION）の前提証拠 MUST とする（監査ギャップ G1:
    CONTRACT_ARTIFACTS_NOT_FOUND_IN_SCOPE — 本ホスト範囲の contracts/**/*.lean 全 12 ファイルに
    定義を発見せず。「存在しない」ではなく「範囲内未発見」と記録）。それまで拡張設計は
    CausalContext を不透明パラメータとして扱い、その内部構造に依存する決定を保留する
    （valid の型は引数としてのみ参照しており、内部構造非依存の E2/G1 設計は成立）。
    監査ギャップ G2（本ホストに lean / lake / elan 無し・凍結層コンパイル検証不能）は
    BLOCKED_EXTERNAL_ARTIFACT として継続記録し、検証は工具の揃うホストで実施する。
  理由（記録）: 監査結果 F1〜F5 が示す現行意味論は「署名証拠が存在すれば無期限に有効」
    （T-191-B の構造的正義）であり、AuthorityRef は位置・失効データを載せてはならない
    証明キー（F4・Normative Conflict 確定）。E2/G1 は凍結層の述語・署名証拠・消費側を
    一切変更せず、歴史的有効性の決定論（D8 M1・INV-03）と現在有効性の実行時強制を
    構造で分離するため、§10・D9・D10・D5 適用条件のすべてと整合する。
  適用条件: 本裁定は凍結解除を認可しない（認可されるのは「拡張契約の採択可否とその形」まで —
    D5 適用条件の範囲内）。AuthorityExpiry.lean 相当の拡張契約の実際の採択・CausalContext
    SSOT 監査（X4）は独立の採択裁定（ADOPTION）を要する（VERIFICATION_IS_NOT_AUTHORIZATION）。
    STEP-192 §12/§13 への語義反映は採択裁定時にドラフト本文へ実施し、本裁定時点では
    ドラフト本文を変更しない（filing discipline）。
  帰結: STEP-192 の OI-192-01..06 はすべて解決済み（D9 / D8 / D7 / D10 / D11 / D12）。
    OI-192-06 が内包していた「凍結層拡張の採択可否」は方針として確定し、残るは拡張契約
    本体の採択（ADOPTION）と X4 前提証拠の充足のみ。ADOPTION フェーズ（参照モデル L1
    検証ハーネス — D11 V4、ドラフト本文への D7〜D12 語義反映）への移行条件が揃う。
  裁定表明: 2026-10-23、セッション内裁定フォーム（4 項目すべて推奨案で採択）。
    検討文書（repo 外）: ~/design-192/STEP192_OI192-06_ANALYSIS.md。
  対象: STEP192_COMMIT_ADMISSION_ATOMICITY_v0.1.0-draft.md §3 / §4 / §12 / §13 OI-192-06 /
    D5 適用条件（contracts/governance/ADJUDICATIONS.md D5）。

## 未決のまま残るもの

- STEP-187/188/189 の全文確定と filing（全文はセッション DB にのみ存在）
- 凍結層拡張契約（AuthorityExpiry.lean 相当・validAt）の採択（ADOPTION）そのもの — D12 は
  拡張形態（E2）と失効セマンティクス（G1）の方針を確定したが、拡張契約本体の採択は
  独立の採択裁定を要する（D5 適用条件 / VERIFICATION_IS_NOT_AUTHORIZATION）。
- CausalContext SSOT 定義の入手・監査（D12 X4 採択前提証拠 MUST・G1
  CONTRACT_ARTIFACTS_NOT_FOUND_IN_SCOPE）と、lean / lake / elan の揃うホストでの凍結層
  コンパイル検証（G2 BLOCKED_EXTERNAL_ARTIFACT）。
- E-218-008（organizer 乖離）: UNRESOLVED のまま別証拠トラックで継続（D4 留保・D11 V6 分離維持）。
- STEP-192 OI は OI-192-01..06 すべて解決済み（OI-192-01 D9 / 02 D8 / 03 D7 / 04 D10 /
  05 D11 / 06 D12）。次フェーズは ADOPTION（ドラフト本文への D7〜D12 語義反映・
  参照モデル L1 検証ハーネス実装 — D11 V4/受理ゲート AG-192-05a..c）。
