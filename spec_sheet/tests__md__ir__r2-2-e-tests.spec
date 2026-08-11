PKG chron-llm/r2-2-e-tests
IMPORT evaluate-observation, derive-ops FROM chron-llm/r2-2-e

TYPE Obs = { finish-reason: Sym | raw-text: Str | error-info: Any }
TYPE Decision = { inference-decision-type: Sym }
TYPE Policy = List[Rule]
TYPE Rule = { cond: Sym -> act: Sym, params: Any }

FN %make-stop-observation() -> Obs: { finish-reason=:stop, raw-text="ok", error-info=NIL }
FN %make-timeout-observation() -> Obs: { finish-reason=:timeout, raw-text=NIL, error-info={type=:timeout} }

FN run-r2-2-e-verification() -> Bool | Error
  SIDE-EFFECTS: Print("E-Tier verification passed.") ON SUCCESS
  BODY:
    // E1 Determinism
    ws = FixedState; obs = %make-stop-observation(); pol = []
    d1 = evaluate-observation(ws, obs, pol)
    d2 = evaluate-observation(ws, obs, pol)
    INV EQ(d1.inference-decision-type, d2.inference-decision-type)

    // E2 Purity
    ws = [(:counter 10)]; obs = %make-stop-observation(); pol = NIL; ws_pre = COPY(ws)
    _ = evaluate-observation(ws, obs, pol)
    INV EQUAL(ws, ws_pre)

    // E3 Policy Enforcement
    pol = [{cond=:timeout -> act=:retry}]; obs = %make-timeout-observation(); ws = NIL
    d = evaluate-observation(ws, obs, pol)
    INV EQ(d.inference-decision-type, :retry)

    // E4 Safety Default
    pol = NIL; obs = {finish-reason=:unknown-error}; ws = NIL
    d = evaluate-observation(ws, obs, pol)
    INV EQ(d.inference-decision-type, :abort)

    // E5 Derivation Stability
    d = evaluate-observation(NIL, %make-stop-observation(), NIL)
    ops1 = derive-ops(d); ops2 = derive-ops(d)
    INV EQUAL(ops1, ops2)

    RETURN T