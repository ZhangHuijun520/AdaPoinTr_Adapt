#!/usr/bin/env bash

set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
LOGS="${MAMBA_V16_D6_LOG_ROOT:-$ROOT/logs/mamba_v16_d6_contact_support}"
LOCKS="${MUG500PLUS_D6_DATA_LOCK_ROOT:-$HOME/datasets/MUG500plusD6Development100_v1/data_locks}"
CALIBRATION="${MAMBA_V16_D6A_CALIBRATION_PROTOCOL_LOCK_DIR:-$LOGS/d6a_gradient_ratio_calibration_protocol_v1}"
FOURFOLD="${MUG500PLUS_D6_FOURFOLD_LOCK_DIR:-$LOCKS/mug500plus_d6_development_generation_fourfold_protocol_lock_v1}"
AUDIT="${MUG500PLUS_D6_GENERATION_AUDIT_DIR:-$LOGS/development_generation_audit_v1}"
CONFIGS="${MAMBA_V16_D6A_CALIBRATION_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v16_d6a_gradient_calibration_seed0_authorized_v1}"
AUTH="${MAMBA_V16_D6A_CALIBRATION_AUTH_DIR:-$LOGS/d6a_gradient_calibration_execution_authorization_v1}"

cd "$ROOT"
python tools/test_mamba_v16_d6a_gradient_calibration_execution_contract.py
for pass in 1 2; do
  python tools/authorize_mamba_v16_d6a_gradient_calibration_execution.py \
    --calibration_lock_dir "$CALIBRATION" \
    --fourfold_lock_dir "$FOURFOLD" \
    --generation_audit_dir "$AUDIT" \
    --config_output_dir "$CONFIGS" \
    --authorization_output_dir "$AUTH"
done
python tools/verify_mamba_v16_d6a_gradient_calibration_execution_authorization.py \
  --config_dir "$CONFIGS" --authorization_dir "$AUTH"
(
  cd "$AUTH"
  sha256sum -c files.sha256
  sha256sum -c d6a_gradient_calibration_execution_authorization_receipt.json.sha256
)
echo "[done] D6-A R1 gradient-calibration execution authorization frozen"
echo "[locked] calibration not started; training=false seed1=false confirmation=false D6B=false sealed=false"
echo "[next] run separate artificial CUDA execution preflight"
