#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_LOCK_ROOT="${MUG500PLUS_D5_DATA_LOCK_ROOT:-$HOME/datasets/MUG500plusD5Development100_v1/data_locks}"
CANDIDATE_LOCK="${MAMBA_V15_D5_CANDIDATE_PROTOCOL_LOCK_DIR:-$ROOT/logs/mamba_v15_d5_contact_support/candidate_training_protocol_v1}"
FOURFOLD_LOCK="${MUG500PLUS_D5_DEVELOPMENT400_FOURFOLD_LOCK_DIR:-$DATA_LOCK_ROOT/mug500plus_d5_development400_fourfold_protocol_lock_v1}"
AUDIT="${MUG500PLUS_D5_GENERATION_AUDIT_DIR:-$ROOT/logs/mamba_v15_d5_contact_support/development_generation_audit_v1}"
OUTPUT="${MAMBA_V15_D5A_ZERO_STEP_OUTPUT_DIR:-$ROOT/logs/mamba_v15_d5_contact_support/d5a_zero_step_preflight_v1}"
TEST="$ROOT/tools/test_mamba_v15_d5a_implementation.py"
LAUNCHER="$ROOT/scripts/run_mamba_v15_d5a_zero_step_preflight.sh"

cd "$ROOT"
echo "===== D5-A deterministic implementation tests ====="
python -u "$TEST"

echo "===== D5-A authorized CUDA zero-step preflight ====="
python -u tools/preflight_mamba_v15_d5a_zero_step.py \
  --candidate_lock_dir "$CANDIDATE_LOCK" \
  --fourfold_lock_dir "$FOURFOLD_LOCK" \
  --generation_audit_dir "$AUDIT" \
  --output_dir "$OUTPUT" \
  --test_script "$TEST" \
  --launcher_script "$LAUNCHER"

(
  cd "$OUTPUT"
  sha256sum -c files.sha256
)

echo "[done] D5-A V0/V1 implementation zero-step preflight completed"
echo "[locked] D5-A training was not started"
echo "[locked] D5B=false selection=false sealed=false"
echo "[next] separate D5-A seed-0 training execution authorization"
