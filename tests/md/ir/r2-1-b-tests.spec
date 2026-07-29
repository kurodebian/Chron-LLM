pkg: chron-llm/r2-1-b
type inference-observation = {raw-text:String|nil, prompt-text:String, usage-tokens:[], token-count:Int, finish-reason:Symbol, config:PList, provider-metadata:PList, error-info:PList|nil}

op %make-test-observation(raw-text, prompt-text, usage-tokens, token-count, finish-reason, config, provider-metadata, error-info) -> inference-observation
op %register-basic-success-scenario() -> obs{id=:mock-success-basic, finish-reason=:stop, raw-text:"mock-success-response", config.temp:0.0}
op %register-timeout-scenario() -> obs{id=:mock-openai-timeout, finish-reason=:timeout, raw-text:nil, error-info.type=:timeout}

op run-r2-1-b-verification() -> t | signal(assert)
  pre: mock_registry.clear()
  exec: [D1..D6]
  post_success: print("D-Tier verification passed.")

ctx execute-inference(mode=:mock)

D1:
  setup: %register-basic-success-scenario()
  INV(obs != nil && obs.finish-reason == :stop && obs.raw-text == "mock-success-response")

D2:
  setup: %register-timeout-scenario()
  INV(obs.finish-reason == :timeout && obs.error-info.msg == "Provider request timeout.")

D3:
  setup: %register-basic-success-scenario()
  cfg = obs.config; mutate(cfg.temp, 99.0)
  INV(obs.config.temp == 0.0)

D4:
  setup: %register-basic-success-scenario()
  meta-a = obs.provider-metadata; meta-b = obs.provider-metadata
  mutate(meta-a.model, "changed")
  INV(meta-b.model == "mock-model" && obs.provider-metadata.model == "mock-model")

D5:
  setup: %register-basic-success-scenario()
  obs1 = execute-inference(provider=:provider-a); obs2 = execute-inference(provider=:provider-b)
  INV(obs1.raw-text == obs2.raw-text && obs1.finish-reason == obs2.finish-reason)

D6:
  setup: %register-basic-success-scenario()
  obs1 = execute-inference(provider=:provider-one); obs2 = execute-inference(provider=[arbitrary])
  INV(obs1.raw-text == obs2.raw-text)