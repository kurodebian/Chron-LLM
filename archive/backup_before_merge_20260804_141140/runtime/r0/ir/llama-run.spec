PKG chronos-r0.llama
EXPORT [llama-run]

TYPE Prompt = String
TYPE Response = String
TYPE ProcRes = {out: String, err: String}

CONST BIN_PATH = "/home/junu/lisp-os/llama.cpp/build/bin/llama-completion"
CONST MODEL_PATH = "/home/junu/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
CONST SYS_PROMPT = "あなたは日本語で丁寧で簡潔に答えるアシスタントです。"
CONST MAX_TOK = 128

OP llama-run(p: Prompt) -> Response
  PRE: p is String
  POST: returns raw stdout; no formatting applied
  BODY:
    args = [BIN_PATH, MODEL_PATH, "--single-turn", "--n-predict", str(MAX_TOK), "--system-prompt", SYS_PROMPT, "-p", p]
    res: ProcRes = uiop:run-program(args, :wait t, :output :string, :error-output :string, :ignore-error-status t)
    return res.out

INV STATELESS: Module holds no state between calls
INV SYNC: Execution is blocking until completion
INV NO_EXCEPTION_ON_FAIL: Process exit codes do not raise exceptions
INV ISOLATION: Interface strictly maps Prompt -> Response