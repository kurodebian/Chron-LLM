# base-excludes.spec
SPEC: BaseExcludes
VERSION: 1.0.0

DESCRIPTION:
  Chron-LLM パイプライン内での使用が固く禁止される非決定論的・不透明要素の全域除外規定。

EXCLUDE_DEFINITIONS:

  EXCLUDE: WallClockTime
    DOC: "システム時刻、現在時刻（OSタイマー）の参照禁止。代替: CommitIndex"

  EXCLUDE: RandomNumberGeneration
    DOC: "乱数、シード非固定の疑似乱数生成の禁止。"

  EXCLUDE: HiddenState
    DOC: "関数外部・スコープ外の暗黙的・隠れ状態（クロージャ内の隠れ変数含む）の参照禁止。"

  EXCLUDE: MutableGlobal
    DOC: "グローバル可変変数、シングルトンミュータブル状態の禁止。"

  EXCLUDE: ExternalIO
    DOC: "非同期ネットワーク通信、ファイルシステムへの直接読み書きなど、純粋関数外とのIO禁止。"

  EXCLUDE: UnboundedConcurrency
    DOC: "実行順序が保証されない非決定論的マルチスレッド競合の禁止。"
