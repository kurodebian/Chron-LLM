MOD ir-callback : Physical->IR Bridge; DEPS=[ir, ir-stream, cffi]
SIG callback(ctx_id:Ptr, pos:Int, token:Int, score:Float, phase:Int)->Void
TRANSITION(callback): ir=make_ir(ctx_id=ctx_id, pos=pos, token=token, score=score, phase=phase); Stream->push_ir(Stream, ir)
INV(Determinism): callback(e1)==callback(e2)<=>e1==e2; INV(Lossless): ir.fields=={ctx_id, pos, token, score, phase}
INV(Isolation): Delta(State)={IR_Stream}; Kernel=Const; Canonical=Const; Runtime=Const
INV(Perf): Time=O(1); Mem=O(1); THREAD: Safe iff push_ir is Thread-Safe; ERROR: None