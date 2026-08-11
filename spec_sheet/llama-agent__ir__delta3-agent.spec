TYPES:
  Str, Int, Float, Bool, Void
  AgentState = { goal: Str, context: Str, todo: [Str], issues: [Str] }
  Env = { n_past: Int, sys_prompt: Str, agent_state: AgentState }

GLOBALS:
  ENV: Env
  THRESHOLD_RESET: Float = 0.85

INIT:
  ENV.n_past = 0
  ENV.sys_prompt = "You are excellent engineer AI Δ3"
  ENV.agent_state.goal = "Reset mechanism test"
  ENV.agent_state.context = "Test env"
  ENV.agent_state.todo = ["REPL check"]
  ENV.agent_state.issues = []

OPS:
  my_llama_reset_kv() -> Void:
    // Physical KV Clear (Stub)

  get_kv_usage() -> Float:
    return 0.86 // Stub

  should_trigger_reset_p() -> Bool:
    return get_kv_usage() >= THRESHOLD_RESET

  format_agent_state_to_prompt(s: AgentState) -> Str:
    return concat("Goal\n", s.goal, "\nTODO\n", join("\n", s.todo))

  my_llama_tokenize(t: Str) -> [Int]:
    return [101, 102, 103] // Stub

  my_llama_decode(tokens: [Int]) -> Void:
    ENV.n_past += len(tokens)
    print("Decode", tokens)

  update_agent_state_from_summary(summary: Str) -> Void:
    prepend(ENV.agent_state.todo, "Transition based on summary") // Stub

CORE_PROCEDURES:
  perform_stateful_reset() -> Void:
    print("Reset Sequence")
    my_llama_reset_kv()
    ENV.n_past = 0
    
    // Inject Identity
    tokens_id = my_llama_tokenize(ENV.sys_prompt)
    my_llama_decode(tokens_id)

    // Inject Agent State
    prompt_state = format_agent_state_to_prompt(ENV.agent_state)
    tokens_state = my_llama_tokenize(prompt_state)
    my_llama_decode(tokens_state)

    print("Memory Rebuild Complete")

  agent_main_loop() -> Void:
    print("Δ3 Start")
    loop:
      cmd = read_input()
      
      if cmd == ":quit": break
      if cmd == ":reset": perform_stateful_reset(); continue

      // Normal Generation (Stub)
      response = my_llama_generate(cmd) 
      update_agent_state_from_summary(response)

      if should_trigger_reset_p():
        perform_stateful_reset()

INVARIANTS:
  INV_RESET_IDENTITY: After(perform_stateful_reset), ENV.sys_prompt == Before(ENV.sys_prompt)
  INV_RESET_STATE: After(perform_stateful_reset), ENV.agent_state.goal/context/todo/issues preserved (modulo summary updates)
  INV_KV_MEMORY_SEP: KV Cache != AgentState; Reset(KV) -> Restore(AgentState)