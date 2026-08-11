# spec-metamodel.spec
SPEC: SpecMetamodel
VERSION: 1.0.0

DESCRIPTION:
  Chron-LLM のすべての仕様書（.spec）が準拠すべきメタモデル定義。
  AST 構造、不変条件の命名規則 (Namespace 規約)、構文妥当性検証ルールを規定する。

TYPES:
  TYPE SpecIdentifier = String
  TYPE InvariantID    = NamespaceInvariantID  # Regex: ^[A-Z]+\.[A-Z]+\.[0-9]{3}$

COMPILER_VALIDATION_RULES:

  # Rule 1: Single Top-Level Definition
  RULE R001: "1つの .spec ファイルは、厳密に1つの SPEC ブロックのみを定義しなければならない。"

  # Rule 2: Version Semantics
  RULE R002: "すべての SPEC は BaseTypes.Version に準拠した VERSION 定義を持たなければならない。"

  # Rule 3: Namespace Invariant Identification
  RULE R003: "すべての INV_DEF 識別子は '<Category>.<Subcategory>.<Number>' (例: ABI.REG.001, PIPE.CORE.001) の Namespace 形式であり、宇宙全体で一意でなければならない。"

  # Rule 4: Type Scoping
  RULE R004: "INV_DEF 内で使用されるすべての型は、自仕様の TYPES、または USES で指定された仕様で宣言されていなければならない。"

  # Rule 5: Exclusion Enforcement
  RULE R005: "EXCLUDES に指定された概念 (例: WallClockTime) に依存する操作・関数の定義はコンパイルエラーとする。"

  # Rule 6: Invariant Reference Binding & Scoping
  RULE R006: "すべての INV_DEF 内で参照される型、述語、操作、不変条件識別子は、自仕様の TYPES/OPERATIONS または USES 先の仕様に存在しなければならない。"