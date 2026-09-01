#!/usr/bin/env bash

set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
LOCKS="${MUG500PLUS_D5_DATA_LOCK_ROOT:-$HOME/datasets/MUG500plusD5Development100_v1/data_locks}"
LOGS="${MAMBA_V15_D5_LOG_ROOT:-$ROOT/logs/mamba_v15_d5_contact_support}"
CANDIDATE="${MAMBA_V15_D5_CANDIDATE_PROTOCOL_LOCK_DIR:-$LOGS/candidate_training_protocol_v1}"
FOURFOLD="${MUG500PLUS_D5_FOURFOLD_LOCK_DIR:-$LOCKS/mug500plus_d5_development400_fourfold_protocol_lock_v1}"
AUDIT="${MUG500PLUS_D5_GENERATION_AUDIT_DIR:-$LOGS/development_generation_audit_v1}"
ZERO="${MAMBA_V15_D5A_ZERO_STEP_DIR:-$LOGS/d5a_zero_step_preflight_v1}"
RESULT="${MAMBA_V15_D5A_ZERO_STEP_RESULT_DIR:-$LOGS/d5a_zero_step_result_freeze_v1}"
TRANSPORT="${MAMBA_V15_D5A_TRANSPORT_RECEIPT:-$LOGS/d5a_overlay_transport_normalization_v1/overlay_transport_normalization_receipt.json}"
PARENT_HOTFIX="${MAMBA_V15_D5A_PARENT_HOTFIX_RECEIPT:-$LOGS/d5a_d4_parent_lineage_hotfix1_v1/d4_parent_lineage_hotfix_receipt.json}"
CONFIG_DIR="${MAMBA_V15_D5A_SEED0_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v15_d5a_seed0_authorized_v1}"
AUTH_DIR="${MAMBA_V15_D5A_SEED0_AUTH_DIR:-$LOGS/d5a_seed0_training_authorization_v1}"

cd "$ROOT"

python -m py_compile \
  tools/authorize_mamba_v15_d5a_seed0_training.py \
  tools/verify_mamba_v15_d5a_seed0_training_authorization.py \
  tools/run_mamba_v15_d5a_seed0_training_fold.py \
  tools/freeze_mamba_v15_d5a_seed0_training.py \
  tools/test_mamba_v15_d5a_seed0_training_pipeline_contract.py

bash -n \
  scripts/authorize_mamba_v15_d5a_seed0_training.sh \
  scripts/preflight_mamba_v15_d5a_seed0_training.sh \
  scripts/run_mamba_v15_d5a_seed0_training_fold.sh \
  scripts/run_mamba_v15_d5a_seed0_training.sh \
  scripts/launch_mamba_v15_d5a_seed0_training_tmux.sh

python tools/test_mamba_v15_d5a_seed0_training_pipeline_contract.py

for pass in 1 2; do
  python tools/authorize_mamba_v15_d5a_seed0_training.py \
    --candidate_lock_dir "$CANDIDATE" \
    --fourfold_lock_dir "$FOURFOLD" \
    --generation_audit_dir "$AUDIT" \
    --zero_step_dir "$ZERO" \
    --zero_step_result_dir "$RESULT" \
    --transport_receipt "$TRANSPORT" \
    --parent_hotfix_receipt "$PARENT_HOTFIX" \
    --config_output_dir "$CONFIG_DIR" \
    --authorization_output_dir "$AUTH_DIR"
done

python tools/verify_mamba_v15_d5a_seed0_training_authorization.py \
  --config_dir "$CONFIG_DIR" \
  --authorization_dir "$AUTH_DIR"

(
  cd "$AUTH_DIR"
  sha256sum -c files.sha256
  sha256sum -c d5a_seed0_training_authorization_receipt.json.sha256
)

echo "[done] D5-A V0/V1 seed-0 training authorization frozen"
echo "[authorized] eight candidate-fold head trainings only; training not started"
echo "[locked] seed1=false confirmation=false D5B=false selection=false sealed=false"
echo "[next] run separate seed-0 training preflight before any tmux launch"
