#!/usr/bin/env bash

set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
CANDIDATE_LOCK="${MAMBA_V14_D4_CANDIDATE_PROTOCOL_LOCK_DIR:-$ROOT/logs/mamba_v14_d4_contact_support/d4_candidate_training_protocol_v1}"
FOURFOLD_LOCK="${MUG500PLUS_D4_M2_FOURFOLD_LOCK_DIR:-$HOME/datasets/MUG500plusD4Source100_v1/data_locks/mug500plus_d4_m2_fourfold_protocol_lock_v1}"
AUDIT="${MUG500PLUS_D4_GENERATION_AUDIT_DIR:-$ROOT/logs/mamba_v14_d4_contact_support/d4_m2_generation_audit_v1}"
ZERO_STEP="${MAMBA_V14_D4A_ZERO_STEP_DIR:-$ROOT/logs/mamba_v14_d4_contact_support/d4a_zero_step_preflight_v1}"
CONFIG_DIR="${MAMBA_V14_D4A_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v14_d4a_seed0_authorized_v1}"
AUTH_DIR="${MAMBA_V14_D4A_AUTH_DIR:-$ROOT/logs/mamba_v14_d4_contact_support/d4a_training_authorization_v1}"

cd "$ROOT"

python -m py_compile \
  tools/authorize_mamba_v14_d4a_training.py \
  tools/verify_mamba_v14_d4a_training_authorization.py \
  tools/run_mamba_v14_d4a_training_fold.py \
  tools/freeze_mamba_v14_d4a_training.py \
  tools/test_mamba_v14_d4a_training_pipeline_contract.py

bash -n \
  scripts/authorize_mamba_v14_d4a_training.sh \
  scripts/preflight_mamba_v14_d4a_training.sh \
  scripts/run_mamba_v14_d4a_training_fold.sh \
  scripts/run_mamba_v14_d4a_training.sh \
  scripts/launch_mamba_v14_d4a_training_tmux.sh

python tools/test_mamba_v14_d4a_training_pipeline_contract.py

for pass in 1 2; do
  python tools/authorize_mamba_v14_d4a_training.py \
    --candidate_lock_dir "$CANDIDATE_LOCK" \
    --fourfold_lock_dir "$FOURFOLD_LOCK" \
    --generation_audit_dir "$AUDIT" \
    --zero_step_dir "$ZERO_STEP" \
    --config_output_dir "$CONFIG_DIR" \
    --authorization_output_dir "$AUTH_DIR"
done

python tools/verify_mamba_v14_d4a_training_authorization.py \
  --config_dir "$CONFIG_DIR" \
  --authorization_dir "$AUTH_DIR"

(
  cd "$AUTH_DIR"
  sha256sum -c files.sha256
  sha256sum -c d4a_training_authorization_receipt.json.sha256
)

echo "[done] D4-A head-only training authorization frozen"
echo "[authorized] D4-A seed-0 folds A-D only; training was not started"
echo "[locked] T0=false T1=false T2=false selection=false protected=false"
echo "[next] run the separate D4-A training preflight before tmux launch"
