Type Event
Type Execution { state: Working | Faulted, causalOrder: LamportClock, retryCount: Int }

State IngressQueue: Queue<Event> []
State ReadyQueue: Queue<Execution> []
State IsolatedQueue: Queue<Execution> []

Config maxRetry = 3
Config maxPenaltyRetry = 2

Op Schedule(ReadyQueue) -> Sort(e.causalOrder ASC, FIFO)

Op retry(exec: Execution) -> if exec.retryCount < maxRetry then Requeue(exec) else Abort()

Op retry-with-penalty(exec: Execution) -> Pre(exec.state == Working) -> if exec.retryCount < maxPenaltyRetry then { exec.temp += 0.2; exec.topP -= 0.1 } -> CanonicalState = Immutable -> Requeue(exec) else Abort()

Op abort(event: FaultEvent) -> Terminate(Branch)

INV Schedule == Deterministic(CanonicalState)
INV Retry -> !Mutate(CanonicalState)
INV NormalDialogueExecution !Depends(IsolatedQueue)
INV FaultIsolation -> !Affect(NormalDialogueReplay)