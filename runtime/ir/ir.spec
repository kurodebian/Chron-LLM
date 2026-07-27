PKG ir
EXPORTS [make-ir, ir-p, ir-ctx-id, ir-pos, ir-phase, ir-token, ir-score]

TYPE Phase = {0:PREFILL | 1:GENERATION | 2:FINALIZE}
TYPE IR = STRUCT { ctx-id:ID; pos:INT; phase:Phase; token:TOKEN_ID; score:FLOAT }
TYPE Stream = [IR]

OP make-ir(ctx-id:ID, pos:INT, phase:Phase, token:TOKEN_ID, score:FLOAT) -> IR
OP ir-p(x) -> BOOL
ACC ir-ctx-id(IR) -> ID
ACC ir-pos(IR) -> INT
ACC ir-phase(IR) -> Phase
ACC ir-token(IR) -> TOKEN_ID
ACC ir-score(IR) -> FLOAT

INV-PURITY: IR.role=OBSERVATION; !IR.decision_authority; !IR.semantic_meaning
INV-IMMUTABLE: post(make-ir) -> immutable(IR.fields)
INV-ORDERING: (A.pos < B.pos) -> emitted_before(A,B)
INV-REPLAY: Stream(S1)==Stream(S2) -> analyze(S1)==analyze(S2)

FLOW: LLM_BACKEND -> IR_CALLBACK -> IR_STREAM -> ANALYSIS/KERNEL