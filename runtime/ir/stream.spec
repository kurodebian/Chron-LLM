PKG ir-stream : USES(cl, ir)

TYPE IR : Observation(token, pos, phase)
TYPE Stream : Array[IR] { adjustable=T, fill-pointer=0 }

STATE:
  *ir-stream* : Stream = []

OPS:
  push-ir(ir: IR) -> IR
    PRE: ir-p(ir) == T
    EFFECT: vector-push-extend(ir, *ir-stream*)
    POST: last(*ir-stream*) == ir; len' == len + 1

  clear-ir-stream() -> Stream
    EFFECT: *ir-stream* = make-array(0, adjustable=T, fill-pointer=0)
    POST: len(*ir-stream*) == 0

INVARIANTS:
  INV-S1 (Ordering): push(A).t < push(B).t => index(A) < index(B)
  INV-S2 (Ephemeral): *ir-stream* != Truth; Authority=History/WAL
  INV-S3 (Neutrality): !mutate(IR); !interpret(IR)
  INV-S4 (Isolation): RunStart -> clear-ir-stream()

LIFECYCLE:
  Clear -> Decode { emit(IR) -> push-ir(IR) } -> Analyze(Stream) -> Clear

THREADING: UNSAFE(GlobalMutable(*ir-stream*))