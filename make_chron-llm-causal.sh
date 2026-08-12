#!/usr/bin/env bash
set -euo pipefail

# chron-llm-causal を ~/Chron-LLM 内に作成
TARGET_DIR="chron-llm-causal"
echo "=== Creating independent causal module at ${TARGET_DIR} ==="

mkdir -p "${TARGET_DIR}/data/delta1_raw"
mkdir -p "${TARGET_DIR}/data/delta1_normalized"
mkdir -p "${TARGET_DIR}/data/graphs"
mkdir -p "${TARGET_DIR}/src/causal_kernel/extractor"
mkdir -p "${TARGET_DIR}/src/causal_kernel/kernel"
mkdir -p "${TARGET_DIR}/spec_sheet"
mkdir -p "${TARGET_DIR}/tests"
mkdir -p "${TARGET_DIR}/examples"

copy_if_exists() {
    src="$1"
    dst="$2"
    if [ -f "$src" ]; then
        cp "$src" "$dst"
        echo "[COPIED] $src -> $dst"
    else
        echo "[SKIP] $src (Not found)"
    fi
}

echo "=== Migrating Delta1 Raw Data ==="
for f in causal_extract_*_raw.json; do
    copy_if_exists "$f" "${TARGET_DIR}/data/delta1_raw/"
done

echo "=== Migrating Delta1 Normalized Data ==="
for f in causal_extract_commit_kernel_v1.json causal_extract_core_v1.json causal_extract_core_v2.json causal_extract_kernel_v1.json causal_extract_kernel_world_v1.json; do
    copy_if_exists "$f" "${TARGET_DIR}/data/delta1_normalized/"
done

echo "=== Migrating Master Graph ==="
copy_if_exists "causal_master_graph.json" "${TARGET_DIR}/data/graphs/causal_master_graph_v2.json"

echo "=== Migrating Extractor & Specs ==="
copy_if_exists "tools/cae_extractor.py" "${TARGET_DIR}/src/causal_kernel/extractor/cae_extractor.py"
copy_if_exists "spec_sheet/cae-schema.yaml" "${TARGET_DIR}/spec_sheet/cae-schema.yaml"

touch "${TARGET_DIR}/src/causal_kernel/__init__.py"
touch "${TARGET_DIR}/src/causal_kernel/extractor/__init__.py"
touch "${TARGET_DIR}/src/causal_kernel/kernel/__init__.py"

echo "=== Setup Completed Successfully ==="

