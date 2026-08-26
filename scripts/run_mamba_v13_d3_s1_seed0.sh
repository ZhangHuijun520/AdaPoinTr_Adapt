#!/usr/bin/env bash
set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
cd "$ROOT"

bash scripts/preflight_mamba_v13_d3_s1_seed0.sh

for fold in A B C D; do
  bash scripts/run_mamba_v13_d3_s1_seed0_fold.sh "$fold"
done

python tools/freeze_mamba_v13_d3_s1_seed0.py \
  --records_root logs/mamba_v13_d3_mug500plus/round_a \
  --authorization_receipt \
    logs/mamba_v13_d3_mug500plus/s1_seed0_training_authorization_v1/s1_seed0_training_authorization_receipt.json \
  --smoke_receipt \
    logs/mamba_v13_d3_mug500plus/s1_seed0_smoke_v1/s1_seed0_smoke_receipt.json \
  --s0_completion \
    logs/mamba_v13_d3_mug500plus/s0_seed0_completion_v1/s0_seed0_completion_receipt.json \
  --output \
    logs/mamba_v13_d3_mug500plus/s1_seed0_completion_v1/s1_seed0_completion_receipt.json

echo "[done] S1 seed-0 folds A-D trained and frozen"
echo "[next] preregistered S1-vs-S0 gate analysis only"
echo "[locked] selection=false S2=false holdout=false"
