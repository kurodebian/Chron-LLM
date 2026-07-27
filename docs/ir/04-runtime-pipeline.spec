TYPES: Event | Canonical | Projection | Graph | Summary | Prompt | Candidate | ValidationReport | RuntimeRequest | RuntimeCommand | MemRef | Config
STATE: Canonical
FLOW: Input -> Event -> Commit -> Replay -> [Projection, Graph, Summary] -> PromptBuilder -> Backend -> Candidate -> Validation -> ValidationReport -> PolicyRouter -> RuntimeRequest -> Kernel -> RuntimeCommand -> Runtime

OP Commit(Event) -> Canonical'
  PRE: Event.authoritative == true
  POST: Canonical = Canonical + Event

OP Replay(Canonical) -> (Projection, Graph, Summary)
  INV: Deterministic(Replay)

OP PromptBuilder(Summary, Graph, MemRef, Config) -> Prompt

OP Backend(Prompt) -> Candidate
  INV: Authoritative(Backend.output) == false

OP Validation(Candidate) -> ValidationReport
  INV: Mutate(State) == false

OP PolicyRouter(ValidationReport) -> RuntimeRequest
  INV: Mutate(State) == false

OP Kernel(RuntimeRequest) -> RuntimeCommand
  INV: Deterministic(Kernel.transition)

OP Runtime(RuntimeCommand)

INV CanonicalWriteAccess: Mutate(Canonical) => Stage == Commit