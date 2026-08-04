SPEC RuntimeR1: REFERENCE_IMPL
  STATUS = NON_NORMATIVE
  CONFORMS_TO = [AgentCausalityConstitution, PhaseA_F, OpSemanticsR1, ValPipelineR0, ArchV1_1, MemModelR1, SchedR1, WorldlineR1]

  TYPE RuntimeState:
    chat_loop: ChatLoop
    prompt_builder: PromptBuilder
    llm_backend: LLMBackend
    memory_integ: MemoryIntegration
    val_pipeline_integ: ValidationPipelineIntegration
    runtime_sched: RuntimeScheduling
    persist_integ: PersistenceIntegration

  OP compose(state: RuntimeState) -> ExecutableRuntime:
    PRE: state != NULL
    POST: returns executable instance composed of state.components
    INV: no_new_runtime_semantics