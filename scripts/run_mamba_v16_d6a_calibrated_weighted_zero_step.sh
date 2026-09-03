#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS="${MAMBA_V16_D6_LOG_ROOT:-$ROOT/logs/mamba_v16_d6_contact_support}"
FOURFOLD="${D6_FOURFOLD_LOCK_DIR:-$HOME/datasets/MUG500plusD6Development100_v1/data_locks/mug500plus_d6_development_generation_fourfold_protocol_lock_v1}"
AUDIT="${D6_GENERATION_AUDIT_DIR:-$LOGS/development_generation_audit_v1}"
CALIBRATION_LOCK="${D6_CALIBRATION_LOCK_DIR:-$LOGS/d6a_gradient_ratio_calibration_protocol_v1}"
CALIBRATION_FOLDS="${D6_CALIBRATION_FOLD_ROOT:-$LOGS/d6a_gradient_calibration_seed0_v1}"
CALIBRATION_COMPLETION="${D6_CALIBRATION_COMPLETION_DIR:-$LOGS/d6a_gradient_calibration_completion_v1}"
OUTPUT="${D6_WEIGHTED_ZERO_STEP_DIR:-$LOGS/d6a_calibrated_weighted_zero_step_v1}"

cd "$ROOT"
python tools/test_mamba_v16_d6a_calibrated_weighted_zero_step.py
python tools/preflight_mamba_v16_d6a_calibrated_weighted_zero_step.py \
  --fourfold_lock_dir "$FOURFOLD" \
  --generation_audit_dir "$AUDIT" \
  --calibration_lock_dir "$CALIBRATION_LOCK" \
  --calibration_fold_root "$CALIBRATION_FOLDS" \
  --calibration_completion_dir "$CALIBRATION_COMPLETION" \
  --output_dir "$OUTPUT"

(
  cd "$OUTPUT"
  sha256sum -c files.sha256
)

echo "[done] D6-A calibrated weighted real-train zero-step completed"
echo "[locked] optimizer=false training=false seed1=false D6B=false sealed=false"

