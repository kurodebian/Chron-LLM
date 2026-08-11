PKG chronos-r0.trace : R0 | Stable

TYPE History = EXTERNAL

TYPE R0Trace = {
  user-text: String,
  prompt: String,
  raw: String,
  parsed: String,
  history-before: History,
  history-after: History,
  prompt-length: Int,
  response-length: Int,
  history-size-before: Int,
  history-size-after: Int
}

STATE *trace-log*: [R0Trace] = [] // Adjustable Vector

OP log-trace(t: R0Trace) -> t
  PRE True
  POST *trace-log* = [*trace-log*, t]
  INV RuntimeState == RuntimeState'
  COST O(1)

OP save-trace-to-file(path: String) -> Void
  PRE FileWritable(path)
  LET snap = coerce(*trace-log*, List)
  POST append_file(path, serialize(snap)) // S-Expression (~S)
  INV *trace-log* == *trace-log*'
  COST O(N)

OP dump-trace() -> Void
  PRE True
  POST print(stdout, format(*trace-log*))
  COST O(N)

INV ObservationOnly: TraceOps !-> Modify(RuntimeState | History | Session | Prompt)
INV ImmutableSnapshot: t.history-before == StateAt(t.capture_time)
INV SerializationFormat: Output =~ ReadableSExpression
INV SideEffectIsolation: save-trace-to-file uses snapshot to prevent race conditions