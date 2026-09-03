#!/usr/bin/env bash

set -euo pipefail

[[ $# -eq 1 ]] || { echo "usage: $0 A|B|C|D"; exit 2; }
FOLD="$1"
[[ "$FOLD" =~ ^[ABCD]$ ]]

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
LOGS="${MAMBA_V16_D6_LOG_ROOT:-$ROOT/logs/mamba_v16_d6_contact_support}"
LOCKS="${MUG500PLUS_D6_DATA_LOCK_ROOT:-$HOME/datasets/MUG500plusD6Development100_v1/data_locks}"
CONFIGS="${MAMBA_V16_D6A_CALIBRATION_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v16_d6a_gradient_calibration_seed0_authorized_v1}"
AUTH="${MAMBA_V16_D6A_CALIBRATION_AUTH_DIR:-$LOGS/d6a_gradient_calibration_execution_authorization_v1}"
CALIBRATION="${MAMBA_V16_D6A_CALIBRATION_PROTOCOL_LOCK_DIR:-$LOGS/d6a_gradient_ratio_calibration_protocol_v1}"
FOURFOLD="${MUG500PLUS_D6_FOURFOLD_LOCK_DIR:-$LOCKS/mug500plus_d6_development_generation_fourfold_protocol_lock_v1}"
AUDIT="${MUG500PLUS_D6_GENERATION_AUDIT_DIR:-$LOGS/development_generation_audit_v1}"
OUTPUT_ROOT="${MAMBA_V16_D6A_CALIBRATION_FOLD_ROOT:-$LOGS/d6a_gradient_calibration_seed0_v1}"

cd "$ROOT"
python tools/run_mamba_v16_d6a_gradient_calibration_fold.py \
  --fold "$FOLD" \
  --config "$CONFIGS/MambaV16D6A_R1_gradient_calibration_fold${FOLD}_seed0.json" \
  --config_dir "$CONFIGS" --authorization_dir "$AUTH" \
  --calibration_lock_dir "$CALIBRATION" --fourfold_lock_dir "$FOURFOLD" \
  --generation_audit_dir "$AUDIT" --output_dir "$OUTPUT_ROOT/fold${FOLD}_seed0"
