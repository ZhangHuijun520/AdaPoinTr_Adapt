#!/usr/bin/env bash
set -euo pipefail

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

for seed in 1 2; do
  echo "============================================================"
  echo "[R1] starting frozen O0=xyz seed=${seed}"
  echo "============================================================"
  bash scripts/run_skullbreak_mamba_v11_o0_seed_replication.sh "$seed"
done

echo "[done] frozen O0 seed-1/seed-2 sequence completed"
echo "[next] aggregate seed-0/1/2 without reopening model selection"
