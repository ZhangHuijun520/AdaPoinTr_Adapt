#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
CONFIG_DIR="cfgs/MUG500plus_models/generated_mamba_v13_d3_s1_seed0_authorized_v1"
AUTH_DIR="logs/mamba_v13_d3_mug500plus/s1_seed0_training_authorization_v1"
DEPLOYMENT="logs/mamba_v13_d3_mug500plus/data_deployment_v1/asset_deployment_receipt.json"
SMOKE="logs/mamba_v13_d3_mug500plus/s1_seed0_smoke_v1/s1_seed0_smoke_receipt.json"

cd "$ROOT"

python -m py_compile \
  tools/smoke_mamba_v13_d3_s1_seed0.py \
  tools/freeze_mamba_v13_d3_s1_seed0.py \
  tools/write_mamba_v13_d3_run_record.py \
  tools/evaluate_skullfix_implant.py \
  tools/benchmark_mamba_v12_efficiency.py

bash -n \
  scripts/preflight_mamba_v13_d3_s1_seed0.sh \
  scripts/run_mamba_v13_d3_s1_seed0_fold.sh \
  scripts/run_mamba_v13_d3_s1_seed0.sh \
  scripts/launch_mamba_v13_d3_s1_seed0_tmux.sh

python tools/test_mamba_v13_d3_s1_training_pipeline_contract.py
python tools/verify_mamba_v13_d3_s1_seed0_training_authorization.py \
  --config_dir "$CONFIG_DIR" \
  --authorization_dir "$AUTH_DIR"

python tools/smoke_mamba_v13_d3_s1_seed0.py \
  --config_dir "$CONFIG_DIR" \
  --authorization_dir "$AUTH_DIR" \
  --deployment_receipt "$DEPLOYMENT" \
  --output "$SMOKE"

python tools/smoke_mamba_v13_d3_s1_seed0.py \
  --config_dir "$CONFIG_DIR" \
  --authorization_dir "$AUTH_DIR" \
  --deployment_receipt "$DEPLOYMENT" \
  --output "$SMOKE" \
  --verify_only

echo "[done] D3 S1 seed-0 preflight passed"
echo "[authorized] launch S1 folds A-D in tmux"
echo "[locked] S2=false holdout=false selection=false"
