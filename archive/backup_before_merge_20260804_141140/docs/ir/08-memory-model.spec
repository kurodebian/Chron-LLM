ShortTermMemory := History[last N Events]
LongTermMemory := PersistentStore
CanonicalMemory := AuthoritativeState

MemoryRef := {short-term | long-term | canonical}

memory-read() -> Prompt : !mut(State), uses(Derived.MemoryRef)
Commit(Event e) -> CanonicalMemory' = CanonicalMemory + {e}, MemoryRef.auth' = update(CanonicalMemory')
recover(ReplayCtx, MemoryRef) -> PrefillState

INV CanonicalMemory.writer == Commit
INV MemoryRef.authoritative.writer == Commit
INV MemoryRef.is_deterministic == true
INV Replay.requires(MemoryRef) == true