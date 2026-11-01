# State note — run resumed 2026-10-30 (read-only)

Status: RECORD OF RUN STATE (not adoption, not adjudication). No corpus file, generator,
ledger, adjudication, or test asset was modified in this run. Three evidence records
(STEP-29, STEP-30, STEP-31) appended to chapter_log.jsonl; they are the first records
written under the full protocol shape (claim-level classification + evidence).

## Run state
- P1 ledger scope: 127 units (md_sheets/1-74.md 77, 75-99.md 25, 100-124.md 25).
- Logged before this run: 31 chapters; after: 34. Remaining in P1 scope: 93, next STEP-32.
- Corpus re-hash against CORPUS-FREEZE-MDSHEETS-01:
  - md_sheets/1-74.md 7205b646... MATCH
  - md_sheets/75-99.md e5f87195... MATCH
  - md_sheets/100-124.md a51afdd7... MATCH
  - md_sheets/chapters_index.md: DRIFT — recorded ea49cecc..., live 769645903...
    (uncommitted regen, 2026-10-29 22:25:38; generator change adds --exclude, which
    excludes md_sheets/chron_os_architecture_summary.md, a non-chapter sheet, from the index)
- Unit pins: 127/127 unit text digests reproduce from live corpus bytes. Anchor-line
  digests: 124/127 match as stored; 3 differ only under newline interpretation
  (mdsu0000, mdsu0014, mdsu0016) — the corpus is LF-only, so the recorded digests for
  those three units were computed with a trailing-newline convention that does not
  reproduce from a line-by-line read. Reported as observed, not corrected.
- Corpus-wide H1 scan: interior-H1 units exist (e.g. mdsu0014 584-686 contains H1 at
  lines 584, 655, 670). Chapter identity is therefore not defined by a single H1;
  this must be adjudicated before further range-pinning decisions.

## Log-shape defect (observed, not corrected)
- 31 pre-existing records disagree with ledger pins on the `lines` field (31/31).
  Example: STEP-28 logged 4982-5269, pin is mdsu0031 4775-5064; STEP-30 logged 5270-5416,
  pin is mdsu0033 5314-5542.
- All 31 pre-existing records' recorded digests reproduce from live bytes *when the
  logged range is used*, so the disagreement is a segmentation-convention change, not
  corpus drift: the pre-regen index split chapters at interior H1 headings.
- New records from this run use ledger pin ranges; the log now mixes two segmentation
  conventions. Adjudication required: which convention governs chapter identity going
  forward, and whether pre-regen records are re-labelled as covering pre-regen units.

## Implementation-surface findings (from this run's read-only checks)
1. runtime/phase-d/wal.lisp:250-252 — recovery unconditionally truncates the WAL file
   to the last scanned valid offset. tests/test_cae_e2e.py:205-235 asserts that
   behaviour as expected. STEP-31 §31.4 prohibits truncation without an explicit storage
   norm; §31.9 declares Storage Contract and WAL Tail Policy unresolved. CONTRADICTION.
2. runtime/phase-d/wal.lisp:259-271 — every PREPARED txid is resolved to ABORT at
   recovery start; no IN_DOUBT state exists. STEP-30 CON-INV-07 and STEP-31 FAC-INV-06
   forbid guessing an IN_DOUBT outcome. CONTRADICTION.
3. chron-llm-causal/src/causal_kernel/bridge/wal_triad_bridge.py:19,170,199-211 —
   PREPARED kept as IN_DOUBT, isolated, never canonical, fail-closed after integrity
   violation. This surface satisfies the invariants that wal.lisp contradicts; the two
   surfaces encode opposite recovery rules and need one adjudicated recovery authority.
4. runtime/phase-d/wal.lisp:107-117 — durability is defined as fdatasync success.
   STEP-30 declares the durability definition unresolved. NORM_GAP (implementation
   asserts an unadopted storage norm).
5. No project code encodes POL-INV-*, CON-INV-*, FAC-INV-* tokens, transaction-index
   precedence, or serialization-slot logic (0 live hits). Design-only status confirmed.

## Scope gap requiring adjudication
- The freeze manifest covers 3 chapter files (127 units). md_sheets contains 7 chapter
  files and 226 H1 chapters; 99 chapters (125-149.md, 150-174.md, 175-199.md, 200-218.md)
  are unpinned and outside the recorded freeze. Whether the pass extends to them, or
  they must be pinned and frozen first, is an open decision.

## Run completion 2026-10-30 (phases P0-P3, read-only)

Shape defects recorded before proceeding (not silently fixed):
- chapter_log.jsonl had two record shapes and no claim-level classification+evidence pairs;
  the 31 pre-run records were left as-is and are reported as nonconformant.
- Post-regen records omitted unresolved_segments; the ledger carries no unresolved field, so
  segments are retained from the live chapter text in new records.
- Pre-regen records recorded digests for a different segmentation (interior-H1 split).
- Adjudication taken for this run (pending adoption): full-chapter span is the unit of chapter
  identity going forward; pre-regen records stay labelled as covering pre-regen ranges.

P1: all 127 recorded units run — re-hash from live bytes, claim lines read, read-only scan of
runtime/, llama-agent/, chron-llm-causal/, tests/, unresolved segments retained.
127/127 unit digests reproduce from live corpus bytes. 3,304 claims across 127 records;
3,067 UNRESOLVED / 192 VERIFIED / 2 AGREED (rule R: pin identity VERIFIED; normative design
claims UNRESOLVED as design candidates with no implementation encoding shown; keyword hits in
code are concept presence only, never semantic equivalence; test-design VERIFIED only as
design-only, no execution evidence).
Gate: PASS for the 96 records written in this run (every claim carries classification+evidence);
not retroactively applied to the 31 pre-run records.

P2: independent recheck recomputed from the ledger pins, live corpus bytes, and the log —
127 units reconstructed, exactly one record per unit, zero digest mismatches, zero unresolved
segments that fail to reproduce from live bytes, 23 evidence paths all present. Corpus freeze:
3 chapter files match; chapters_index.md drifts (recorded ea49cecc, live 595a41b66c) — the
uncommitted regen, re-recording requires adoption.
P2 could not re-run the earlier phases: no P0 artifacts and no P1 execution results exist in
the repo for the pre-run records. Reported as missing, not inferred.
Artifact: results/impl_verification/p2_recheck_2026-10-30.json

## CAUSAL_IR run 2026-10-30 (MODE=CAUSAL_IR, read-only, deterministic)

Pipeline: results/impl_verification/causal_ir/pipeline.py
Outputs: claim_ir.jsonl, code_ir.jsonl, graph.jsonl, causal_audit.json, conflict_report.json

Stage counts (from the 127 recorded units, 3,304 claim nodes):
- LOAD/VERIFY: 127 units, digests reproduce from live bytes; corpus drift unchanged
  (chapters_index.md recorded ea49cecc vs live 595a41b66c).
- PARSE: chapter sections; claim types 2,076 normative / 776 test-design / 452 open.
- EXTRACT+NORMALIZE: claim nodes with actor 571, precondition 1,195, effect 347, invariant token
  475; unfilled fields are null, not guessed. Text-level extraction only (heuristic), so actor and
  effect coverage is low by design — those nodes stay GAP.
- GRAPH: 2,139 edges — IMPLEMENTS 1,224 (keyword-level concept presence only, strength recorded as
  such), SUPPORTS 776, REQUIRES 98, REFERENCES 31, VIOLATES 5, DEPENDS_ON 5.
- SCAN/MAP: 49 code nodes from recorded evidence paths; 623 claims have code-surface evidence,
  1,982 have no implementation surface.
- CLASSIFY: proven→VERIFIED 192 (pin identity + design-only scans; no test execution evidence),
  adopted→AGREED 0 (no adoption record exists in the repo), gap→UNRESOLVED 3,106,
  violation→CONFLICT 6.
  Discrepancy, not silently fixed: the 2 claims recorded as AGREED in chapter_log.jsonl are
  reported here as GAP, because AGREED requires an adoption record and none exists.
- Gate: 96/127 records carry claim-level classification+evidence for every node; not retroactive to
  records written before this pass (20 records have claim lists without per-claim pairs).
- CAUSAL roots and dependency order: recovery authority → storage/WAL tail norm → event order norm
  → retention/tiering norm. Retention/tiering has no code surface, so its claims can only be GAP,
  never VIOLATION.
- CONFLICT_REPORT: 5 semantic-level conflicts (design norm vs code behaviour); no claim-to-claim
  conflict recorded. See conflict_report.json.

P3: BLOCKED. No adoption record exists for this pass. Nothing beyond pin identity is marked
VERIFIED; the segmentation convention, scope decision, and index re-record are decision-ready
but unadopted.
