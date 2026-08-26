#!/usr/bin/env bash
set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
cd "$ROOT"

bash scripts/prepare_mamba_v13_d3_s2_feasibility.sh

for fold in A B C D; do
  bash scripts/run_mamba_v13_d3_s2_feasibility_fold.sh "$fold"
done

python tools/freeze_mamba_v13_d3_s2_feasibility.py \
  --runs_root logs/mamba_v13_d3_mug500plus/s2_head_feasibility_v1 \
  --lock_dir logs/mamba_v13_d3_mug500plus/s2_head_feasibility_protocol_v1 \
  --output \
    logs/mamba_v13_d3_mug500plus/s2_head_feasibility_completion_v1/s2_head_feasibility_completion_receipt.json

echo "[done] S2 head-only feasibility folds A-D frozen"
echo "[locked] no automatic full S2 training; inspect completion receipt next"
echo "[locked] holdout=false selection_started=false"
