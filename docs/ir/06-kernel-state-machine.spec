TYPES:
KernelState = {Canonical:{History:[Event], MemoryRef, LamportClock:int}, DeferredQueue:[Candidate], Working}
RuntimeCommand = proceed | discard | sleep | regenerate | regenerate-with-penalty | terminate
Event = {intent:{memory-write|recover}}

KERNEL_FUNC:
Kernel(req:RuntimeRequest, s:KernelState, cfg:Config) -> (s':KernelState, cmd:RuntimeCommand)

TRANSITIONS:
req.type=commit -> events:=Map(Working.Candidate); Canonical.History+=events; if exists(e in events|e.intent in {memory-write,recover})->Canonical.MemoryRef++; Canonical.LamportClock++; Working:=Init(); cmd=proceed
req.type=reject -> Working:=Init(); cmd=discard
req.type=defer -> DeferredQueue.enqueue(Working.Candidate); cmd=sleep
req.type=retry -> cmd=regenerate
req.type=retry-penalty -> Working.Policy:=ApplyPenalty(Working.Policy, cfg.penalty_policy); cmd=regenerate-with-penalty
req.type=abort -> Emit(FaultEvent); cmd=terminate

DEFERRED_QUEUE:
WakeupTrigger = (Canonical.LamportClock' > Canonical.LamportClock)

INVARIANTS:
INV1: Mutate(Canonical) => op==Commit
INV2: RuntimeCommand !-> Mutate(Canonical)
INV3: Owner(DeferredQueue)==Kernel
INV4: Kernel !-> Invoke(Backend)
INV5: Deterministic(Kernel(req,s,cfg))