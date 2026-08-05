# base-invariants.spec
SPEC: BaseInvariants
VERSION: 1.0.0

USES:
  BaseTypes

DESCRIPTION:
  Chron-LLM 全域で参照される標準不変条件（Standard Invariants）および
  決定論・純粋性・権威境界の公理的定義。

DEFINITIONS:

  # 1. Pure Function & Determinism (純粋性と決定論)
  INV_DEF PUR-001: pure(f: Function)
    AXIOM: no_side_effects(f) = true
    AXIOM: no_external_io(f) = true
    AXIOM: deterministic(f) = true
    AXIOM: environmental_dependencies(f) = ∅
    DOC: "関数 f は外部副作用・外部IO・暗黙の環境依存を持たない純粋関数であること。"

  INV_DEF DET-001: deterministic(f: Function)
    AXIOM: ∀ x1 x2, (x1 = x2) ⇒ (f(x1) = f(x2))
    DOC: "同一の入力状態に対して、常に同一の出力状態を算出すること（数学的一致）。"

  INV_DEF DET-002: deterministic_under(f: Function, context: Context)
    AXIOM: ∀ x1 x2 c, (x1 = x2) ⇒ (f(x1, c) = f(x2, c))
    DOC: "指定されたコンテキスト (例: ABI) の下で決定論的であること。"

  # 2. Append-Only & Reproducibility (追記専用性と再現性)
  INV_DEF APP-001: append_only(target: DataStore)
    AXIOM: target.mutable = false
    AXIOM: ∀ t1 t2, (t1 < t2) ⇒ is_prefix_of(target@t1, target@t2)
    DOC: "対象データストアは過去の履歴を変更できず、末尾への追記のみが許容されること。"

  INV_DEF REP-001: reproducible(evaluator: Function, history: History)
    AXIOM: ∀ h1 h2, (h1 = h2) ⇒ (evaluator(h1) = evaluator(h2))
    DOC: "同一の履歴 h を再実行した場合、常に全く同一の状態に到達すること。"

  INV_DEF REP-002: replay_deterministic(pipeline: Pipeline, history: History)
    AXIOM: ∀ h1 h2, (h1 = h2) ⇒ (pipeline.run(h1) = pipeline.run(h2))
    DOC: "パイプライン全域 (H -> M -> S -> G) の再実行出力が履歴に対して完全一致すること。"

  # 3. Derivation & Pure Projection (純粋導出と隠れ状態排除)
  INV_DEF DER-001: derived_exclusively_from(target: State, source: State)
    AXIOM: dependencies(target) = {source}
    AXIOM: ∀ s1 s2, (s1 = s2) ⇒ (derive(s1) = derive(s2))
    DOC: "target の生成ロジックは source のみを唯一の依存源とし、隠れた状態を参照しない。"

  INV_DEF DER-002: preserves_order(f: Function, sequence: Sequence)
    AXIOM: ∀ i j, (i < j) ⇒ (index_of(f(sequence[i])) < index_of(f(sequence[j])))
    DOC: "変換処理 f は、入力シーケンスの因果順序（インデックス順）を破壊しない。"

  # 4. Authority & Boundary Isolation (権威隔離と逆流禁止)
  INV_DEF AUTH-001: authoritative(target: DataStore, authority_kind: AuthorityKind)
    AXIOM: target.authority = Authoritative(authority_kind)
    AXIOM: append_only(target)
    DOC: "正実（Canonical Authority）は Append-only であり、指定された権威分類を持つ。"

  INV_DEF AUTH-002: non_authoritative(target: State)
    AXIOM: target.authority = NonAuthoritative
    AXIOM: ∀ auth_state, (authoritative(auth_state, _)) ⇒ (target CANNOT_MUTATE auth_state)
    DOC: "非権威層（二次的プロジェクション/グラフ等）は、いかなる権威状態に対しても変異を起こしえない。"