SPEC: Chron-LLM-Recovery-R1
State: Canonical:Immutable, Runtime:Mutable, Cache:Mutable, KVCache:Mutable, Context:Mutable
Input: {Canonical, MemoryRef}
Output: {Context}
Ops:
  Recover(Input) -> Output
  Recover = Replay(Canonical) -> ReconstructDerived -> ReconstructMemoryRef -> ReconstructWorking -> ResumeRuntime
  Allowed = {Destroy(Cache), Destroy(KVCache), Reconstruct(Prefill), Reconstruct(Derived), Reconstruct(Working), Resume}
  Forbidden = {Mutate(Canonical), Create(AuthoritativeEvent), Bypass(Commit)}
INV: Canonical.mutate == False
INV: Canonical.mutate -> Commit
INV: Recover == Deterministic
INV: Recover == ReplayCompatible
INV: Canonical.History == Recoverable
INV: Recover.Introduce(AuthoritativeInfo) == False