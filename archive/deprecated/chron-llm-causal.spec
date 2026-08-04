TYPE Event = { node-id: Int, causal-id: Int, kind: Symbol, payload: Any, clock: Int? }
TYPE WAL = { storage: [Event], staged-events: [Event], clock: Int, node-counter: Int, world-counter: Int }

INIT WAL = { storage: [], staged-events: [], clock: 0, node-counter: 1000, world-counter: 100 }

OP invariant-check(wal: WAL) -> Bool
  return true

OP make-event(wal: WAL, kind: Symbol, payload: Any) -> Event
  node-id = wal.node-counter++
  return { node-id, causal-id: 0, kind, payload, clock: null }

OP stage-event(wal: WAL, event: Event) -> WAL
  wal.staged-events.push(event)
  return wal

OP commit-event(wal: WAL, event: Event) -> Event
  wal.clock++
  event.clock = wal.clock
  wal.storage.push(event)
  return event

OP append-event(wal: WAL, kind: Symbol, payload: Any) -> Event
  e = make-event(wal, kind, payload)
  return commit-event(wal, e)

OP rollback-stage(wal: WAL) -> WAL
  wal.staged-events = []
  return wal

OP discard-staged(wal: WAL) -> WAL
  wal.staged-events = []
  return wal

OP commit-staged(wal: WAL) -> { success: Bool, committed-events: [Event] }
  PRE: invariant-check(wal)
  committed = []
  for e in wal.staged-events: committed.push(commit-event(wal, e))
  wal.staged-events = []
  POST: wal.staged-events.length == 0
  return { success: true, committed-events: committed }

OP clear-wal(wal: WAL) -> WAL
  wal = INIT WAL
  return wal

INV clock-monotonic: forall i < j in wal.storage: wal.storage[i].clock < wal.storage[j].clock
INV node-unique: forall i != j in wal.storage: wal.storage[i].node-id != wal.storage[j].node-id
INV post-commit: after commit-staged: wal.staged-events.length == 0