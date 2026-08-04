TYPE Phase = {0:prefill | 1:gen | 2:finalize}
TYPE IR = {ctx-id: ptr, pos: int, phase: Phase, token: int, score: float}
TYPE Stream = array[IR]
TYPE DivRes = {step: int, all-same: bool, p-same: float}

STATE *ir-stream*: Stream = []

OP init-bridge() -> void
  PRE: RuntimeReady
  POST: CallbackRegistered

OP ir-callback(ctx-id: ptr, pos: int, token: int, score: float, phase: Phase) -> void
  BODY: push(IR{ctx-id, pos, phase, token, score})
  INV-NON-INVASIVE: !mod(RuntimeState)

OP push(ir: IR) -> IR
  PRE: ir != null
  POST: *ir-stream* = append(*ir-stream*, [ir])

OP clear() -> void
  POST: *ir-stream* = []

OP extract-actions(s: Stream) -> array[IR]
  BODY: filter(ir in s | ir.phase == 1)
  INV-ORDERED: forall i < len(result)-1, result[i].pos <= result[i+1].pos

OP run-trial(prompt, n_trials) -> array[array[IR]]
  BODY:
    clear()
    res = []
    for _ in range(n_trials):
      run_generation(prompt)
      append(res, extract-actions(*ir-stream))
    return res

OP divergence-profile(trials: array[array[IR]]) -> array[DivRes]
  BODY: map(step_idx, trials | calc_divergence_metrics(step_idx, trials))

INV-IMMUTABLE: forall ir in Stream, !mod(ir.fields) post_creation
INV-APPEND-ONLY: len(Stream') >= len(Stream) unless clear() called
INV-DETERMINISTIC: run-trial(prompt, n) -> deterministic output given fixed seed/runtime
INV-COUPLING: AnalysisOps != CollectionOps