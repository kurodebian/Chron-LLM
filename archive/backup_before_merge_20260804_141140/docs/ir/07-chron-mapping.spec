Candidate = proposalIR
ValidationReport = Δ0_Report
Validation = Δ0_Validator(proposalIR) -> ValidationReport (det)
PolicyRouter = Δ0_Policy(ValidationReport) -> KernelAction
Kernel = Runtime_Kernel
Commit = op:mutate(CanonicalState)
Event = WAL_Entry
History = WAL[]
Canonical = CanonicalState
DeferredQueue = DeferredProposalQ[]
Replay = replay(snapshot) -> Context (det)
Derived = snapshot | projection(Canonical)
Session = kernel_state
Context = replay_input
MemoryRef = RefStore
Config = RuntimeConfig
FaultEvent = FaultEvent
External = ExtStore
INV: write(CanonicalState) == Commit
INV: Replay(History) -> deterministic(Context)
INV: Derived ⊆ CanonicalState