# base-history.spec
SPEC: BaseHistory
VERSION: 1.0.0

USES:
  BaseTypes
  BaseInvariants
  BaseExcludes

DESCRIPTION:
  Causal Authority (因果権威) の根幹をなす不変イベントログ、
  識別子、および History 型の所有権を定義する基底仕様。

TYPES:
  TYPE CausalID = String
  TYPE EventPayload = String

  TYPE Event = Frozen<{
    causal_id    : CausalID,
    commit_index : CommitIndex,
    payload      : EventPayload
  }>

  TYPE History = Frozen<List<Event>>

STATE:
  HistoryStore : History

AXIOMS:
  AXIOM: AUTH-001(HistoryStore, Causal)
  AXIOM: APP-001(HistoryStore)