// ============================================================================
// CHRON-LLM PHASE 3: LLAMA AGENT / GENERATE EXECUTION LAYER SPECIFICATION
// Version: v1.0 (SSOT Standardization)
// Domain: LLM Generation Loop, Sensor Monitoring, and Fault Recovery Architecture
// ============================================================================

PKG: chron-llm-llama-agent-generate-v1.0

TYPES:
  Status = Enum{:ok, :warning, :fault}
  ImmuneRes = { status:Status, entropy:F32 }
  GenConfig = { temp:F32, top_p:F32, max_tokens:U32 }
  LlamaModelHdl = Ref<Hdl>
  LlamaCtxt = Ref<Ctxt>
  LlamaSampler = Ref<Smp>
  KernelRef = Ref<Kernel>
  GenState = { model:LlamaModelHdl, ctx:LlamaCtxt, sampler:LlamaSampler, n_past:U32, step:U32 }
  GenResult = Enum{:eos, :fault, :nil}

INVARIANTS:
  INV-1 (Fault-No-Commit)    : ir.status == :fault IMPLIES NOT committed(kernel)
  INV-2 (Rollback-Stage-Empty): rolled_back(kernel) IMPLIES stage_is_empty()
  INV-3 (Fault-KV-Reset)     : ir.status == :fault IMPLIES kv_cache_reset(ctx)
  INV-4 (Step-Limit-Bound)   : s.step <= cfg.max_tokens + 1

OPERATIONS:
  init-chron-llm(model_path:Str, prompt:Str, cfg:GenConfig) -> GenState
    POST: s.n_past == 0 AND s.step == 1

  PURE check-immune-status() -> ImmuneRes

  fault-recovery!(s:GenState, kernel:KernelRef) -> GenResult
    PRE: ir.status == :fault OR ir.entropy > 20.0
    SEQ: my-llama-reset-kv(s.ctx); kernel-rollback!(kernel); cleanup!(s)
    POST: RESULT == :fault

  cleanup!(s:GenState)
    SEQ: my-sampler-free(s.sampler); my-llama-free(s.ctx); my-llama-model-free(s.model)

  run-llm-generation-with-sensors(model_path:Str, prompt:Str, max_tokens:U32, kernel:KernelRef) -> GenResult
    PRE: max_tokens > 0
    LOGIC: Loop step sampling while s.step <= max_tokens; check-immune-status(); trigger fault-recovery! if fault.
