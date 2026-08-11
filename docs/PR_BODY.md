Title: Finalize CAE schema v2.1.0-D and add CI baseline

Summary:
- Finalized CAE OpenAPI schema with R2.1-D canonicalization rules.
- Added txid and payload_len to CommitSeal contract to align with Phase A WAL header.
- Added CI workflow to run tests and static analysis.

What changed:
- spec_sheet/cae-schema.yaml
  - Canonicalization ordering and JCS (RFC 8785) guidance.
  - Prepare/Commit endpoints and payload definitions.
  - txid, payload_len, hdr_clock handling documented.
- .github/workflows/ci.yml
  - CI template: checkout, python setup, install, ruff, pytest, artifact upload.
- tests/test_cae_e2e.py updated to use tools.cae_extractor and Phase A mock adjustments.

Why:
- Locking the schema prevents interface drift between Phase A and Phase B.
- payload_len and txid are required to guarantee WAL header integrity and recover semantics per R2.1-D.
- CI ensures regressions are caught early.

Testing:
- Local: `python3 -m pytest -q tests/test_cae_e2e.py` passes.
- CI: workflow will run pytest and ruff on PR.

Notes for reviewers:
- Confirm Phase A implementation exposes prepare/commit/abort/recover with the expected fields:
  - prepare returns { txid, rec } where rec.hdr.payload_len and rec.crc_status are present.
  - commit returns { rec, hdr_clock } and rec.hdr.clock is incremented.
- If Phase A API differs, we will add a small adapter layer `phaseA/adapter_for_cae.py` to normalize responses.
- After merge, run integration tests against staging Phase A to validate real WAL header behavior.

Checklist:
- [ ] Schema reviewed and accepted
- [ ] CI green on PR
- [ ] Phase A API compatibility confirmed
- [ ] Tag release r2.1-d-2pc-e2e after merge

