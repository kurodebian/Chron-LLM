PKG ir-stream : USES(ir)

;; Backward-compatibility wrapper for ir-stream package
TYPE Stream = ir.IR_Buffer

OPS:
    push-ir(buf: Stream, ir: ir.IR) -> BOOL => ir.push-ir(buf, ir)
    clear-ir-stream(buf: Stream) -> VOID => ir.clear-buffer(buf)

INVARIANTS:
    INV-S1 (Ordering): Enforced by ir.IR_Buffer atomic append
    INV-S2 (Ephemeral): *ir-stream* != Truth; Authority=History/WAL
    INV-S3 (Neutrality): !mutate(IR); !interpret(IR)
    INV-S4 (Isolation): RunStart -> clear-buffer()