MODULE: Chron-LLM/Runtime
VER: Δ3-P1

TYPES:
  KernelState = { world_id: ID, health: Status, context: ContextObject }
  RuntimeEnv = { kernel: Kernel }

INV:
  Runtime.logic_state == {}
  Runtime.access(WAL | Graph | History | Event | Projection) == FALSE
  Kernel == SingleSourceOfTruth

OPS:
  init() -> RuntimeEnv:
    kernel = make-chron-kernel()
    return { kernel }

  main_loop(env: RuntimeEnv) -> Void:
    loop:
      input = console_read()
      env.kernel.submit_user_input(input)
      state = env.kernel.current_state()
      console_write(state.world_id, state.health)
      // P4: prompt = build_prompt(state.context)
      // P4: reply = llm_generate(prompt)
      // P4: env.kernel.submit_assistant_reply(reply)

APIS:
  make-chron-kernel() -> Kernel
  kernel.submit_user_input(str) -> Void
  kernel.current_state() -> KernelState
  kernel.submit_assistant_reply(str) -> Void

CONSTRAINTS:
  Runtime.knows(LLM) == TRUE
  Kernel.knows(LLM) == FALSE
  Runtime.knows(WAL | Graph | History) == FALSE