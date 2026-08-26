#!/usr/bin/env bash
set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
cd "$ROOT"

bash scripts/prepare_mamba_v13_d3_s1_calibration.sh

for fold in A B C D; do
  bash scripts/run_mamba_v13_d3_s1_calibration_fold.sh "$fold"
done

python tools/freeze_mamba_v13_d3_s1_calibration.py \
  --runs_root logs/mamba_v13_d3_mug500plus/s1_gradient_calibration_v1 \
  --authorization_dir \
    logs/mamba_v13_d3_mug500plus/s1_gradient_calibration_authorization_v1 \
  --output \
    logs/mamba_v13_d3_mug500plus/s1_gradient_calibration_completion_v1/s1_gradient_calibration_completion_receipt.json

echo "[done] S1 gradient-ratio calibration folds A-D frozen"
echo "[next] inspect completion receipt before separately materializing S1 configs"
echo "[locked] S1 training=false S2=false holdout=false selection=false"
