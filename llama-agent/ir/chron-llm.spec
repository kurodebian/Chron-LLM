TYPES:
Event: header:Header, payload:PropertyList [Persistent]
Header: index:WALPos, clock:LogicalClock, node-id:UUID, causal-id:WorldlineID, kind:Symbol [ManagedBy:Kernel]
Node: id:ID, kind:Symbol, content:Any, parent:NodeRef, worldline:WorldlineID, status:Active|Fault [RuntimeObject]
Context: model:ModelPtr, ctx:LLamaCtx, n-past:Int
Sampler: temp:Float, top-p:Float

STATE:
*n-past*:Int = 0

OPS:
init-chron-llm(path:String, size:Int) -> Context
  PRE: path != NULL
  POST: Context.n-past = 0

tokenize(model:ModelPtr, text:String) -> List<Token>
  ALGO: UTF8(text) -> Pass1(Size) -> Pass2(Tokens)
  ERR: len(Tokens) <= 0

prefill-prompt(ctx:Context, tokens:List<Token>) -> Void
  EXEC: llama_eval(ctx.ctx, tokens)
  POST: ctx.n-past += len(tokens)

generate(ctx:Context, model:ModelPtr, temp:Float, top-p:Float, max:Int) -> String
  PRE: ctx.n-past == len(PromptTokens)
  EXEC:
    sampler = create-sampler(temp, top-p)
    buf = []
    LOOP max:
      id = sample(sampler, ctx.ctx)
      IF my-llama-is-eog(id) BREAK
      buf += print-token-stream(model, id)
      llama_eval(ctx.ctx, [id])
      ctx.n-past++
    free(sampler)
  POST: ctx.n-past == len(PromptTokens) + len(buf)
  RET: UTF8(buf)

print-token-stream(model:ModelPtr, id:Token) -> ByteVector
  EXEC: Token(id) -> Piece -> Bytes -> Console
  RET: Bytes

INV:
INV(Event.Header): Writer == Kernel
INV(Event.Payload): Writer == User
INV(LLM.Runtime): Input == Prompt, Output == Text, Knowledge == {}
INV(Sampler): Lifecycle == {Create -> Use -> Free}
INV(n-past): Start == PromptLen, End == PromptLen + GenLen