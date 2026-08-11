Title: Integration Test Procedure Phase A and Phase B

Purpose:
Validate real Phase A implementation (phaseA/durable_engine_v2_6_11.py or equivalent) against finalized CAE schema and 2PC contract.

Prerequisites:
- Repository merged to main with spec_sheet/cae-schema.yaml and CI.
- Deployable Phase A binary or service reachable from test runner.
- Environment variables or config pointing to Phase A endpoint or local module path.
- Python 3.10+ environment with pytest installed.

Steps:

1. Prepare environment
   - Create virtualenv and install project in editable mode:
     python -m venv .venv
     source .venv/bin/activate
     pip install -e .
     pip install pytest

2. Configure Phase A endpoint
   - If Phase A is an HTTP service, set env var:
     export PHASEA_URL=http://phasea-host:port
   - If Phase A is a local module, ensure PYTHONPATH includes its package or use adapter.

3. Provide adapter if needed
   - If Phase A API signatures differ from tests, create phaseA/adapter_for_cae.py that implements:
     - prepare(payload_dict) -> {"txid": <int>, "rec": <dict>, "status": "OK"|"CORRUPT"}
     - commit(txid) -> {"rec": <dict>, "status": "OK"|"CORRUPT", "hdr_clock": <int>}
     - abort(txid) -> {"rec": <dict>, "status": "OK"|"CORRUPT"}
     - recover() -> {"status": "OK"|"TRUNCATED", ...}
   - Point tests to adapter by setting TEST_PHASEA_ADAPTER=phaseA.adapter_for_cae

4. Run E2E tests against real Phase A
   - Execute:
     python -m pytest -q tests/test_cae_e2e.py -k "not mock"  # if you added real-vs-mock markers
   - Expected: all tests pass. Pay attention to:
     - payload_len equality
     - content_hash match
     - CRC status OK
     - hdr.clock increment and returned hdr_clock

5. Crash and recover scenarios
   - Simulate a crash after prepare but before commit:
     - Prepare a payload via Phase B to Phase A (prepare)
     - Kill Phase B process
     - Restart Phase A and call recover()
     - Verify PREPARED records are truncated if not committed
   - Simulate CRC failure injection if Phase A supports fault injection and verify Phase B aborts.

6. Duplicate node_id and causal cycle tests
   - Send a CAE node with an existing node_id and expect Phase A or Phase B to reject with 409 semantics.
   - Create a small graph that would introduce a causal cycle and verify detection and 409 response.

7. Logging and artifacts
   - Collect Phase A WAL entries, headers, and Phase B logs for each test.
   - Save artifacts to a central location for postmortem.

8. Post-test actions
   - If tests pass, tag the release:
     git tag -a r2.1-d-2pc-e2e -m "R2.1-D CAE schema and 2PC baseline"
     git push origin r2.1-d-2pc-e2e
   - If failures occur, open an issue with logs and assign to Phase A/Phase B owners.

Notes:
- Ensure canonical JSON generation in Phase B matches Phase A canonicalization exactly (JCS RFC 8785). Any mismatch will cause content_hash failures.
- For production, enable signature/seal verification: signatures must be computed over the same canonical bytes.
- Keep a small test corpus of representative CAE nodes to run nightly regression tests.

