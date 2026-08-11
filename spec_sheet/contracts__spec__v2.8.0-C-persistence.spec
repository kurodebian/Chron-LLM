SPECIFICATION: Chron-LLM Kernel
VERSION: 2.8.0-C (Canonical Event Persistence Algebra)
STATUS: FROZEN & AUDITED (FINAL)

1. IDENTITY & AUTHORITY BOUNDARIES
   - CausalID     :: { epoch: Nat, sequence: Nat }  -> "Where & When" (因果線形座標)
   - AuthorityRef :: { id: Nat }                     -> "Why Valid" (検証権限・証明境界参照)
   - CausalID ∩ AuthorityRef = ∅ (型空間として完全分離)

2. PERSISTENCE TRANSFORMATIONS
   - History ctx p  ---[toEventStream]---> List CanonicalEventRecord
   - List CanonicalEventRecord ---[serializeRecords sctx]---> List WALFrame
   - List WALFrame ---[deserializeFrames]---> List CanonicalEventRecord (Candidate Generation)

3. PROOF THEOREMS & DERIVATIONS
   - WAL.RECORD_ROUNDTRIP.001          : deserializeFrames(serializeRecords(sctx, recs)) = recs
   - WAL.SERIALIZE_PRESERVES_LENGTH.001 : length(serialize(sctx, h)) = historyLength(h)
   - WAL.CAUSAL_ID_PRESERVATION.001     : (epoch, sequence) tuple projection mapped identically
     * Note: WAL.CAUSAL_ID_PRESERVATION.001 is a DERIVED THEOREM directly implied
             by WAL.RECORD_ROUNDTRIP.001 (C-1 -> C-3).

4. UNTRUSTED PERSISTENCE PRINCIPLE (v2.8.0-D Guard)
   - Abstract WALFrame is UNTRUSTED / NON-CANONICAL.
   - Raw WALFrame CANNOT be converted into History ctx p directly.
   - Replay Pipeline enforces:
       WALFrame --[deserialize]--> CanonicalEventRecord --[validate]--> ValidatedEventStream --[build]--> History ctx p