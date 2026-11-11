# Ratification run 2026-11-11 (MODE=RATIFY_ADOPTION)

Human ratification of all 8 adoption records, continuing the 2026-11-03
RECLASSIFY_ADOPTION run. Authorization act recorded verbatim:

裁定 (逐語): 「全て批准 (8件 → RATIFIED_HUMAN)」
裁定表明: 2026-11-11、セッション内裁定フォーム (単一選択)。裁定者: junu (user)。

## Tier upgrade
- ADR-001..008: ADOPTED_LLM_PROVISIONAL -> RATIFIED_HUMAN.
- Each record carries a `ratification` block (method HUMAN_RATIFICATION, ratifier,
  date, verbatim adjudication, upgraded_from).
- adoption_record.schema.json status enum already permitted RATIFIED_HUMAN;
  every record re-validated against the schema after the flip.

## Gates
- Immutable layers byte-identical before/after (digests unchanged on disk):
  claim_ir_v2.jsonl c488f2a0…, causal_graph.json bf072281…,
  conflict_matrix.json 39e2c902…, causal_resolution.json 0d89252b…
  (causal_resolution.json is the ORIGINAL file; the derived
  causal_resolution_after_adoption.json is regenerated below.)
- reclassify_adoption.py re-run: GATE 1 (cited evidence resolves on disk) and
  GATE 2 (effect targets exist) pass; total 3304 asserted; conflicts remaining
  unadjudicated = 0. Claim statuses unchanged by ratification — same 5 deltas,
  same counts (MISSING_EVIDENCE 37, UNRESOLVED 3262, VERIFIED_VIA_ADOPTED_NORM 1,
  AGREED_VIA_LLM_ADJUDICATION 2, CLAIM_RESTRICTED_BY_ADOPTED_NORM 2).
- Derived artifacts regenerated with ratification provenance:
  reclassification_report.json (provenance tag RATIFIED_HUMAN per applied effect;
  inputs_digest.adoption_records_sha256 now cf6a1a30…) and
  causal_resolution_after_adoption.json (roots now
  RESOLVED_BY_LLM_ADJUDICATION_RATIFIED, ratification blocks attached).

## Effect on pending items (from adoption_run_note_2026-11-03.md)
- Human ratification: DONE (this run).
- Code repairs (wal.lisp IN_DOUBT preservation, tail quarantine, Canonical-History
  join path, test_cae_e2e.py reconciliation): authorization gate cleared; repairs
  remain implementation work queued as a separate track — not performed here.
- Pinning + freeze for unpinned chapter files: prerequisite satisfied in the same
  session by CORPUS-FREEZE-MDSHEETS-02 (see ledger/corpus_manifest_mdsheets_ext.json);
  scope extension per ratified ADR-006 may proceed after the pass is re-run on the
  extension units.
- Index re-record: adopted regenerated chapters_index.md (ADR-007) re-recorded with
  live digest 769645903bb7fc6e… in the extension manifest (record, this run).
- Anchor mismatches (mdsu0000, mdsu0014, mdsu0016): ADR-008 LF-only convention
  ratified; mismatches stay reported, not corrected.

Nothing outside results/impl_verification/adoption/ was written by ratify_adoption.py
and reclassify_adoption.py.

VERIFICATION_IS_NOT_AUTHORIZATION. ARTIFACT_EXISTENCE != NORMATIVE_ADOPTION.
Tier is now RATIFIED_HUMAN because the human adjudicated — not because artifacts exist.
