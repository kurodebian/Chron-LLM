TYPES: Event | Canonical | Projection | Graph | Summary | Prompt | Candidate | ValidationReport | KernelAction | RuntimeCommand | MemRef | Config
STATE: Canonical
FLOW: Input -> Event -> Commit -> Replay -> [Projection, Graph, Summary] -> PromptBuilder -> Backend -> Candidate -> Validation -> ValidationReport -> PolicyRouter -> KernelAction -> Kernel -> RuntimeCommand -> Runtime

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

OP PolicyRouter(ValidationReport) -> KernelAction
  INV: Mutate(State) == false

OP Kernel(KernelAction) -> RuntimeCommand
  INV: Deterministic(Kernel.transition)

OP Runtime(RuntimeCommand)

INV CanonicalWriteAccess: Mutate(Canonical) => Stage == Commit