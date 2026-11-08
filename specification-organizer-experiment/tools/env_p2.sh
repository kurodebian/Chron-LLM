#!/usr/bin/env bash
# P2 extraction environment profile (2026-11-03 endpoint).
# Sourcing this exports the client env vars read by tools/llm_backend.py and
# tools/mdsheets_dm2_runner.py. The API key is resolved from ~/.hermes/.env
# (never embedded in this file, never printed).
set -a
[ -f "$HOME/.hermes/.env" ] && export MDSHEETS_DM2_API_KEY="$(grep '^HERMES_CUSTOM_10_0_0_1_8080_API_KEY=' "$HOME/.hermes/.env" | cut -d= -f2-)"
set +a
export MDSHEETS_DM2_BASE_URL="${MDSHEETS_DM2_BASE_URL:-http://10.0.0.1:8080/v1}"
export MDSHEETS_DM2_MODEL="${MDSHEETS_DM2_MODEL:-qwen3.8-flash-next-gyro-gyro-s}"
export MDSHEETS_DM2_TIMEOUT="${MDSHEETS_DM2_TIMEOUT:-1200}"
# Throughput calibration (2026-11-03): reasoning-enabled template consumed
# ~5.2k completion tokens per small unit (~270s at 19 tok/s). Transport-only
# knob; exact payload is recorded in provenance. temp/seed/grammar untouched.
export MDSHEETS_DM2_ENABLE_THINKING="${MDSHEETS_DM2_ENABLE_THINKING:-0}"
echo "P2 env: base=$MDSHEETS_DM2_BASE_URL model=$MDSHEETS_DM2_MODEL timeout=$MDSHEETS_DM2_TIMEOUT thinking=$MDSHEETS_DM2_ENABLE_THINKING api_key_present=$([ -n "$MDSHEETS_DM2_API_KEY" ] && echo yes || echo no)"
