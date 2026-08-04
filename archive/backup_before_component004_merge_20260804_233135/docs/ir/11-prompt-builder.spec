State: Canonical
State: DerivedContext
Type: Prompt, Config, Summary, Graph, MemoryRef
Set: Excluded = {Observation, FaultEvent, DetectorOutput, RuntimeMetric}

Flow: Canonical -> Replay -> DerivedContext -> {Summary, Graph, MemoryRef}
Op: Construct(Summary, Graph, MemoryRef, Config) -> Prompt

INV: Deterministic(Construct)
INV: Immutable(Canonical)
INV: Prompt !contains Excluded
INV: Construct depends_on {Replay, Config}