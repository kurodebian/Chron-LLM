# Step 10 — 決定的検証契約（Deterministic Verification Contract）

**Contract ID:** `DV`
**Version:** `0.1.0-draft`
**Status:** `DRAFT / NOT FROZEN`
**Phase:** `DESIGN ONLY`
**Mutation policy:** `NO_MUTATION`（実ファイル照合・編集、Validator 実装・実行、テスト、Freeze はいずれも GATED）
**Normative target:** ローカル LLM が生成する提案（Proposal）に対する決定的検証器の判定契約

---

## 0. この文書の位置づけ

Step 9 の失敗モード分析を受けて、LLM 提案を **どの条件で受理・拒否・保留するか** を決定的に定義する。

前提原則:

1. LLM は **提案を生成する**。
2. 決定的検証器は **契約への適合性を判定する**。
3. 契約への適合は **提案の意味的な正しさを証明しない**。
4. 検証器は **権限を付与しない**。権限は検証器の外部で明示的に付与される。

本契約は設計のみを行う。実装・実行・テスト・凍結は行わない。
§11 に「実施しなかったこと」を明記する。

---

## 1. 用語と固定入力契約

### 1.1 Fixed Input Bundle（FIB）

検証器が参照できる唯一の権威ある入力。以下を必須要素とする。

| 要素 | 内容 | 権威性 |
| --- | --- | --- |
| `adopted_norms` | 採択済み規範の集合（`norm_id`, `norm_version`, `norm_digest`） | 規範的権威 |
| `candidate_registry` | 候補 ID の閉じた集合（closed world） | ID の存在判定の権威 |
| `evidence_state` | 主張・候補ごとの証拠状態（§1.3） | 証拠状態の権威 |
| `input_version` | FIB のバージョンとバイト列の SHA-256（`input_digest`） | 入力固定の権威 |
| `ruleset_version` | 検証規則のバージョンと `ruleset_digest` | 規則の権威 |
| `authority_state` | 各ゲートの状態（`GATED` / `RELEASED(scope)`）と許可レコード | 権限の権威 |

**Closed-world 規則.** `candidate_registry` に存在しない ID は「存在しない」と確定している事実とする。
**Version-binding 規則.** 提案は検証対象の `input_digest` を明示的にバインドしなければならない（`DV-01`）。

### 1.2 Proposal（検証対象）

提案は少なくとも次を含む（具体的なフィールド名・型は §9 OPEN-10-1 で未確定）。

- `proposal_id`
- `input_digest`（バインド）
- `claims[]`（`claim_id`, `claim_type`, 内容, `evidence_refs[]`, `norm_refs[]`）
- `dependencies[]`（`from`, `to`）
- `requested_disposition`（提案が確定を要求するか否か: `NONE` / `REVIEW` / `DECIDE`）
- `counter_evidence[]`（反証の参照）

### 1.3 Evidence status（閉じた列挙）

| 状態 | 意味 | 判定寄与 |
| --- | --- | --- |
| `CONFIRMED` | 証拠管理機構により確認済み | FACT を支持しうる |
| `UNCONFIRMED` | 参照はあるが未確認 | 支持しない |
| `CONTRADICTED` | 反証が確認済み | 支持しない |
| `NOT_EVALUATED` | 未確定スロット（判定未実施） | 未知（保留要因） |
| `ABSENT` | 該当証拠なしと確定 | known-negative |

**核心の区別.** `ABSENT` / 未登録 ID は **known-negative**。`NOT_EVALUATED` は **not-yet-determined**。
この区別が §4 の REJECT / HOLD 境界の基盤になる。

---

## 2. 検証パイプライン（ステージと順序）

検証器は以下のステージを **この順序で** 評価する。順序は契約の一部であり、実装ごとに変えてはならない。

| Stage | 対象 | 対応規則 |
| --- | --- | --- |
| `S0 TRANSPORT` | JSON として解析可能か、バイト固定が確認可能か | DV-01 |
| `S1 STRUCTURE` | 必須フィールド、型、列挙値、ID 形式、重複規則 | DV-01 |
| `S2 REFERENCE` | 参照 ID が FIB に存在するか、`input_digest` バインド一致 | DV-02 |
| `S3 EVIDENCE` | 主張の `claim_type` と `evidence_state` の整合 | DV-02 |
| `S4 DEPENDENCY` | 依存先の存在、自己依存、循環、未確定依存 | DV-03 |
| `S5 TRANSITION` | 許可された状態遷移か | DV-04 |
| `S6 AUTHORITY` | 提案が権限を主張・導出していないか | DV-05 |
| `S7 HANDOFF` | 意味的レビューへ渡す範囲と未解決事項の確定 | §6 |

### 2.1 評価方針（決定性のため）

- **Fail-fast しない。** S1 で違反があっても S2〜S6 まで評価を試みる。
- 前段の不正により評価不能なステージは `NOT_EVALUATED` として記録し、**判定には寄与させない**。
- 判定は **確定した違反のみ** で決める。
- 違反・所見は **規則 ID の昇順** で並べて出力する（列挙順は出力の再現性に含まれる）。

### 2.2 検証器の異常と提案の不適合の分離

| 事象 | 扱い |
| --- | --- |
| 提案が JSON ですらない／契約に違反 | `REJECT`（提案側の不適合） |
| 検証器が規則を読み込めない／例外で中断 | `EXECUTION_FAULT`（検証結果ではない） |
| FIB のダイジェスト取得不能 | `EXECUTION_FAULT` |
| FIB と提案の `input_digest` 不一致 | `REJECT`（`STALE_INPUT_BINDING`） |

`EXECUTION_FAULT` は §3 の 3 判定のいずれにも写像してはならない。
「検証に成功したように見せる」経路を禁止する（別終了コード・別レコード型）。

---

## 3. 検証結果の契約

### 3.1 3 つの判定

| 結果 | 意味 | 次の処理 |
| --- | --- | --- |
| `ACCEPT_FOR_REVIEW` | 構造・参照・状態などの機械的条件に適合 | 意味的レビュー・規範照合へ |
| `REJECT` | 確定済み規則または固定入力に対する矛盾が確定 | 違反を記録し、修正提案または再生成を要求 |
| `HOLD` | 必須証拠・規範・判断が不足（未確定スロットが存在） | 不足情報を要求し、確定を保留 |

`ACCEPT_FOR_REVIEW` は「レビュー対象として受理した」だけを意味する。
規範への採択・実行許可を意味する `ACCEPT` ではない。`ACCEPT` は検証器の出力語彙に含めない。

### 3.2 判定優先順位

```
verdict =
  EXECUTION_FAULT        if 検証器自体の実行障害
  else REJECT            if REJECT 級の違反が 1 つ以上確定
  else HOLD              if HOLD 級の条件が 1 つ以上確定
  else ACCEPT_FOR_REVIEW otherwise
```

- **REJECT > HOLD.** 確定した規則違反は、情報追加によって治愈されない。HOLD を返すと違反が隠蔽される。
- 両方が同時に成立する場合、判定は `REJECT` とし、HOLD 級条件も所見としてすべて記録する。

### 3.3 判定レコード（Verdict Record）必須要素

| フィールド | 目的 |
| --- | --- |
| `verdict` | 3 判定のいずれか |
| `verdict_record_type` | `VERIFICATION` / `EXECUTION_FAULT` の区別 |
| `input_digest`, `ruleset_digest`, `validator_version`, `config_digest` | 再現性 |
| `stage_coverage` | 各ステージが `EVALUATED` / `NOT_EVALUATED` |
| `findings[]` | `rule_id`, `code`, `severity`, `subject_id`, `basis`（規則条文への参照） |
| `unresolved[]` | HOLD 級条件・未確定依存・意味的レビューへ渡す項目 |
| `semantic_review_scope[]` | 機械検証では判定不能な主張のリスト |
| `no_repair` | 修復・補完を行っていないことの宣言 |

**禁止.** 検証器は提案の内容を書き換えない。正規化・補完・推測復元を行わない。
**必須.** 同一入力（同一 FIB・同一規則・同一設定）に対し、同一判定レコードを返す。

---

## 4. REJECT / HOLD 境界の判別規則（暫定確定）

境界は「条件の性質」で決める。重大度や LLM の自信度で決めてはならない。

### 4.1 判別テスト

条件 C について:

1. **固定入力のみから C の違反が確定できるか？**
2. **提案側が情報を追加しても、FIB または規範が変わらない限り判定が覆らないか？**

| 1 | 2 | 級 |
| --- | --- | --- |
| Yes | Yes | **REJECT 級**（固定入力に対する矛盾） |
| No | — | **HOLD 級**（未確定スロット） |
| Yes | No（追加情報で正当化されうる） | **HOLD 級**（§4.3 の限定付き） |

### 4.2 既定の分類（本契約で暫定確定）

| 条件 | 級 | 根拠 |
| --- | --- | --- |
| 参照 ID が `candidate_registry` に存在しない | REJECT | known-negative（closed world） |
| `claim_type = FACT` で `CONFIRMED` 証拠がない | REJECT | 固定入力の証拠状態との矛盾（`EPISTEMIC_INFLATION`） |
| `HYPOTHESIS` を事実として提示（FACT 化） | REJECT | 閉じた語彙の違反 |
| 不正な型・未知の列挙値・不正 ID 形式 | REJECT | 出力契約違反 |
| 同一候補 ID の複数出現（同一内容を含む） | REJECT（暫定） | 一意性規則違反。OPEN-10-7 |
| `input_digest` バインド不一致 | REJECT | 入力固定契約違反 |
| 許可されていない状態遷移の要求 | REJECT | 遷移表違反 |
| 証拠が `UNCONFIRMED` / `NOT_EVALUATED` で、かつ `requested_disposition = DECIDE` | HOLD | not-yet-determined |
| 必要な規範が未採択 | HOLD | 規範のスロット未確定 |
| 根拠が存在するが主張を支持するか不明 | `ACCEPT_FOR_REVIEW` + `semantic_review_scope` | 機械判定不能 |
| 依存先の状態が未確定で、候補の確定を要求 | HOLD | 依存未確定 |

### 4.3 HOLD の発火条件（設計決定）

`HOLD` は **情報不足そのもの** では発火しない。
**提案が確定（採択・解決・実行）を要求したときに限り** 発火する。

- `requested_disposition = NONE`（単なる記録・観察の提案）で情報不足 → `ACCEPT_FOR_REVIEW` + `unresolved[]` に記録。
- `requested_disposition = DECIDE` で情報不足 → `HOLD`。

理由: 情報不足を理由に観察記録自体を拒否すると、未知事項の可視化という目的と矛盾する。
一方で、未確定のまま確定を要求する行為は保留しなければならない。

### 4.4 FACT 証拠欠落の最終判定

Step 10 の暫定決定: **REJECT**（`EPISTEMIC_INFLATION`）。

代替案（HOLD）は「証拠が存在する可能性が残っている」ケースを救うが、FIB が `ABSENT` を確定している場合に
検証器が可能性を推測することになり、§7 の決定性要件に反する。
正式採否は OPEN-10-5 で保留。

---

## 5. 決定的検証ルール DV-01〜DV-05

### DV-01 出力構造

- 必須フィールドの欠落を拒否する。
- 型違反、未知の列挙値、不正な ID 形式を拒否する。
- 重複フィールド・重複候補 ID の扱いは契約で定義する（暫定: 同一 ID の複数出現は REJECT）。
- 不正出力を推測で修復・補完しない。
- 検証器自身の異常と提案の不適合を区別する（§2.2）。
- JSON Schema で表現できる構造制約は Schema に委ね、レコード横断の整合性は決定的検証ロジックで扱う。

**決定性要件.** Schema 検証の合否は、Schema 版本・解決された `$ref`・`format` 処理の設定にのみ依存する。
暗黙のデフォルト（追加プロパティの扱い、`format` 検証の有無）は設定として固定し、判定レコードに記録する。

### DV-02 証拠整合性

| 条件 | 判定 |
| --- | --- |
| 参照 ID が入力契約に存在する | 参照形式の検査を通過（支持は意味的レビュー） |
| 参照 ID が存在しない | REJECT |
| FACT に確認済み証拠がない | REJECT（§4.4 暫定） |
| HYPOTHESIS を事実として提示 | REJECT |
| 証拠が未確認・不足 | `requested_disposition` に応じて HOLD または ACCEPT_FOR_REVIEW + unresolved |
| 根拠が存在するが主張を支持するか不明 | 意味的レビューへ送る |

**核心.** 参照 ID の存在（機械的）と、参照先が主張を支持していること（規範的・意味的）は別の性質である。
検証器は後者を判定したと記録してはならない。

### DV-03 依存関係

- 依存先は FIB に登録された ID に限定する。未登録 ID への依存は REJECT。
- 自己依存（`from == to`）は REJECT。
- 循環依存は検出して記録する。検証器は循環を **自動的に解消しない**。
- 未確定の依存先を確定済みとして扱わない。
- 依存先の状態が変わった場合、影響を受ける候補の再評価を要求する（`revalidation_required`）。
- 優先順位を依存関係だけから一意に導けない場合は未確定として保持する（HOLD または unresolved 記録）。

**循環の報告形式（暫定).** 循環は参加 ID を昇順に正規化し、最小循環のみ列挙する。
複数循環の列挙順は辞書順とする。正式仕様は OPEN-10-6。

### DV-04 状態遷移

候補の判断状態とレビュー実行状態は **直交する別軸** として管理する。

| 軸 | 状態（例） | 遷移上の制約 |
| --- | --- | --- |
| 候補の判断（epistemic） | `UNVERIFIED` → `EVIDENCED` → `RESOLVED` / `CONTRADICTED` | 証拠なしに `RESOLVED` へ遷移できない |
| 候補の採否（disposition） | `DEFER` → `ACCEPTED` / `REJECTED` | レビューの反復だけでは確定しない。裁定レコードが必要 |
| レビュー実行（review execution） | `NOT_REVIEWED` → `IN_REVIEW` → `NEEDS_REVIEW` → `REVIEW_COMPLETE` | 未解決の問題を保持したまま完了扱いにしない |
| 実行権限（authority） | `GATED` → `RELEASED(scope)` | 明示的な許可手続きのみ。検証器出力では解除されない |

禁止遷移（例）:

- `UNVERIFIED → RESOLVED`
- `DEFER → ACCEPTED`（裁定レコードなし）
- `NEEDS_REVIEW → REVIEW_COMPLETE`（open finding 保持中）
- `GATED → RELEASED`（検証器の判定のみによる）
- `REVIEW_COMPLETE → FREEZE`（この遷移は存在しない。Freeze は別ゲート）

`REVIEW_COMPLETE` の完了条件（暫定）: すべての `findings` が解決済みまたは理由付きで close 済み、
かつ `unresolved[]` が空、かつ `semantic_review_scope[]` のすべてに裁定または明示的な保留決定がある。

**状態遷移の妥当性** は許可された遷移表に基づき機械的に判定する。完全な遷移表は OPEN-10-2。

### DV-05 権限境界

権限は LLM の出力から導出しない。

- `PROPOSAL` は変更許可ではない。
- `REVIEW_COMPLETE` は Freeze 許可ではない。
- `RESOLVED` は実装検証済みという意味ではない。
- `GATED` を解除できるのは、別途定義された明示的な許可手続きだけとする。
- 将来の実装では、プロンプトだけでなく **ツール権限・実行経路** でも制限する（プロンプト上の禁止文に依存しない）。

許可レコード（Authorization Record）の必須要素（暫定）: `grant_id`, `granted_by`（人間または明示的裁定主体）,
`scope`, `target_input_digest`, `allowed_operations[]`, `issued_at`, `expires_at`, `audit_ref`。正式仕様は OPEN-10-10。

**検証器の権限.** 検証器は `findings` と `verdict` を書くことだけを許される。
`disposition`・`authority`・`freeze_status` を書く権限を持たない。

---

## 6. 検証責務の分離

| 検証対象 | 主たる責務 |
| --- | --- |
| JSON 構造・型・列挙値 | Schema |
| 入力に対する ID の存在・一意性 | 決定的検証器 |
| 依存グラフの循環・参照整合性 | 決定的検証器 |
| 状態遷移の許可条件 | 決定的検証器 |
| 証拠の実在・出所・固定バージョン | 証拠管理機構 |
| 証拠が主張を意味的に支持するか | 意味的レビューと規範照合 |
| 規範上の採択・拒否 | 明示的な裁定手続き |
| ファイル編集・実行・Freeze の権限 | 外部の実行ゲート |

**Schema 合格が意味すること.** 構造契約への適合のみ。
意味的正当性・証拠の真正性・規範への採択・実行許可のいずれも保証しない。
`ACCEPT_FOR_REVIEW` を「検証済み」と呼称することを禁止する。

---

## 7. 決定性・再現性の要件

検証器は以下を満たさなければならない。

1. LLM 判断・確率的分類・類似度・モデル自信度・コーパス頻度・暗黙の heuristic（未文書化の経験則）を使用しない。
2. 乱数・壁時計・ネットワーク・非決定な反復順序（ハッシュセット順など）に判定が依存しない。
3. 全入力に対して全関数として振る舞う（例外時は `EXECUTION_FAULT` を返す）。
4. 冪等である（同一入力の再検証で同一レコード）。
5. 入力を一切変更しない（read-only）。
6. 判定レコードに `input_digest`, `ruleset_digest`, `validator_version`, `config_digest` を記録する。
7. 実行障害は再試行可能性・終了コードで区別し、検証結果に偽装しない。

---

## 8. Step 9 失敗モードとの対応（暫定・未照合）

Step 9 の失敗モード一覧は本セッション外に記録されている可能性が高く、
実ファイル照合は GATED であるため **対応関係は未検証** である（OPEN-10-11）。

| 想定失敗モード | 抑止規則 |
| --- | --- |
| 存在しない ID・証拠の捏造 | DV-02（closed world） |
| 確信度の昇格（HYPOTHESIS → FACT） | DV-02（`EPISTEMIC_INFLATION`） |
| 循環・未確定依存の隠蔽 | DV-03 |
| 状態の自動昇格（レビュー反復で採択） | DV-04 |
| 提案を実行許可として扱う | DV-05 |
| 不正出力の静かな修復 | DV-01（no repair） |
| 検証器障害の「合格」への偽装 | §2.2 / §3.1 |
| 古い入力バージョンへの参照 | DV-01（version binding） |
| 構造合格を意味的正しさと誤認 | §6 |

---

## 9. 未確定事項（OPEN）

| ID | 内容 | Step 11 への影響 |
| --- | --- | --- |
| OPEN-10-1 | 具体的な出力 Schema（フィールド名・必須性・ID 形式正規表現・閉じた列挙値集合） | Validator 実装に BLOCKING |
| OPEN-10-2 | 完全な状態遷移表（4 軸の全状態と許可遷移の閉じた集合、完了条件の完全列表） | DV-04 実装に BLOCKING |
| OPEN-10-3 | エラーコード体系（規則 ID ↔ コード、深刻度、報告順序、互換性ポリシー） | 判定レコード契約に BLOCKING |
| OPEN-10-4 | §4 の REJECT / HOLD 分類の正式採否（暫定規則の承認） | 結果契約に BLOCKING |
| OPEN-10-5 | FACT 証拠欠落の最終判定（REJECT / HOLD） | DV-02 に BLOCKING |
| OPEN-10-6 | 循環依存の報告形式（正規化・最小循環のみか・部分解決の扱い） | DV-03 実装に BLOCKING |
| OPEN-10-7 | 重複候補 ID・重複フィールドの扱い（同一内容の重複は許容か） | DV-01 に BLOCKING |
| OPEN-10-8 | `EXECUTION_FAULT` の下位分類（終了コード、再試行可能性、障害報告様式） | 失敗分類に BLOCKING |
| OPEN-10-9 | 意味的レビューへの引き渡し単位（提案全体 / claim 単位） | レビュー機構設計に BLOCKING |
| OPEN-10-10 | 許可レコード（Authorization Record）の正式仕様 | 権限ゲートに BLOCKING |
| OPEN-10-11 | Step 9 失敗モード一覧との対応の照合（実ファイル照合が必要・GATED） | 網羅性証明に BLOCKING |
| OPEN-10-12 | `requested_disposition` の語彙確定（`NONE` / `REVIEW` / `DECIDE` の妥当性） | HOLD 発火規則に BLOCKING |

**BLOCKING 宣言.** 上記のうち OPEN-10-1〜OPEN-10-5、OPEN-10-8 は、
Step 11 の「設計完了条件」を真にするために解決が必要である。
現時点で Step 11 の受入基準を **合格済みとして宣言することは禁止** である。

---

## 10. Step 11 への引き継ぎ

Step 11 で扱う 4 領域と、Step 10 が渡す材料:

1. **機能的受入基準** — 不正出力・未知 ID・循環依存・証拠不足の識別。→ §5 の規則 ID と §4 の分類表。
2. **安全性の受入基準** — GATED 操作を実行できないこと、提案の自動昇格がないこと。→ DV-04 / DV-05 と禁止遷移リスト。
3. **再現性の受入基準** — 固定入力と記録された設定からの再現。→ §7 と判定レコードのダイジェスト群。
4. **設計完了条件** — 必須規則・状態遷移・失敗分類・未解決事項の明示、BLOCKING なし。→ §9 の OPEN 一覧が未解決事項の正式記録。

**区別の維持.** 基準が設計済みであることと、実行による証明が済んでいることは異なる。
Step 11 で基準を定義しても、テスト実行（GATED）による適合証明がなければ実装の適合性は未確認のまま。

---

## 11. 本 Step で実施しなかったこと（GATED 遵守）

- 実ファイルの照合・編集（既存 spec / schema / validator / テストファイルへの読み書き照合）: **未実施**
- Validator の実装・実行: **未実施**
- テストの作成・実行: **未実施**
- Freeze・凍結報告・状態の更新: **未実施**
- Step 9 成果物との対応照合: **未実施**（OPEN-10-11）
- 既存の規範・候補登録・証拠状態の実在確認: **未実施**（§1 は契約上の定義であり、実データへの照合ではない）

本契約は設計成果物であり、実装の適合性・網羅性・安全性の実証は行っていない。

---

## 12. Step 10 判定

```
STEP 10 = DRAFTED（設計済み）

設計済み:
  検証アーキテクチャ（固定入力 → 提案 → 決定的検証器 → 判定 → レビュー・裁定）
  検証ステージ S0〜S7 と評価方針
  DV-01〜DV-05
  検証結果の 3 区分 + EXECUTION_FAULT の分離
  REJECT / HOLD 判別規則（known-negative vs not-yet-determined）
  HOLD 発火条件（requested_disposition 依存）
  検証責務の分離
  決定性・再現性要件
  未確定事項の正式記録（OPEN-10-1〜OPEN-10-12）

未確定:
  具体的な出力 Schema / 完全な遷移表 / エラーコード体系 /
  各条件の正式分類 / FACT 証拠欠落の最終判定 / 循環報告形式

実行制限:
  実ファイル照合・編集、テスト、Validator 実行、Freeze は GATED
```
