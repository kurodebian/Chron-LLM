DOC: CHRON-R2.0-D-COMMIT-KERNEL-CONSTITUTION
REV: 1.0
STATUS: FREEZE_CANDIDATE
DEPS: [R2.0-A, R2.0-B, R2.0-C]

TYPE ID = Hash
TYPE Ref = Pointer
TYPE Enum = Symbol

TYPE CandidateEvent = { type: Enum, world-id: ID, parent-id: ID, payload-ref: Ref, metadata: Map, schema-version: Int }
TYPE CanonicalEvent = { event-id: ID, causal-id: ID, parent-id: ID, world-id: ID, type: Enum, payload-ref: Ref, schema-version: Int }
TYPE WALRecord = CanonicalEvent
TYPE CommitResult = { status: Enum[:committed, :rejected, :fault], event-id: ID?, causal-id: ID?, world-id: ID?, reason: String? }

STATE Graph = List[CanonicalEvent]
STATE WAL = List[WALRecord]
STATE WorldHead = Map[ID -> CanonicalEvent]
STATE Memory = ImmutableStore

FUNC GenEventID(c: CandidateEvent) -> ID = H(c.parent-id, c.world-id, c.type, c.payload-ref, c.schema-version)
FUNC GenCausalID(c: CandidateEvent, p: CanonicalEvent) -> ID = H(p.causal-id, c.world-id, c.type, c.payload-ref, c.schema-version)

OP Commit(c: CandidateEvent) -> CommitResult:
  PRE: c.payload-ref IN Memory AND (c.parent-id IN Graph OR c.parent-id == ROOT) AND c.world-id IN WorldHead
  STEPS:
    1. head = WorldHead[c.world-id]
    2. IF !ValidateParent(c, head) -> RETURN {status: :rejected, reason: "invalid-parent"}
    3. eid = GenEventID(c)
    4. cid = GenCausalID(c, head)
    5. ce = CanonicalEvent{event-id: eid, causal-id: cid, parent-id: c.parent-id, world-id: c.world-id, type: c.type, payload-ref: c.payload-ref, schema-version: c.schema-version}
    6. WAL.Append(ce)
    7. Graph.Append(ce)
    8. WorldHead[c.world-id] = ce
    9. RETURN {status: :committed, event-id: eid, causal-id: cid, world-id: c.world-id}
  POST:
    IF status == :committed -> ce IN Graph AND ce IN WAL AND WorldHead[c.world-id] == ce
    IF status != :committed -> Graph == Graph_old AND WAL == WAL_old AND WorldHead == WorldHead_old

INV:
  1. AUTHORITY: ONLY Commit OP modifies Graph, WAL, WorldHead
  2. UNIQUENESS: !exists(e1, e2 IN Graph | e1.event-id == e2.event-id && e1 != e2)
  3. APPEND_ONLY: Graph is strictly append-only
  4. IMMUTABILITY: CanonicalEvent fields immutable post-creation
  5. NO_TIMESTAMPS: CanonicalEvent excludes wall-clock time
  6. WAL_ORDERING: WAL commit precedes Graph visibility
  7. HEAD_VALIDITY: WorldHead[w].event-id IN Graph
  8. DETERMINISM: Commit(c) == Commit(c) given identical inputs
  9. IDEMPOTENCY: Repeated Commit(c) yields identical result
  10. ISOLATION: Commit(w1) does not affect WorldHead[w2] where w1 != w2
  11. MEMORY_REF: CanonicalEvent.payload-ref points to Immutable Memory
  12. GRANULARITY: 1 Commit == 1 CanonicalEvent == 1 Graph Append

TESTS:
  D1: Valid Commit -> :committed
  D2: Invalid Candidate -> :rejected, No Mutation
  D3: Deterministic ID -> H(Inputs) == ID
  D4: Graph Append Only -> Len(Graph) increases by 1
  D5: Visibility Order -> WAL -> Graph -> WorldHead
  D6: WAL Replay -> Reconstructs Graph
  D7: Duplicate -> Same Result
  D8: Crash Recovery -> No Corruption
  D9: Cross World Isolation -> No Side Effects
  D10: Memory Immutability -> Payload unchanged