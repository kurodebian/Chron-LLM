enum ToolEvent = {START, TIMEOUT, ABORT, COMMIT}
type Context = { causal_id: ID }
type State = { canonical: CanonicalState, dialogue: DialogueState }

op apply(evt: ToolEvent) -> State'

INV(authority): State'.canonical != State.canonical <-> evt.type == COMMIT
INV(isolation_fail): evt.type in {TIMEOUT, ABORT} -> State'.dialogue == State.dialogue
INV(causal_id): forall e: ToolEvent, e.causal_id == Context.causal_id

op retry() -> Stream<ToolEvent>
INV(retry_scope): retry() subset_of tool_stream
INV(retry_no_mutation): on(RETRY) -> State.canonical == prev(State.canonical)

INV(no_bypass): evt.type != COMMIT -> State'.canonical == State.canonical
INV(determinism): replay(Events) -> deterministic_outcome