#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
cd "$ROOT"

CONFIG_DIR="cfgs/MUG500plus_models/generated_mamba_v13_d3_s0_seed0_v1"
AUTH_RECEIPT="logs/mamba_v13_d3_mug500plus/s0_seed0_authorization_v1/s0_seed0_authorization_receipt.json"
DEPLOYMENT_RECEIPT="logs/mamba_v13_d3_mug500plus/data_deployment_v1/asset_deployment_receipt.json"
SMOKE_RECEIPT="logs/mamba_v13_d3_mug500plus/s0_seed0_smoke_v1/s0_seed0_smoke_receipt.json"

python -m py_compile \
  tools/smoke_mamba_v13_d3_s0_seed0.py \
  tools/write_mamba_v13_d3_run_record.py \
  tools/freeze_mamba_v13_d3_s0_seed0.py \
  tools/test_mamba_v13_d3_s0_pipeline_contract.py \
  tools/test_mamba_v13_d3_s0_receipts.py \
  tools/evaluate_skullfix_implant.py \
  tools/benchmark_mamba_v12_efficiency.py

bash -n \
  scripts/preflight_mamba_v13_d3_s0_seed0.sh \
  scripts/run_mamba_v13_d3_s0_seed0_fold.sh \
  scripts/run_mamba_v13_d3_s0_seed0.sh \
  scripts/launch_mamba_v13_d3_s0_seed0_tmux.sh

python tools/test_mamba_v13_d3_s0_pipeline_contract.py
python tools/test_mamba_v13_d3_s0_receipts.py
python tools/verify_mamba_v13_d3_s0_runtime_authorization.py \
  --config_dir "$CONFIG_DIR" \
  --receipt "$AUTH_RECEIPT"
python tools/smoke_mamba_v13_d3_s0_seed0.py \
  --config_dir "$CONFIG_DIR" \
  --authorization_receipt "$AUTH_RECEIPT" \
  --deployment_receipt "$DEPLOYMENT_RECEIPT" \
  --output "$SMOKE_RECEIPT"
python tools/smoke_mamba_v13_d3_s0_seed0.py \
  --config_dir "$CONFIG_DIR" \
  --authorization_receipt "$AUTH_RECEIPT" \
  --deployment_receipt "$DEPLOYMENT_RECEIPT" \
  --output "$SMOKE_RECEIPT" \
  --verify_only

echo "[done] D3 S0 seed-0 preflight passed"
echo "[authorized] launch S0 folds A-D in tmux"
echo "[locked] S1=false S2=false holdout=false selection_started=false"
