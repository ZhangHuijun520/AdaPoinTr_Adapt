#!/usr/bin/env bash
set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
cd "$ROOT"

for fold in A B C D; do
  bash scripts/run_mamba_v13_d3_s0_seed0_fold.sh "$fold"
done

python tools/freeze_mamba_v13_d3_s0_seed0.py \
  --records_root logs/mamba_v13_d3_mug500plus/round_a \
  --authorization_receipt \
    logs/mamba_v13_d3_mug500plus/s0_seed0_authorization_v1/s0_seed0_authorization_receipt.json \
  --smoke_receipt \
    logs/mamba_v13_d3_mug500plus/s0_seed0_smoke_v1/s0_seed0_smoke_receipt.json \
  --output \
    logs/mamba_v13_d3_mug500plus/s0_seed0_completion_v1/s0_seed0_completion_receipt.json

echo "[done] S0 seed-0 folds A-D trained and frozen"
echo "[next] S2 head-only feasibility; S1/S2 full training remains locked"
echo "[locked] holdout=false selection_started=false"
