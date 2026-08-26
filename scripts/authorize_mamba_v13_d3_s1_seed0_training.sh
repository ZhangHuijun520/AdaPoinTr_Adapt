#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
MATERIALIZATION_DIR="logs/mamba_v13_d3_mug500plus/s1_seed0_materialization_v1"
MATERIALIZED_CONFIG_DIR="cfgs/MUG500plus_models/generated_mamba_v13_d3_s1_seed0_materialized_v1"
DEPLOYMENT="logs/mamba_v13_d3_mug500plus/data_deployment_v1/asset_deployment_receipt.json"
S0_COMPLETION="logs/mamba_v13_d3_mug500plus/s0_seed0_completion_v1/s0_seed0_completion_receipt.json"
S2_NEGATIVE="logs/mamba_v13_d3_mug500plus/s2_head_feasibility_negative_freeze_v1"
CONFIG_DIR="cfgs/MUG500plus_models/generated_mamba_v13_d3_s1_seed0_authorized_v1"
AUTH_DIR="logs/mamba_v13_d3_mug500plus/s1_seed0_training_authorization_v1"

cd "$ROOT"

python -m py_compile \
  tools/authorize_mamba_v13_d3_s1_seed0_training.py \
  tools/verify_mamba_v13_d3_s1_seed0_training_authorization.py \
  tools/smoke_mamba_v13_d3_s1_seed0.py \
  tools/freeze_mamba_v13_d3_s1_seed0.py \
  tools/test_mamba_v13_d3_s1_training_pipeline_contract.py

bash -n \
  scripts/authorize_mamba_v13_d3_s1_seed0_training.sh \
  scripts/preflight_mamba_v13_d3_s1_seed0.sh \
  scripts/run_mamba_v13_d3_s1_seed0_fold.sh \
  scripts/run_mamba_v13_d3_s1_seed0.sh \
  scripts/launch_mamba_v13_d3_s1_seed0_tmux.sh

python tools/test_mamba_v13_d3_s1_training_pipeline_contract.py

for pass in 1 2; do
  python tools/authorize_mamba_v13_d3_s1_seed0_training.py \
    --materialization_dir "$MATERIALIZATION_DIR" \
    --materialized_config_dir "$MATERIALIZED_CONFIG_DIR" \
    --deployment_receipt "$DEPLOYMENT" \
    --s0_completion "$S0_COMPLETION" \
    --s2_negative_dir "$S2_NEGATIVE" \
    --config_output_dir "$CONFIG_DIR" \
    --authorization_output_dir "$AUTH_DIR"
done

python tools/verify_mamba_v13_d3_s1_seed0_training_authorization.py \
  --config_dir "$CONFIG_DIR" \
  --authorization_dir "$AUTH_DIR"

(
  cd "$AUTH_DIR"
  sha256sum -c files.sha256
  sha256sum -c s1_seed0_training_authorization_receipt.json.sha256
)

echo "[done] S1 seed-0 training authorization frozen"
echo "[authorized] S1 folds A-D only; training has not started"
echo "[locked] S2=false holdout=false official_test=false selection=false"
echo "[next] run the separate S1 preflight before tmux launch"
