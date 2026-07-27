MODULE ffi-bindings-mock.lisp : PhysicalLayerMock

TYPE mock-model = { path: STRING }
TYPE mock-ctx = { model: REF<mock-model>, context-size: INT, kv-past-tokens: INT }
TYPE sampler-hdl = SYMBOL

CONST SUCCESS_CODE = 0
CONST MOCK_TOKEN_ID = 42

OP my-llama-model-load(path: STRING) -> mock-model
  POST: RET.path == path; SIDE: PRINT("Load")

OP my-llama-model-free(model: REF<mock-model>) -> BOOL
  RET: TRUE

OP my-llama-model-get-vocab(model: REF<mock-model>) -> SYMBOL
  RET: :mock-vocab

OP my-llama-init(model: REF<mock-model>, ctx_size: INT) -> mock-ctx
  POST: RET.model == model; RET.context-size == ctx_size; RET.kv-past-tokens = 0

OP my-llama-free(ctx: REF<mock-ctx>) -> BOOL
  SIDE: PRINT("Free"); RET: TRUE

OP my-llama-eval(ctx: REF<mock-ctx>, tokens: ARRAY<INT>, count: INT, n_past: INT) -> INT
  EFFECT: ctx.kv-past-tokens = n_past + count; RET: SUCCESS_CODE

OP my-llama-kv-cache-seq-rm(ctx: REF<mock-ctx>, seq_id: INT, start: INT, end: INT) -> INT
  EFFECT: ctx.kv-past-tokens = start; RET: SUCCESS_CODE

OP my-llama-reset-kv(ctx: REF<mock-ctx>) -> BOOL
  EFFECT: ctx.kv-past-tokens = 0; SIDE: PRINT("Reset"); RET: TRUE

OP my-llama-tokenize(...) -> INT
  RET: 1

OP my-llama-token-to-piece(...) -> INT
  RET: 0

OP my-llama-is-eog(token_id: INT) -> BOOL
  RET: FALSE

OP my-sampler-init(temp: FLOAT, top_p: FLOAT) -> sampler-hdl
  RET: :mock-sampler

OP my-sampler-sample(sampler: sampler-hdl) -> INT
  RET: MOCK_TOKEN_ID

OP my-sampler-free(sampler: sampler-hdl) -> BOOL
  RET: TRUE

INV ABI_COMPATIBLE_WITH_LLAMA_CPP
INV ALL_OPS_COMPLEXITY == O(1)
INV NO_EXCEPTIONS_RAISED