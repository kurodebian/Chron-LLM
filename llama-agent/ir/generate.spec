MODULE run-llm-generation-with-sensors(model-path, prompt, max-tokens, wal) -> Result(:eos|:fault|NIL)
TYPES: Status=:ok|:warning|:fault; ImmuneRes={status:Status, entropy:Float}; Config={temp:0.7, topp:0.9}
STATE S={model:Hdl, ctx:Ctxt, sampler:Smp, n_past:Int, step:Int}
INIT: init-chron-llm() -> {S.model, S.ctx}; S.sampler = my-sampler-init(Config); prefill-prompt(S.ctx, tokenize(prompt)); S.n_past=0; S.step=1
LOOP WHILE S.step <= max-tokens: tid=my-sampler-sample(S.sampler); IF my-llama-is-eog(tid): RETURN :eos; print(my-llama-token-to-piece(tid)); ir=check-immune-status(); IF ir.status==:fault OR ir.entropy>20: FAULT_RECOVERY() -> :fault; IF ir.status==:warning AND ir.entropy>5: log("Warn"); my-llama-eval(S.ctx, tid); S.n_past++; S.step++
RETURN NIL
FAULT_RECOVERY(): my-llama-reset-kv(S.ctx); rollback-stage(wal); cleanup(); RETURN :fault
CLEANUP(unwind): my-sampler-free(S.sampler); my-llama-free(S.ctx); my-llama-model-free(S.model)
INV: Fault -> !Commit; Rollback -> Stage.Empty; Fault -> KV.Reset