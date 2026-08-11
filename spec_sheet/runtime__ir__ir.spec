PKG ir
EXPORTS [
    make-ir, ir-p, ir-ctx-id, ir-pos, ir-phase, ir-token, ir-score,
    IR_Buffer, allocate-buffer, push-ir, clear-buffer, snapshot-buffer,
    buffer-overflow-p
]

;; 1. Canonical Enum & Structural Types
TYPE Phase = {0:PREFILL | 1:GENERATION | 2:FINALIZE}
TYPE TOKEN_ID = INT
TYPE ID = PTR

TYPE IR = STRUCT {
    ctx-id: ID;
    pos: INT;
    phase: Phase;
    token: TOKEN_ID;
    score: FLOAT
}

;; 2. Integrated Thread-Safe Buffer
TYPE IR_Buffer = STRUCT {
    capacity: INT;
    size: ATOMIC_INT;
    overflow_count: ATOMIC_INT;
    data: Array[IR]
}

;; 3. Core Operations
OP make-ir(ctx-id:ID, pos:INT, phase:Phase, token:TOKEN_ID, score:FLOAT) -> IR
OP ir-p(x) -> BOOL
ACC ir-ctx-id(IR) -> ID
ACC ir-pos(IR) -> INT
ACC ir-phase(IR) -> Phase
ACC ir-token(IR) -> TOKEN_ID
ACC ir-score(IR) -> FLOAT

OP allocate-buffer(capacity: INT) -> IR_Buffer
    PRE: capacity > 0
    EFFECT: buf = STRUCT {
                capacity: capacity,
                size: atomic_store(0),
                overflow_count: atomic_store(0),
                data: allocate_array(IR, capacity)
            }
    POST: buf.size == 0

OP push-ir(buf: IR_Buffer, ir: IR) -> BOOL
    PRE: ir-p(ir) == T
    BODY: 
        slot = atomic_fetch_add(buf.size, 1)
        IF slot < buf.capacity THEN
            buf.data[slot] = ir
            RETURN T
        ELSE
            atomic_fetch_add(buf.overflow_count, 1)
            RETURN F
        ENDIF

OP clear-buffer(buf: IR_Buffer) -> VOID
    EFFECT: 
        atomic_store(buf.size, 0)
        atomic_store(buf.overflow_count, 0)
        memory_fence_release()
    POST: buf.size == 0 AND buf.overflow_count == 0

OP snapshot-buffer(buf: IR_Buffer) -> Array[IR]
    BODY:
        memory_fence_acquire()
        current_size = min(atomic_read(buf.size), buf.capacity)
        RETURN slice(buf.data, 0, current_size)

OP buffer-overflow-p(buf: IR_Buffer) -> BOOL
    BODY: RETURN atomic_read(buf.overflow_count) > 0

;; 4. Invariants
INV-PURITY: IR.role=OBSERVATION; !IR.decision_authority; !IR.semantic_meaning
INV-IMMUTABLE: post(make-ir) -> immutable(IR.fields)
INV-ORDERING: (A.pos < B.pos) -> emitted_before(A,B)
INV-BOUNDED: buf.size <= buf.capacity OR atomic_read(buf.overflow_count) > 0
INV-THREAD-SAFE: Concurrent push-ir calls populate distinct slots without data races
INV-REPLAY: Stream(S1)==Stream(S2) -> analyze(S1)==analyze(S2)

FLOW: LLM_BACKEND -> IR_CALLBACK -> IR_Buffer -> ANALYSIS/KERNEL