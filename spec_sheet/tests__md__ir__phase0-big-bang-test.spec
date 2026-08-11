TYPES:
  TestMockProvider: { input_sequence: [Str], execution_log: [Action] }
  InferenceObservation: { raw_text: Str, finish_reason: Symbol, config: List, provider_metadata: List }
  WorldState: { causal_id: Str, parent_id: Str, retry_count: Int }
  Action: { physical_type: Symbol }
  Decision, Op

OPS:
  run_phase0_big_bang_test() -> Boolean
  fetch_observation(p: TestMockProvider, a: Action) -> InferenceObservation
  evaluate_observation(w: WorldState, o: InferenceObservation) -> Decision
  derive_ops(d: Decision) -> [Op]
  scheduler_step(w: WorldState, ops: [Op], id: Str) -> (WorldState, Action)

STATE:
  genesis: WorldState
  mock_provider: TestMockProvider
  current_world: WorldState
  iteration_count: Int

INIT:
  genesis.causal_id == "genesis"
  mock_provider.input_sequence == ["hello", "world"]
  mock_provider.execution_log == []
  iteration_count == 0

FLOWS:
  PipelineStep:
    evaluate_observation(current_world, obs) -> decision
    derive_ops(decision) -> ops
    scheduler_step(current_world, ops, gen_id) -> (new_world, action)
    fetch_observation(mock_provider, action) -> next_obs
    current_world = new_world

INV:
  INV-Loop-1: new_world.parent_id == current_world.causal_id
  INV-Loop-2: action.physical_type == :invoke-api
  INV-Final-1: final_world.causal_id == "node-2"
  INV-Final-2: final_world.retry_count == 2
  INV-Final-3: count(PipelineStep) == 2