# Per-chapter implementation verification protocol

Established 2026-10-29 (UTC). Framework inherited from STEP-1 (the framework IS chapter 1's normative content).

Scope of one pass per chapter N:

1. READ the chapter slice via the ledger line range (SHA-pinned; never read whole giant files).
2. RUN the procedure the chapter prescribes, exactly as prescribed (read-only; no test runs or file changes unless the chapter itself prescribes them).
3. RECONCILE live results against claims recorded in the chapter body.
4. CLASSIFY every claim into the four-class framework (chapter-1 canon):
   AGREED / VERIFIED / UNRESOLVED / OUT_OF_SCOPE.
   - VERIFIED only from reconciliation against live assets, never from identification alone.
   - Time-bound historical claims (snapshots at the time) are UNRESOLVED unless re-provable; recorded as historical, not silently re-verified.
   - Semantic content checks (e.g. DG-01..DG-05 alignment) stay UNRESOLVED until the content is actually read on that chapter's turn.
5. APPEND one evidence line to chapter_log.jsonl (provenance: chapter id, source file + line range, recorded digest, live digest, classifications, UTC timestamp).

Disciplines (non-negotiable):
- MISSING_EVIDENCE != PASS
- VERIFICATION_IS_NOT_AUTHORIZATION
- Corpus read-only; artifacts under results/impl_verification/ only.

Gate per chapter: PASS only when all chapter claims received an explicit classification with evidence. Otherwise the chapter remains OPEN, not optimistic.
