MOD ffi-bindings.lisp : PhysicalLayer(HAL)
PKG chron-llm

TYPES:
  llama-token = int32
  ptr-model = pointer
  ptr-ctx = pointer
  ptr-vocab = pointer
  ptr-sampler = pointer
  event = struct(index:int, causal-id:any, kind:symbol, payload:any)

STATE:
  *n-past* : int32

EXPORTS(KERNEL_ABI):
  make-event -> event
  ev-index(event), ev-causal-id(event), ev-kind(event), ev-payload(event)

EXPORTS(RUNTIME_API):
  init-chron-llm, tokenize, prefill-prompt, generate
  start-delta3, start-delta3-stub

FFI_OPS:
  my-llama-model-load(path:str) -> ptr-model
  my-llama-init(m:ptr-model, n_ctx:int) -> ptr-ctx
  my-llama-model-get-vocab(m:ptr-model) -> ptr-vocab
  my-llama-eval(ctx:ptr-ctx, buf:[llama-token], count:int, n_past:int) -> int32
    POST ret=0 => success
  my-llama-token-to-piece(m:ptr-model, tok:id, buf:str[], len:int) -> int
  my-llama-tokenize(vocab:ptr-vocab, text:str, len:int, out:[llama-token], max_tok:int, add_special:bool, parse_special:bool) -> int
  my-llama-is-eog(ctx:ptr-ctx, tok:id) -> bool
  my-sampler-init(temp:f32, top_p:f32) -> ptr-sampler
  my-sampler-sample(samp:ptr-sampler, ctx:ptr-ctx) -> llama-token
  my-sampler-free(samp:ptr-sampler)
  my-llama-free(ctx:ptr-ctx)
  my-llama-model-free(m:ptr-model)
  my-llama-reset-kv(ctx:ptr-ctx)

INVARIANTS:
  INV stateless : Module holds only native pointers. No inference logic.
  INV abi_1to1 : FFI calls map 1:1 to C Wrapper -> llama.cpp.
  INV error_pass_through : Return values passed up; no local handling.
  INV mock_compat : ABI matches ffi-bindings-mock.lisp.

LIFECYCLE_SEQ:
  LoadModel -> CreateCtx -> Tokenize -> Prefill(Eval) -> Generate(Sample+Eval)* -> Reset(opt) -> FreeCtx -> FreeModel