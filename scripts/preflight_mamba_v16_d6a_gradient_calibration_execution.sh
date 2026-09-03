#!/usr/bin/env bash

set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
LOGS="${MAMBA_V16_D6_LOG_ROOT:-$ROOT/logs/mamba_v16_d6_contact_support}"
CONFIGS="${MAMBA_V16_D6A_CALIBRATION_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v16_d6a_gradient_calibration_seed0_authorized_v1}"
AUTH="${MAMBA_V16_D6A_CALIBRATION_AUTH_DIR:-$LOGS/d6a_gradient_calibration_execution_authorization_v1}"
OUTPUT="${MAMBA_V16_D6A_CALIBRATION_PREFLIGHT_DIR:-$LOGS/d6a_gradient_calibration_execution_preflight_v1}"

cd "$ROOT"
python -m py_compile \
  tools/authorize_mamba_v16_d6a_gradient_calibration_execution.py \
  tools/verify_mamba_v16_d6a_gradient_calibration_execution_authorization.py \
  tools/preflight_mamba_v16_d6a_gradient_calibration_execution.py \
  tools/run_mamba_v16_d6a_gradient_calibration_fold.py \
  tools/freeze_mamba_v16_d6a_gradient_calibration.py
python tools/test_mamba_v16_d6a_gradient_calibration_execution_contract.py
python tools/verify_mamba_v16_d6a_gradient_calibration_execution_authorization.py \
  --config_dir "$CONFIGS" --authorization_dir "$AUTH"
python tools/preflight_mamba_v16_d6a_gradient_calibration_execution.py \
  --config_dir "$CONFIGS" --authorization_dir "$AUTH" --output_dir "$OUTPUT"
(
  cd "$OUTPUT"
  sha256sum -c files.sha256
)
echo "[done] D6-A calibration artificial CUDA preflight passed"
echo "[authorized-next] separate tmux launch of folds A-D only"
echo "[locked] calibration not started by this script; training=false sealed=false"
