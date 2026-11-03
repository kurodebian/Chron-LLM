# Adoption run 2026-11-03 (MODE=RECLASSIFY_ADOPTION, continuation of P3)

P3 was BLOCKED: no adoption record existed. This run supplies the authorization layer
and re-derives claim statuses. Nothing beyond the adoption/ directory was written;
claim_ir_v2.jsonl, graph.jsonl, conflict_matrix.json, causal_resolution.json are
byte-identical (digests recorded in reclassification_report.json.inputs_digest and
re-verified against disk after the run).

## Records (8, all ADOPTED_LLM_PROVISIONAL, pending human ratification)
- ADR-001 ROOT-001 RECOVERY_AUTHORITY: bridge (fail-closed IN_DOUBT retention) adopted;
  wal.lisp PREPARED->ABORT at recovery start is a violation pending repair.
- ADR-002 ROOT-002 WAL_TAIL_POLICY: quarantine adopted; truncation forbidden without an
  adopted norm + evidence; wal.lisp truncation and test_cae_e2e.py assertion are violations
  pending repair (test != adoption).
- ADR-003 ROOT-003 DURABILITY_NORM: fdatasync-success linearization point adopted (local
  scope); Canonical-History precedence restricted until a join path exists.
- ADR-004 ROOT-004 SURFACE_DIVERGENCE: bridge is canonical authority; wal.lisp is legacy
  non-authoritative until aligned with ADR-001/002.
- ADR-005 CHAPTER_SEGMENTATION: full-chapter span (ledger pins) is chapter identity;
  pre-regen records stay labelled as covering pre-regen ranges.
- ADR-006 P1_SCOPE: pass stays scoped to the freeze-pinned 127-unit corpus; the 99
  unpinned chapters enter only after pinning + recorded freeze.
- ADR-007 INDEX_RE_RECORD: regenerated chapters_index.md adopted as index record
  (non-chapter sheet excluded); re-record provisional until ratification.
- ADR-008 ANCHOR_DIGEST_CONVENTION: LF-only convention adopted; three recorded anchor
  mismatches (mdsu0000, mdsu0014, mdsu0016) stay reported, not corrected.

## Gates (all pass)
- Every cited evidence path:line resolves on disk (verified before writing records;
  re-checked by reclassify_adoption.py GATE 1).
- Every effect target exists in the claim layer (GATE 2).
- Recomputed total = 3304 (asserted).
- conflict_matrix claims: zero remaining CONFLICT after adoption.

## Claim status deltas (5 effects applied)
- mdsu0033#dee9153c1e CONFLICT -> AGREED_VIA_LLM_ADJUDICATION
- mdsu0034#901f414c31 CONFLICT -> AGREED_VIA_LLM_ADJUDICATION
- mdsu0033#6ca9741022 VERIFIED -> VERIFIED_VIA_ADOPTED_NORM (the promotable rule)
- mdsu0035#81bdafbbc1 CONFLICT -> CLAIM_RESTRICTED_BY_ADOPTED_NORM
- mdsu0035#7296fb4b84 UNRESOLVED -> CLAIM_RESTRICTED_BY_ADOPTED_NORM

Final counts: MISSING_EVIDENCE 37, UNRESOLVED 3262, VERIFIED_VIA_ADOPTED_NORM 1,
AGREED_VIA_LLM_ADJUDICATION 2, CLAIM_RESTRICTED_BY_ADOPTED_NORM 2. Total 3304.
Plain VERIFIED count is 0 after promotion — VERIFIED_VIA_ADOPTED_NORM carries the
adoption provenance; the two AGREED claims in pre-run chapter_log records remain
discrepancies (text claims without claim_ir ids; left as-is).

## Resolution state
All four roots now RESOLVED_BY_LLM_ADJUDICATION_PROVISIONAL (see
causal_resolution_after_adoption.json; original causal_resolution.json untouched).
Adjudication method: LLM_ADJUDICATION, adjudicator hermes-agent,
model qwen3.8-flash-next-gyro-gyro-s, confidence per record.

## Pending (not done in this run)
- Human ratification of all 8 records (tier upgrade ADOPTED_LLM_PROVISIONAL -> RATIFIED_HUMAN).
- Code repairs: wal.lisp IN_DOUBT preservation, tail quarantine, Canonical-History join path,
  test_cae_e2e.py expectation reconciliation. Repairs are implementation work; they were not
  performed here because this run's scope was authorization + reclassification only.
- Pinning + freeze for the 4 unpinned chapter files before scope extension.
- Index/anchor re-recording after ratification.

VERIFICATION_IS_NOT_AUTHORIZATION. ARTIFACT_EXISTENCE != NORMATIVE_ADOPTION.
Provisional tier until human ratification.
