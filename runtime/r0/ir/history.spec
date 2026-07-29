MODULE chronos-r0.history
TYPE HistoryEvent = { role: Any , content: Any }
TYPE History = { events: Vector[HistoryEvent] }
make-history() -> h: History ; INIT(h.events) = []
make-history-event(r: Any , c: Any) -> e: HistoryEvent ; e.role=r ; e.content=c
history-events(h: History) -> Vector[HistoryEvent]
history-event-role(e: HistoryEvent) -> Any
history-event-content(e: HistoryEvent) -> Any
history-append(h: History , e: HistoryEvent) -> h ; MUTATE(h.events = append(h.events, [e])) ; RET(h)
history-size(h: History) -> n: Integer ; n = LEN(h.events)
history-copy(h: History) -> h': History ; INIT(h'.events) = COPY-SEQ(h.events) ; SHALLOW_COPY_EVENTS
INV(history-append): APPEND_ONLY , PRESERVE_ORDER
INV(history-size): SIZE_CONSISTENT
INV(history-copy): VECTOR_CLONED , EVENTS_SHARED
INV(module): PURE_DATA_LAYER , NO_EXTERNAL_DEPS