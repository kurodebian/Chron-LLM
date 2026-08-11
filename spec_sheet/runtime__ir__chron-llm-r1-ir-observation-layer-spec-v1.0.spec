PKG chron-observation-layer
IMPORTS: [ir]

;; 1. Unified Return Types
TYPE DivRes = STRUCT {
    step: INT,
    all-same: BOOL,
    p-same: FLOAT
}

;; 2. State & Bridge Operations
STATE *observation-buffer*: ir.IR_Buffer

OP init-bridge(capacity: INT) -> VOID
    PRE: capacity > 0
    EFFECT: *observation-buffer* = ir.allocate-buffer(capacity)

OP ir-callback(ctx_id: ir.ID, pos: INT, phase: ir.Phase, token: ir.TOKEN_ID, score: FLOAT) -> VOID
    BODY: ir_obj = ir.make-ir(ctx_id, pos, phase, token, score)
          pushed = ir.push-ir(*observation-buffer*, ir_obj)
          IF !pushed THEN
              log_warning("IR_Buffer overflow: Token event dropped at pos", pos)
          ENDIF
    INV-NON-INVASIVE: !mod(RuntimeState)

;; 3. Standardized Extract Operations
OP extract-actions(buf: ir.IR_Buffer) -> Array[ir.IR]
    PRE: buf != NULL
    BODY: raw_data = ir.snapshot-buffer(buf)
          actions = filter(raw_data, lambda(x): ir.ir-phase(x) == 1) ;; 1 = GENERATION
          return sort(actions, key=ir.ir-pos)
    INV-ORDERED: forall i < len(result)-1: ir.ir-pos(result[i]) <= ir.ir-pos(result[i+1])

;; 4. Trial Execution & Divergence Analysis Operations
OP run-single-trial(prompt: STRING, seed: INT) -> Array[ir.IR]
    BODY: ir.clear-buffer(*observation-buffer*) ;; Enforce INV-S4 (RunStart Isolation)
          run_generation_with_seed(prompt, seed)
          IF ir.buffer-overflow-p(*observation-buffer*) THEN
              log_warning("Trial completed with buffer overflow; observations truncated.")
          ENDIF
          return extract-actions(*observation-buffer*)

OP run-trial(prompt: STRING, n_trials: INT, seed_base: INT) -> Array[Array[ir.IR]]
    PRE: n_trials > 0
    BODY: res = []
          for i in range(n_trials):
              trial_res = run-single-trial(prompt, seed_base + i)
              append(res, trial_res)
          return res

OP calc-divergence-at-step(step_idx: INT, trials: Array[Array[ir.IR]], n_trials: INT) -> DivRes
    BODY: tokens = [trials[t][step_idx].token for t in range(n_trials)]
          max_cnt = max(count(t, tokens) for t in unique(tokens))
          p = max_cnt / n_trials
          return DivRes{step: step_idx, all-same: (p == 1.0), p-same: p}

OP divergence-profile(prompt: STRING, n_trials: INT, seed_base: INT) -> Array[DivRes]
    PRE: n_trials > 0
    BODY: trials = run-trial(prompt, n_trials, seed_base)
          min_len = min(len(t) for t in trials)
          return [calc-divergence-at-step(s, trials, n_trials) for s in range(min_len)]

;; 5. Consolidated Invariants
INVARIANTS:
    INV-IMMUTABLE: forall ir in *observation-buffer*, !mod(ir.fields) post_creation
    INV-THREAD-SAFE: Concurrent ir-callback invocations are safe and lock-free
    INV-BOUNDED-NO-CRASH: Buffer overflows gracefully log without crashing LLM backend
    INV-APPEND-ONLY: len(*observation-buffer*') >= len(*observation-buffer*) unless clear-buffer() called
    INV-DETERMINISTIC: run-single-trial(prompt, seed) -> deterministic output
    INV-COUPLING: AnalysisOps != CollectionOps
    INV-OBS-ONLY: !write(Runtime|Kernel|Candidate|Canonical|Prompt)