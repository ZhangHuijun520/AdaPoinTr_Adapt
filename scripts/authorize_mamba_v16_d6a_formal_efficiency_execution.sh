#!/usr/bin/env bash

set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
LOGS="${MAMBA_V16_D6_LOG_ROOT:-$ROOT/logs/mamba_v16_d6_contact_support}"
CANDIDATE_LOCK="${MAMBA_V16_D6A_CANDIDATE_PROTOCOL_LOCK_DIR:-$LOGS/d6a_candidate_training_efficiency_protocol_v1}"
ZERO_STEP="${MAMBA_V16_D6A_EFFICIENCY_ZERO_STEP_DIR:-$LOGS/d6a_efficiency_implementation_zero_step_v1}"
CONFIGS="${MAMBA_V16_D6A_FORMAL_EFFICIENCY_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v16_d6a_formal_efficiency_authorized_v1}"
AUTH="${MAMBA_V16_D6A_FORMAL_EFFICIENCY_AUTH_DIR:-$LOGS/d6a_formal_efficiency_execution_authorization_v1}"

cd "$ROOT"
python tools/test_mamba_v16_d6a_formal_efficiency_execution_contract.py
for pass in 1 2; do
  python tools/authorize_mamba_v16_d6a_formal_efficiency_execution.py \
    --candidate_lock_dir "$CANDIDATE_LOCK" \
    --zero_step_dir "$ZERO_STEP" \
    --config_output_dir "$CONFIGS" \
    --authorization_output_dir "$AUTH"
done
python tools/verify_mamba_v16_d6a_formal_efficiency_authorization.py \
  --config_dir "$CONFIGS" --authorization_dir "$AUTH"
(
  cd "$AUTH"
  sha256sum -c files.sha256
  sha256sum -c formal_efficiency_execution_authorization_receipt.json.sha256
)
echo "[done] D6-A formal-efficiency execution authorization frozen"
echo "[locked] benchmark not started; training=false seed1=false D6B=false sealed=false"
echo "[next] run separate artificial CUDA authorization preflight"
