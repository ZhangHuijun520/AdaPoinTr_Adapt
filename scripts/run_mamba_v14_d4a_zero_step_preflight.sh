#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

CANDIDATE_LOCK_DIR="${MAMBA_V14_D4_CANDIDATE_PROTOCOL_LOCK_DIR:-$REPO_ROOT/logs/mamba_v14_d4_contact_support/d4_candidate_training_protocol_v1}"
FOURFOLD_LOCK_DIR="${MUG500PLUS_D4_M2_FOURFOLD_LOCK_DIR:-$HOME/datasets/MUG500plusD4Source100_v1/data_locks/mug500plus_d4_m2_fourfold_protocol_lock_v1}"
GENERATION_AUDIT_DIR="${MUG500PLUS_D4_GENERATION_AUDIT_DIR:-$REPO_ROOT/logs/mamba_v14_d4_contact_support/d4_m2_generation_audit_v1}"
OUTPUT_DIR="${MAMBA_V14_D4A_ZERO_STEP_OUTPUT_DIR:-$REPO_ROOT/logs/mamba_v14_d4_contact_support/d4a_zero_step_preflight_v1}"

echo "===== D4-A deterministic implementation tests ====="
python -u tools/test_mamba_v14_d4a_implementation.py

echo "===== D4-A authorized CUDA zero-step preflight ====="
python -u tools/preflight_mamba_v14_d4a_zero_step.py \
  --candidate_lock_dir "$CANDIDATE_LOCK_DIR" \
  --fourfold_lock_dir "$FOURFOLD_LOCK_DIR" \
  --generation_audit_dir "$GENERATION_AUDIT_DIR" \
  --output_dir "$OUTPUT_DIR" \
  --test_script tools/test_mamba_v14_d4a_implementation.py \
  --launcher_script scripts/run_mamba_v14_d4a_zero_step_preflight.sh

echo "===== Verify immutable D4-A preflight output ====="
(
  cd "$OUTPUT_DIR"
  sha256sum -c files.sha256
)

echo "[done] D4-A implementation zero-step preflight completed"
echo "[locked] D4A training was not started"
echo "[locked] D4_training=false selection=false protected=false"
echo "[next] separate D4-A training execution authorization"
